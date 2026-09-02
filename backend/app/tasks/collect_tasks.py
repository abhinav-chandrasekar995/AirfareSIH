"""Stage 1 tasks. Idempotent and keyed so any task can safely be retried."""
from __future__ import annotations

import asyncio

from app.collection.orchestrator import ScrapingOrchestrator, build_work_matrix
from app.config import settings
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("tasks.collect")


@celery_app.task(name="app.tasks.collect_tasks.collect_all", bind=True, max_retries=2)
def collect_all(self) -> dict:
    if not settings.collection_enabled:
        logger.info("collection disabled; skipping scheduled run")
        return {"status": "SKIPPED", "reason": "collection_enabled=False"}
    return asyncio.run(_collect_all())


async def _collect_all() -> dict:
    from app.db.repositories import analytics_repository as repo
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        routes = [r.route_code for r in await repo.all_routes(session, basket_only=True)]
        sources = [s.source_code for s in await repo.sources(session) if s.status == "ACTIVE"]

    plan = build_work_matrix(routes, sources)
    orchestrator = ScrapingOrchestrator(respect_robots=settings.respect_robots_txt)

    succeeded = failed = 0
    for source_code, query in plan.queries:
        result = await orchestrator.collect_with_fallback(source_code, query, set(sources))
        if result[0].status.value in ("SUCCESS", "PARTIAL"):
            succeeded += 1
        else:
            failed += 1
    return {"status": "COMPLETE", "queries": len(plan), "succeeded": succeeded, "failed": failed}


@celery_app.task(name="app.tasks.collect_tasks.collect_source")
def collect_source(source_code: str, run_id: int | None = None) -> dict:
    if not settings.collection_enabled:
        return {"status": "SKIPPED", "source": source_code, "reason": "collection_enabled=False"}
    return {"status": "QUEUED", "source": source_code, "run_id": run_id}
