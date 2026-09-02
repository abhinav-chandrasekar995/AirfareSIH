"""Route weight handling.

Weights derive from DGCA passenger-traffic data and are versioned (weight_set_version).
When a route drops out of a period for lack of data, the remaining weights are
renormalised so the index stays on a comparable scale instead of silently drifting down.
"""
from __future__ import annotations


def renormalise(weights: dict[str, float], observed_routes: set[str]) -> dict[str, float]:
    """Restrict weights to observed routes and rescale them to sum to 1."""
    present = {r: w for r, w in weights.items() if r in observed_routes and w > 0}
    total = sum(present.values())
    if total <= 0:
        return {}
    return {r: w / total for r, w in present.items()}


def excluded_routes(weights: dict[str, float], observed_routes: set[str]) -> list[str]:
    return sorted(r for r in weights if r not in observed_routes)
