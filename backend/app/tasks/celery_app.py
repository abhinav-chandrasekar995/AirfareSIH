"""Celery application with separate queues per stage of the pipeline."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "airfare_intelligence",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.collect_tasks",
        "app.tasks.pipeline_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.ml_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    # A message-send from the API process must fail fast, not retry with backoff:
    # the send happens inline in an HTTP request handler (see admin.py), and a
    # multi-attempt reconnect storm there blocks that request - and, since the call is
    # synchronous, the whole ASGI event loop - for the entire retry window if the
    # broker is briefly unreachable. Workers reconnecting to their own broker is a
    # different, legitimate use case and is unaffected by this (it only governs the
    # client-side send path used by apply_async/delay).
    broker_connection_retry=False,
    broker_connection_timeout=2.0,
    # kombu's Redis transport uses redis-py under the hood, which has its own
    # socket-level connect/read timeouts independent of broker_connection_timeout
    # above; without these the observed failure time was ~9s instead of ~2s.
    broker_transport_options={"socket_connect_timeout": 2.0, "socket_timeout": 2.0},
    # No caller in this codebase ever polls a Celery AsyncResult - task outcomes are
    # read back from Postgres (scrape_runs, data_quality_flags), which is the actual
    # architecture (doc/02-ARCHITECTURE.md). The result backend has its OWN, separate
    # connection-retry policy that broker_connection_retry above does not touch, and it
    # was found (empirically, against a real unreachable broker) to retry for ~20s on
    # the very first apply_async call in a process. Ignoring results removes that
    # second retry path entirely rather than trying to tune it to match the first.
    task_ignore_result=True,
    # Separate queues so a slow ML retrain cannot starve collection, and so each stage
    # can be scaled independently (build prompt Sec.1).
    task_routes={
        "app.tasks.collect_tasks.*": {"queue": "collect"},
        "app.tasks.pipeline_tasks.*": {"queue": "pipeline"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.ml_tasks.*": {"queue": "ml"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
)
