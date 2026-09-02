"""CPI augmentation simulation.

This is a scenario tool, not a CPI revision. The disclaimer is part of the result object
rather than something a caller attaches afterwards, so no code path can produce a
simulation without it (build prompt Sec.15).
"""
from __future__ import annotations

from dataclasses import dataclass

DISCLAIMER = (
    "This module is a simulation for analytical demonstration. It does not represent "
    "an official CPI revision or official NSO methodology."
)

DEFAULT_WEIGHT_PCT = 2.5
FORMULA = "Augmented = Base CPI x (1 - w) + Airfare Index x w"


@dataclass(frozen=True)
class SimulationResult:
    base_cpi: float
    airfare_index: float
    weight_pct: float
    augmented_index: float
    delta: float
    formula: str
    disclaimer: str


def simulate(
    base_cpi: float,
    airfare_index: float,
    weight_pct: float = DEFAULT_WEIGHT_PCT,
) -> SimulationResult:
    if not 0.0 <= weight_pct <= 100.0:
        raise ValueError("airfare weight must be between 0 and 100 percent")
    w = weight_pct / 100.0
    augmented = base_cpi * (1 - w) + airfare_index * w
    return SimulationResult(
        base_cpi=round(base_cpi, 2),
        airfare_index=round(airfare_index, 3),
        weight_pct=round(weight_pct, 3),
        augmented_index=round(augmented, 2),
        delta=round(augmented - base_cpi, 2),
        formula=FORMULA,
        disclaimer=DISCLAIMER,
    )


def sensitivity(
    base_cpi: float,
    airfare_index: float,
    weights: list[float] | None = None,
) -> list[SimulationResult]:
    """Sweep the weight so a reader can see how much the choice actually matters."""
    return [simulate(base_cpi, airfare_index, w) for w in (weights or [1.0, 2.5, 5.0, 7.5, 10.0])]
