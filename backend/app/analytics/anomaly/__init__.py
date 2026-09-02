from app.analytics.anomaly.attribution import AttributionContext, FactorContribution, attribute
from app.analytics.anomaly.baseline import (
    Baseline,
    build_baseline,
    classify_severity,
    deviation_pct,
)
from app.analytics.anomaly.detectors import (
    detect_iqr,
    detect_isolation_forest,
    detect_mad,
    detect_zscore,
)
from app.analytics.anomaly.scraper_anomaly import check_batch

__all__ = [
    "Baseline",
    "build_baseline",
    "deviation_pct",
    "classify_severity",
    "AttributionContext",
    "FactorContribution",
    "attribute",
    "check_batch",
    "detect_zscore",
    "detect_iqr",
    "detect_mad",
    "detect_isolation_forest",
    "run_detectors",
]


def run_detectors(value: float, sample: list[float]) -> list[str]:
    """Run all four detectors and return the names of those that fired.

    Recording which detectors agreed is what lets an analyst judge how much confidence
    an anomaly deserves - one detector firing is a hint, four is a finding.
    """
    fired = []
    if detect_zscore(value, sample):
        fired.append("zscore")
    if detect_iqr(value, sample):
        fired.append("iqr")
    if detect_mad(value, sample):
        fired.append("mad")
    if detect_isolation_forest(value, sample):
        fired.append("isolation_forest")
    return fired
