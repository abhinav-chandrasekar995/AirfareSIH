"""Stage 2.6 - Fare decomposition reconciliation."""
from __future__ import annotations

COMPONENTS = ("base_fare", "taxes", "udf", "airport_charges", "convenience_fee")
TOLERANCE = 0.02


def reconcile(obs: dict) -> tuple[bool, float]:
    """Check that the components sum to the total. Returns (reconciles, drift_fraction)."""
    total = float(obs.get("total_fare") or 0)
    if total <= 0:
        return False, 1.0
    components = sum(float(obs.get(k) or 0) for k in COMPONENTS)
    drift = abs(components - total) / total
    return drift <= TOLERANCE, round(drift, 4)


def composition(obs: dict) -> dict[str, float]:
    """Component breakdown with percentage shares, as rendered on the route page."""
    total = float(obs.get("total_fare") or 0)
    out: dict[str, float] = {}
    for key in COMPONENTS:
        value = float(obs.get(key) or 0)
        out[key] = round(value, 2)
        out[f"{key}_pct"] = round(value / total * 100.0, 2) if total > 0 else 0.0
    out["total_fare"] = round(total, 2)
    return out
