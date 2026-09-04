"""Report generation endpoints.

Each report is assembled from the SAME service-layer functions the interactive pages
call - a report can never show a number the rest of the app doesn't already show
somewhere, because it is not a separate code path with its own queries. CSV/JSON
export rather than PDF: no new heavy dependency (a PDF/layout engine) for a hackathon
build, and CSV is more useful to the report's actual audience (a statistician or
analyst who wants to load it into their own tool) than a fixed-layout document.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.services import analytics_service, apix_service, dashboard_service, index_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _csv_response(filename: str, header: list[str], rows: list[list]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/index-summary", summary="Weekly Index Summary report")
async def report_index_summary(
    fmt: str = Query(default="csv", pattern="^(csv|json)$"),
    session: AsyncSession = Depends(get_session),
):
    dash = await dashboard_service.get_dashboard(session)
    regional = await index_service.get_regional_summaries(session)
    generated_at = datetime.now(UTC).isoformat()

    if fmt == "json":
        payload = {
            "report_type": "WEEKLY_INDEX_SUMMARY",
            "generated_at": generated_at,
            "national_index": dash["index_value"],
            "national_change_mom_pct": dash["index_change_mom_pct"],
            "regional_indices": regional,
            "top_increases": dash["top_increases"],
            "top_decreases": dash["top_decreases"],
            "insights": [i["text"] for i in dash["insights"]],
        }
        return StreamingResponse(
            io.StringIO(json.dumps(payload, default=str, indent=2)),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=weekly_index_summary.json"},
        )

    rows: list[list] = [
        ["Metric", "Value"],
        ["Generated at", generated_at],
        ["National Airfare Index", dash["index_value"]],
        ["Month-over-month change (%)", dash["index_change_mom_pct"]],
        [],
        ["Regional Index", ""],
    ]
    for r in regional:
        rows.append([r["scope"], r["current_value"]])
    rows.append([])
    rows.append(["Top Increases (7d)", "Route", "Change %"])
    for m in dash["top_increases"]:
        rows.append(["", m["route_code"], m["change_pct"]])
    rows.append(["Top Decreases (7d)", "Route", "Change %"])
    for m in dash["top_decreases"]:
        rows.append(["", m["route_code"], m["change_pct"]])
    rows.append([])
    rows.append(["Key Insights", ""])
    for insight in dash["insights"]:
        rows.append(["", insight["text"]])

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=weekly_index_summary.csv"},
    )


@router.get("/route-brief", summary="Route Intelligence Brief report")
async def report_route_brief(
    route_code: str = Query(..., description="e.g. DEL-BOM"),
    session: AsyncSession = Depends(get_session),
):
    detail = await analytics_service.get_route_detail(session, route_code)

    header = ["Field", "Value"]
    rows = [
        ["Route", detail["route_code"]],
        ["Origin", f"{detail['origin_city']} ({detail['origin']})"],
        ["Destination", f"{detail['destination_city']} ({detail['destination']})"],
        ["Region", detail["region"]],
        ["Route Index", detail["route_index"]],
        ["Current Fare", detail["current_fare"]],
        ["7-Day Average", detail["avg_7d"]],
        ["30-Day Average", detail["avg_30d"]],
        ["Yearly Average", detail["avg_yearly"]],
        ["Month-over-month change (%)", detail["change_mom_pct"]],
        ["Observations", detail["n_observations"]],
    ]
    if detail.get("composition"):
        rows.append(["", ""])
        rows.append(["Fare Composition", ""])
        for key in ("base_fare", "taxes", "udf", "airport_charges", "convenience_fee", "total_fare"):
            rows.append([key, detail["composition"].get(key)])
    if detail.get("volatility"):
        rows.append(["", ""])
        rows.append(["Volatility Score", detail["volatility"]["volatility_score"]])
        rows.append(["Coefficient of Variation", detail["volatility"]["coefficient_of_variation"]])

    return _csv_response(f"route_brief_{detail['route_code']}.csv", header, rows)


@router.get("/backtest-validation", summary="Backtesting Validation Report")
async def report_backtest_validation(session: AsyncSession = Depends(get_session)):
    backtest = await analytics_service.get_backtest(session)
    if backtest is None:
        raise NotFoundError("no back-test run is available to report on")

    header = ["Metric", "Value"]
    rows = [
        ["Run at", backtest["run_at"]],
        ["Route scope", backtest["route_scope"]],
        ["Estimator", backtest["estimator"]],
        ["Train window", f"{backtest['train_start']} to {backtest['train_end']}"],
        ["Test window (out-of-sample)", f"{backtest['test_start']} to {backtest['test_end']}"],
        ["Test days", backtest["n_test_days"]],
        ["MAE", backtest["mae"]],
        ["RMSE", backtest["rmse"]],
        ["MAPE (%)", backtest["mape"]],
        ["Correlation", backtest["correlation"]],
        ["Directional accuracy (%)", backtest["directional_accuracy"]],
        ["DGCA benchmark vintage", backtest["dgca_vintage"]],
        ["Alignment method", backtest["alignment_method"]],
        [],
        ["Month", "Our Index", "DGCA Benchmark"],
    ]
    for point in backtest["series"]:
        rows.append([point["month"], point["ours"], point["dgca"]])

    return _csv_response("backtest_validation_report.csv", header, rows)


@router.get("/cpi-scenario", summary="CPI Augmentation Scenario Note")
async def report_cpi_scenario(
    weight: float = Query(default=2.5, ge=0, le=100),
    session: AsyncSession = Depends(get_session),
):
    sim = await analytics_service.get_cpi_simulation(session, weight)

    header = ["Field", "Value"]
    rows = [
        ["DISCLAIMER", "This module is a simulation for analytical demonstration. It does not represent an official CPI revision or official NSO methodology."],
        [],
        ["Period", sim["period_month"]],
        ["Base CPI", sim["base_cpi"]],
        ["CPI vintage", sim["cpi_vintage"]],
        ["CPI base year", sim["cpi_base_year"]],
        ["Airfare Index", sim["airfare_index"]],
        ["Airfare weight (%)", sim["airfare_weight_pct"]],
        ["Simulated Augmented Index", sim["augmented_index"]],
        ["Delta vs base CPI", sim["delta"]],
        ["Formula", sim["formula"]],
        [],
        ["Sensitivity: Weight (%)", "Augmented Index", "Delta"],
    ]
    for s in sim["sensitivity"]:
        rows.append([s["weight_pct"], s["augmented_index"], s["delta"]])

    return _csv_response("cpi_augmentation_scenario_note.csv", header, rows)


@router.get("/rbi-policy-brief", summary="RBI Policy Brief - Core APIx inflation snapshot")
async def report_rbi_policy_brief(session: AsyncSession = Depends(get_session)):
    """One-page brief for the RBI inflation-alert scenario: current alert status, the
    Core vs Headline split, and the price breakdown behind it. Assembled from the exact
    same apix_service functions the /apix/* endpoints and dashboard call - see
    RBI_APIX_MODULE_LOG.md."""
    alert = await apix_service.get_alert_status(session)
    breakdown = await apix_service.get_price_breakdown(session)
    comparison = await apix_service.get_comparison(session)

    core_latest = comparison["core"][-1] if comparison["core"] else None
    headline_latest = comparison["headline"][-1] if comparison["headline"] else None

    header = ["Field", "Value"]
    rows = [
        ["Report", "RBI Policy Brief"],
        ["Generated at", datetime.now(UTC).isoformat()],
        ["As of", alert.get("as_of")],
        [],
        ["Alert Status", alert.get("status")],
        ["Triggered", alert.get("triggered")],
        ["National Core APIx WoW (%)", alert.get("national_wow_pct")],
        ["National tolerance band (%)", alert.get("national_threshold_pct")],
        ["Spiking route", alert.get("spiking_route")],
        ["Spiking route WoW (%)", alert.get("spiking_route_wow_pct")],
        ["Route tolerance band (%)", alert.get("route_threshold_pct")],
        ["Message", alert.get("message")],
        [],
        ["Core APIx (base fare, national)", core_latest["index_value"] if core_latest else None],
        ["Headline APIx (total fare, national)", headline_latest["index_value"] if headline_latest else None],
    ]
    if breakdown:
        rows.append([])
        rows.append(["Price Breakdown", f"as of {breakdown['as_of']}"])
        rows.append(["Avg base fare", breakdown["avg_base_fare"]])
        rows.append(["Avg taxes & fees", breakdown["avg_taxes_and_fees"]])
        rows.append(["Avg total fare", breakdown["avg_total_fare"]])
        rows.append(["Observations", breakdown["n_observations"]])

    return _csv_response("rbi_policy_brief.csv", header, rows)
