"""Add AGGREGATOR to sources.source_type CHECK constraint.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-04

Third-party APIs like SerpApi's Google Flights engine are neither an airline-direct
site nor an OTA - they are an authorized data vendor, a genuinely distinct category from
the other two, which is why this is a schema change rather than reusing OTA loosely.
See IMPLEMENTATION_LOG.md for the ethics/feasibility investigation that led here: direct
scraping of the airline/OTA sources in this basket was found to be blocked by their own
robots.txt (EaseMyTrip, SpiceJet both confirmed), which is what made an authorized
aggregator API worth adding as its own first-class source type rather than a workaround.
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sources DROP CONSTRAINT IF EXISTS chk_source_type")
    op.execute(
        "ALTER TABLE sources ADD CONSTRAINT chk_source_type "
        "CHECK (source_type IN ('AIRLINE_DIRECT','OTA','AGGREGATOR'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE sources DROP CONSTRAINT IF EXISTS chk_source_type")
    op.execute(
        "ALTER TABLE sources ADD CONSTRAINT chk_source_type "
        "CHECK (source_type IN ('AIRLINE_DIRECT','OTA'))"
    )
