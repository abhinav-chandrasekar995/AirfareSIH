"""Add core_index_values table (base-fare-only "Core APIx", RBI module).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-04

Additive only - mirrors index_values exactly (same columns, same RLS treatment: public
SELECT, ANALYST/ADMIN write) so the existing, DGCA-backtested Headline (total_fare)
series in index_values is never touched by this. See RBI_APIX_MODULE_LOG.md for why this
is a separate table rather than a column/flag on IndexValue.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

TABLE = "core_index_values"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("index_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("index_value", sa.Numeric(8, 3), nullable=False),
        sa.Column("base_period", sa.Date(), nullable=False),
        sa.Column("weight", sa.Numeric(6, 4)),
        sa.Column("estimator", sa.String(20), nullable=False),
        sa.Column("mean_fare", sa.Numeric(10, 2)),
        sa.Column("median_fare", sa.Numeric(10, 2)),
        sa.Column("trimmed_mean_fare", sa.Numeric(10, 2)),
        sa.Column("weighted_median_fare", sa.Numeric(10, 2)),
        sa.Column("n_observations", sa.Integer(), nullable=False),
        sa.Column("weight_set_version", sa.String(30)),
        sa.Column("methodology_version", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(f"ix_{TABLE}_date", TABLE, ["date"])

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {TABLE}_public_read ON {TABLE} FOR SELECT USING (true)")
    op.execute(
        f"CREATE POLICY {TABLE}_elevated_write ON {TABLE} FOR ALL "
        f"USING (current_setting('app.role', true) IN ('ANALYST','ADMIN')) "
        f"WITH CHECK (current_setting('app.role', true) IN ('ANALYST','ADMIN'))"
    )


def downgrade() -> None:
    op.drop_table(TABLE)
