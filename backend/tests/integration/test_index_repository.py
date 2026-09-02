"""Regression test for the index_repository "latest" ordering bug (see
IMPLEMENTATION_LOG.md, incident: dashboard headline disagreed with the trend chart's
own last point).

Root cause: `_base_query()` baked in `.order_by(IndexValue.date)` (ascending), and
`latest()`/`value_on_or_before()` each appended `.order_by(desc(IndexValue.date))` on
top, expecting it to override. SQLAlchemy's `Select.order_by()` appends rather than
replaces, so the effective query became `ORDER BY date ASC, date DESC` - the ascending
clause still won as the primary sort key, so `.limit(1)` silently returned the OLDEST
row every time "latest" was requested.
"""
from __future__ import annotations

import pytest

from app.core.constants import IndexLevel
from app.db.repositories import index_repository as index_repo
from app.db.session import SessionLocal
from tests.conftest import requires_db


@requires_db
async def test_latest_returns_the_most_recent_date_not_the_oldest():
    async with SessionLocal() as session:
        series = await index_repo.series(session, IndexLevel.NATIONAL)
        assert len(series) > 1, "need real seeded history for this regression test to mean anything"

        latest = await index_repo.latest(session, IndexLevel.NATIONAL)
        assert latest is not None

        true_latest_date = max(row.date for row in series)
        assert latest.date == true_latest_date, (
            f"latest() returned {latest.date}, but the series' true most recent date is "
            f"{true_latest_date} - this is the ordering regression, not a data issue"
        )


@requires_db
async def test_series_is_chronologically_ascending():
    """The trend chart plots series() left-to-right; it must be ascending by date."""
    async with SessionLocal() as session:
        series = await index_repo.series(session, IndexLevel.NATIONAL)
        dates = [row.date for row in series]
        assert dates == sorted(dates)


@requires_db
async def test_dashboard_headline_matches_the_series_last_point():
    """The bug this test guards against: the dashboard KPI and the trend chart's own
    last plotted point must be the same number - they read the same underlying data."""
    async with SessionLocal() as session:
        series = await index_repo.series(session, IndexLevel.NATIONAL)
        latest = await index_repo.latest(session, IndexLevel.NATIONAL)
        last_series_point = max(series, key=lambda r: r.date)

        assert float(latest.index_value) == pytest.approx(float(last_series_point.index_value))
