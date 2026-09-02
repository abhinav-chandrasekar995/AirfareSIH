"""Repository helpers. All SQL lives in this package - no other layer emits queries."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def count_of(session: AsyncSession, stmt: Select) -> int:
    subquery = stmt.with_only_columns(func.count()).order_by(None)
    return int((await session.execute(subquery)).scalar() or 0)


async def paginate(session: AsyncSession, stmt: Select, page: int, page_size: int) -> tuple[list[Any], int]:
    """Always paginate. An unbounded analytical query is a production incident waiting
    to happen (build prompt Sec.18)."""
    total = await count_of(session, select(*stmt.selected_columns) if stmt.selected_columns else stmt)
    rows = (await session.execute(stmt.limit(page_size).offset((page - 1) * page_size))).all()
    return list(rows), total
