"""Contributing-factor attribution for a detected anomaly.

This is the most scientifically contestable thing the platform does, so two rules are
enforced structurally rather than by convention:
  1. Shares always sum to 100%, with whatever the model cannot explain named explicitly
     as an "unexplained residual" instead of being quietly distributed.
  2. Every result carries the model-based-attribution note, surfaced in UI and API.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactorContribution:
    factor: str
    label: str
    pct: float


@dataclass(frozen=True)
class AttributionContext:
    """Observable conditions around the anomalous observation."""
    is_weekend: bool = False
    seats_available: int | None = None
    days_to_event: int | None = None
    lead_days: int | None = None
    is_seasonal_peak: bool = False


# Raw factor strengths in [0,1]. Normalised into percentage shares of the deviation
# actually observed; they are explanatory weights, not measured causal effects.
def _raw_strengths(ctx: AttributionContext) -> dict[str, tuple[str, float]]:
    strengths: dict[str, tuple[str, float]] = {}

    if ctx.is_weekend:
        strengths["weekend_demand"] = ("Weekend demand", 0.55)

    if ctx.seats_available is not None:
        if ctx.seats_available <= 5:
            strengths["low_seat_availability"] = ("Low seat availability", 0.85)
        elif ctx.seats_available <= 15:
            strengths["low_seat_availability"] = ("Low seat availability", 0.45)

    if ctx.days_to_event is not None and ctx.days_to_event <= 14:
        # Closer to the event means stronger attribution, tapering linearly.
        strengths["festival_proximity"] = ("Festival proximity", 0.75 * (1 - ctx.days_to_event / 14))

    if ctx.lead_days is not None:
        if ctx.lead_days <= 3:
            strengths["short_booking_window"] = ("Short booking window", 0.80)
        elif ctx.lead_days <= 10:
            strengths["short_booking_window"] = ("Short booking window", 0.40)

    if ctx.is_seasonal_peak:
        strengths["seasonal_demand"] = ("Seasonal demand", 0.50)

    return {k: v for k, v in strengths.items() if v[1] > 0}


def attribute(ctx: AttributionContext, min_residual_pct: float = 4.0) -> list[FactorContribution]:
    """Normalise factor strengths into percentage shares that sum to exactly 100."""
    strengths = _raw_strengths(ctx)

    if not strengths:
        return [FactorContribution("unexplained", "Unexplained residual", 100.0)]

    total = sum(s for _, s in strengths.values())
    explained_budget = 100.0 - min_residual_pct

    contributions = [
        FactorContribution(key, label, round(strength / total * explained_budget, 1))
        for key, (label, strength) in sorted(strengths.items(), key=lambda kv: -kv[1][1])
    ]
    # The residual absorbs rounding drift so the breakdown always totals 100.
    residual = round(100.0 - sum(c.pct for c in contributions), 1)
    contributions.append(FactorContribution("unexplained", "Unexplained residual", residual))
    return contributions
