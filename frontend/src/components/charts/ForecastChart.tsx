"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { istDate, inr } from "@/lib/format";
import type { ForecastPoint } from "@/types/api";

// A point forecast must never render alone (build prompt Sec.17). `points` here always
// carry lower/upper bounds from the backend schema (ForecastPoint requires them), so
// there is no code path in this component that can plot a bare prediction.
export function ForecastChart({ points }: { points: ForecastPoint[] }) {
  const dates = points.map((p) => istDate(p.forecast_date));
  const colors = seriesColors();

  // Band drawn as a filled area between lower and upper bounds.
  const lower = points.map((p) => p.lower_bound);
  const bandHeight = points.map((p) => p.upper_bound - p.lower_bound);
  const prediction = points.map((p) => p.prediction);

  const option = {
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value", scale: true, axisLabel: { formatter: (v: number) => `₹${(v / 1000).toFixed(1)}k` } },
    series: [
      { name: "Lower bound", type: "line", data: lower, symbol: "none", lineStyle: { opacity: 0 }, stack: "band" },
      {
        name: "Confidence interval", type: "line", data: bandHeight, symbol: "none",
        lineStyle: { opacity: 0 }, areaStyle: { color: colors[0], opacity: 0.15 }, stack: "band",
      },
      {
        name: "Forecast", type: "line", data: prediction, symbol: "circle", symbolSize: 5,
        lineStyle: { width: 2, type: "dashed", color: colors[0] }, itemStyle: { color: colors[0] },
      },
    ],
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) => {
        const p = points[params[0]?.dataIndex ?? 0];
        if (!p) return "";
        return `${istDate(p.forecast_date)}<br/>Prediction: ${inr(p.prediction)}<br/>Range: ${inr(p.lower_bound)} – ${inr(p.upper_bound)}`;
      },
    },
  };

  return (
    <ChartFrame
      option={option}
      height={280}
      ariaLabel="Forecast with prediction interval"
      summary={`Forecast over ${points.length} days, prediction interval width from ${inr(Math.min(...bandHeight))} to ${inr(Math.max(...bandHeight))}.`}
      tableData={{
        columns: ["Date", "Prediction", "Lower", "Upper"],
        rows: points.map((p) => [istDate(p.forecast_date), inr(p.prediction), inr(p.lower_bound), inr(p.upper_bound)]),
      }}
    />
  );
}
