"""Reclassify scrape_runs and data_quality_flags as publicly readable.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-02

The Collection Engine page (/collection) shows per-source OTA/airline-direct scraper
status (found/valid/failed/success) and open data-quality flags to anyone viewing the
app, with no API key - it is an operational status page, not privileged data, and the
frontend never gates it behind login. The 0001 migration put both tables in
ANALYST_TABLES (FOR ALL, ANALYST/ADMIN only), and neither the /data-quality endpoint nor
any dependency it uses ever calls apply_principal() to set an RLS role - so every read of
these two tables from that endpoint was silently and correctly filtered to zero rows by
RLS's fail-closed default (build prompt Sec.6). That is not a data-loss bug; the rows
were always there (confirmed via a role-scoped psql session). The fix is to make read
access match what the UI already promises: public SELECT, elevated (ANALYST/ADMIN)
INSERT/UPDATE/DELETE - the exact PUBLIC_READ_TABLES pattern 0001 already uses for every
other analytical product. fare_observations_raw stays ANALYST-only: it is raw per-scrape
fare data, not a status summary, and nothing in the UI displays it without a key.
"""
from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

RECLASSIFIED_TABLES = ["scrape_runs", "data_quality_flags"]


def upgrade() -> None:
    for table in RECLASSIFIED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_analyst ON {table}")
        op.execute(f"CREATE POLICY {table}_public_read ON {table} FOR SELECT USING (true)")
        op.execute(
            f"CREATE POLICY {table}_elevated_write ON {table} FOR ALL "
            f"USING (current_setting('app.role', true) IN ('ANALYST','ADMIN')) "
            f"WITH CHECK (current_setting('app.role', true) IN ('ANALYST','ADMIN'))"
        )


def downgrade() -> None:
    for table in RECLASSIFIED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_public_read ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_elevated_write ON {table}")
        op.execute(
            f"CREATE POLICY {table}_analyst ON {table} FOR ALL "
            f"USING (current_setting('app.role', true) IN ('ANALYST','ADMIN')) "
            f"WITH CHECK (current_setting('app.role', true) IN ('ANALYST','ADMIN'))"
        )
