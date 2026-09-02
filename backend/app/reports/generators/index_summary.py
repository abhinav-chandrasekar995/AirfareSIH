"""Weekly index summary report generator.

SCOPE NOTE: report rendering (PDF layout, CSV export formatting) is stubbed at
data-assembly level; the frontend Reports page correctly shows generation as disabled
rather than pretending it works (see IMPLEMENTATION_LOG.md). The data this would render
is already real and available via /api/v1/index and /api/v1/dashboard - a report is a
formatting layer over data that already exists, not a new computation.
"""
from __future__ import annotations

from datetime import date
from typing import Any


async def build_weekly_index_summary(session: Any, as_of: date) -> dict:
    """Assemble the data payload for a weekly index summary report.

    Returns the same shape the dashboard and index endpoints already serve, reused
    rather than recomputed - report data must never diverge from what the dashboard
    shows for the same period.
    """
    from app.core.constants import IndexLevel
    from app.services import dashboard_service, index_service

    dashboard = await dashboard_service.get_dashboard(session)
    national = await index_service.get_summary(session, IndexLevel.NATIONAL)
    regional = await index_service.get_regional_summaries(session)

    return {
        "report_type": "WEEKLY_INDEX_SUMMARY",
        "as_of": as_of.isoformat(),
        "national_index": national,
        "regional_indices": regional,
        "top_increases": dashboard["top_increases"],
        "top_decreases": dashboard["top_decreases"],
        "insights": dashboard["insights"],
    }
