"""Scheduled orchestration.

Collection runs off-peak and each downstream stage follows once the previous one has
drained. A failed stage does not block the next: the dashboard degrades to the previous
vintage with a freshness warning rather than showing nothing.
"""
from __future__ import annotations

from celery.schedules import crontab

from app.tasks.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "collect-all-sources": {
        "task": "app.tasks.collect_tasks.collect_all",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "collect"},
    },
    "run-cleaning-pipeline": {
        "task": "app.tasks.pipeline_tasks.process_pending",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "pipeline"},
    },
    "compute-indices": {
        "task": "app.tasks.analytics_tasks.compute_all_indices",
        "schedule": crontab(hour=5, minute=0),
        "options": {"queue": "analytics"},
    },
    "detect-anomalies": {
        "task": "app.tasks.ml_tasks.detect_anomalies",
        "schedule": crontab(hour=5, minute=30),
        "options": {"queue": "ml"},
    },
    "generate-forecasts": {
        "task": "app.tasks.ml_tasks.generate_forecasts",
        "schedule": crontab(hour=5, minute=45),
        "options": {"queue": "ml"},
    },
    "refresh-backtest": {
        "task": "app.tasks.analytics_tasks.run_backtest",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "analytics"},
    },
    "nightly-maintenance": {
        "task": "app.tasks.maintenance_tasks.nightly",
        "schedule": crontab(hour=6, minute=15),
        "options": {"queue": "maintenance"},
    },
}
