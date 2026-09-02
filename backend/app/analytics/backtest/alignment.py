"""Alignment between our daily index and the DGCA monthly benchmark.

The two series have different granularity, so the aggregation method has to be stated
rather than assumed. We aggregate our daily values to a monthly mean and compare
like with like; the method is recorded on every back-test run.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

ALIGNMENT_METHOD = (
    "daily index aggregated to calendar-month mean, compared to DGCA monthly average fare"
)


def to_monthly(series: list[tuple[date, float]]) -> dict[date, float]:
    buckets: dict[date, list[float]] = defaultdict(list)
    for day, value in series:
        buckets[day.replace(day=1)].append(value)
    return {month: round(sum(v) / len(v), 3) for month, v in sorted(buckets.items())}


def align_series(
    ours: list[tuple[date, float]],
    benchmark: list[tuple[date, float]],
) -> tuple[list[date], list[float], list[float]]:
    """Return the months present in both series, with the paired values."""
    ours_monthly = to_monthly(ours)
    bench_monthly = {d.replace(day=1): v for d, v in benchmark}
    months = sorted(set(ours_monthly) & set(bench_monthly))
    return months, [ours_monthly[m] for m in months], [bench_monthly[m] for m in months]
