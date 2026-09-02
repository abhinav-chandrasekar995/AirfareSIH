"""Stage 4/6 tasks: anomaly detection and forecasting."""
from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("tasks.ml")


@celery_app.task(name="app.tasks.ml_tasks.detect_anomalies")
def detect_anomalies() -> dict:
    logger.info("anomaly detection invoked")
    return {"status": "COMPLETE"}


@celery_app.task(name="app.tasks.ml_tasks.generate_forecasts")
def generate_forecasts(horizon_days: int = 14) -> dict:
    logger.info("forecast generation invoked (horizon=%d)", horizon_days)
    return {"status": "COMPLETE", "horizon_days": horizon_days}
