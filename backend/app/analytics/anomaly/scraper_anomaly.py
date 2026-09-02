"""Scraper-anomaly detection.

A broken collector and a genuine price surge look identical in a naive pipeline. This
check runs BEFORE market-anomaly classification: if a batch shows the signature of a
collection failure, it is routed to the data-quality path instead of being published as
a market surge (build prompt Sec.11).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ScraperAnomalyResult:
    is_scraper_anomaly: bool
    flag_type: str | None
    description: str | None


def check_batch(fares: list[float], source_code: str, min_batch: int = 20) -> ScraperAnomalyResult:
    """Screen a single source's batch for collection-failure signatures."""
    clean = ScraperAnomalyResult(False, None, None)
    if len(fares) < min_batch:
        return clean

    arr = np.asarray(fares, dtype=float)

    # Identical-value flood: a source returning one fare for a whole batch is broken,
    # not a market in which every seat costs the same. The threshold is deliberately
    # generous (5%, not 2%): for a realistic batch of ~40 observations, even a single
    # unique value only gives a ratio of 1/40 = 0.025, so a tighter threshold could
    # never fire in practice and this check would be dead code at normal batch sizes.
    unique_ratio = len(np.unique(arr)) / arr.size
    if unique_ratio < 0.05:
        return ScraperAnomalyResult(
            True,
            "DUPLICATE_FLOOD",
            f"Source '{source_code}' returned {arr.size} observations with only "
            f"{len(np.unique(arr))} distinct fare value(s). Routed to data quality, "
            f"not classified as a market surge.",
        )

    # Collapsed variance: near-zero dispersion across a large batch is implausible.
    mean_fare = float(np.mean(arr))
    if mean_fare > 0 and float(np.std(arr)) / mean_fare < 0.005:
        return ScraperAnomalyResult(
            True,
            "VARIANCE_COLLAPSE",
            f"Source '{source_code}' fare dispersion collapsed below 0.5% of the mean "
            f"across {arr.size} observations, indicating a collection fault.",
        )

    # Implausible values: fares outside any credible domestic range.
    if float(np.min(arr)) < 500 or float(np.max(arr)) > 500_000:
        return ScraperAnomalyResult(
            True,
            "IMPLAUSIBLE_RANGE",
            f"Source '{source_code}' produced fares outside the plausible domestic "
            f"range (min {np.min(arr):.0f}, max {np.max(arr):.0f}).",
        )

    return clean
