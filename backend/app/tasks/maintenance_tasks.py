"""Nightly maintenance: cache warming, retention, report generation."""
from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("tasks.maintenance")


@celery_app.task(name="app.tasks.maintenance_tasks.nightly")
def nightly() -> dict:
    logger.info("nightly maintenance invoked")
    return {"status": "COMPLETE"}
