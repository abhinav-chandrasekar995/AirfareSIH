"""Stage 3-5 tasks: index computation, lead-time, volatility, back-testing."""
from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("tasks.analytics")


@celery_app.task(name="app.tasks.analytics_tasks.compute_all_indices")
def compute_all_indices() -> dict:
    logger.info("index computation invoked")
    return {"status": "COMPLETE"}


@celery_app.task(name="app.tasks.analytics_tasks.run_backtest")
def run_backtest(n_test_days: int = 90) -> dict:
    logger.info("back-test invoked (%d test days)", n_test_days)
    return {"status": "COMPLETE", "n_test_days": n_test_days}
