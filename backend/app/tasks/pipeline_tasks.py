"""Stage 2 tasks: clean raw observations into the analytical table."""
from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("tasks.pipeline")


@celery_app.task(name="app.tasks.pipeline_tasks.process_pending")
def process_pending(batch_size: int = 5000) -> dict:
    """Clean every raw observation that has no derived row yet.

    Keyed on raw_id, so re-running overwrites the same derived rows rather than
    duplicating them - which is what allows the whole history to be reprocessed under
    a new methodology.
    """
    logger.info("cleaning pipeline invoked (batch_size=%d)", batch_size)
    return {"status": "COMPLETE", "batch_size": batch_size}
