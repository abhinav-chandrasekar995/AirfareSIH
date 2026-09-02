"""Aggregates every v1 router."""
from fastapi import APIRouter

from app.api.v1.routers import admin, analytics, fares, index, reports

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(index.router)
api_router.include_router(fares.router)
api_router.include_router(analytics.dashboard_router)
api_router.include_router(analytics.routes_router)
api_router.include_router(analytics.airlines_router)
api_router.include_router(analytics.leadtime_router)
api_router.include_router(analytics.anomalies_router)
api_router.include_router(analytics.volatility_router)
api_router.include_router(analytics.forecast_router)
api_router.include_router(analytics.backtest_router)
api_router.include_router(analytics.cpi_router)
api_router.include_router(analytics.quality_router)
api_router.include_router(analytics.events_router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
