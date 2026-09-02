"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import AirfareError
from app.core.logging import configure_logging, get_logger
from app.middleware.cpi_disclaimer import CpiDisclaimerMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware

logger = get_logger("app")

DESCRIPTION = """
High-frequency measurement of India's domestic airfare market.

The platform collects airfare observations, normalises and quality-scores them,
constructs a transparent route-weighted **India Airfare Price Index**, explains abnormal
movements, validates against DGCA benchmarks, forecasts near-term pressure, and
simulates how a high-frequency airfare signal could augment CPI analysis.

Every response carries `meta.data_mode` (`LIVE` / `CACHED` / `REPLAY`) and a
`methodology_version`, so any published number is traceable to the configuration that
produced it.

**The CPI simulation module is a simulation for analytical demonstration. It does not
represent an official CPI revision or official NSO methodology.**
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.debug)
    logger.info("starting %s (%s)", settings.app_name, settings.environment)
    yield
    from app.db.session import dispose_engine

    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Order matters: context outermost so every log line and error carries a request id,
    # disclaimer innermost so it sees the final serialised body.
    app.add_middleware(CpiDisclaimerMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-Request-ID"],
    )

    app.include_router(api_router)

    @app.exception_handler(AirfareError)
    async def handle_domain_error(request: Request, exc: AirfareError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health", tags=["ops"], summary="Liveness")
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/health/ready", tags=["ops"], summary="Readiness")
    async def ready() -> dict:
        """Readiness reports the age of the newest published index, because a platform
        serving a three-week-old index is 'up' but not actually working."""
        from sqlalchemy import text

        from app.db.session import SessionLocal

        checks = {"database": False, "index_available": False}
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
                checks["database"] = True
                from app.db.repositories import analytics_repository as repo

                latest = await repo.latest_index_date(session)
                checks["index_available"] = latest is not None
                checks["latest_index_date"] = str(latest) if latest else None
        except Exception as exc:
            checks["error"] = str(exc)

        healthy = checks["database"]
        return {"status": "ready" if healthy else "degraded", "checks": checks}

    return app


app = create_app()
