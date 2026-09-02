"""Async engine and session factory.

The engine is created lazily rather than at import time. Building it eagerly means a
missing driver or an unreachable database breaks `import app.main` itself, which would
take down the OpenAPI schema, the unit tests and the offline demo along with it.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a session that always closes."""
    async with get_session_factory()() as session:
        try:
            yield session
        finally:
            await session.close()


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


class _SessionLocalProxy:
    """Callable proxy so `SessionLocal()` keeps working without eager engine creation."""

    def __call__(self) -> AsyncSession:
        return get_session_factory()()


SessionLocal = _SessionLocalProxy()
