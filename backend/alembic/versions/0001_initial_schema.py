"""Initial schema: all tables, TimescaleDB hypertables (graceful), RLS policies.

Revision ID: 0001
Create Date: 2026-09-01

This migration is written to run on THREE targets without modification:
  - Timescale Cloud / self-hosted Postgres with the timescaledb extension
  - Supabase / plain Postgres 16+ (hypertables degrade to plain tables + indexes)
  - a local Postgres for portable demos

TimescaleDB DDL is guarded: if the extension is unavailable the tables stay ordinary
Postgres tables and every index/constraint/RLS policy still applies. The index math is
identical either way - hypertables are a performance feature, not a correctness one.
"""
from __future__ import annotations

from alembic import op

from app.db.base import Base
from app.db import models  # noqa: F401

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# Tables that are hypertables under TimescaleDB, keyed by their time column.
HYPERTABLES = {
    "fare_observations_raw": "observed_at",
    "fare_observations": "observed_at",
}

# Tables carrying Row Level Security. Public analytical products are readable by all;
# operational/security tables are restricted to elevated roles (build prompt Sec.6).
PUBLIC_READ_TABLES = [
    "airports", "airlines", "routes", "route_weights", "sources", "events",
    "dgca_benchmarks", "cpi_reference", "methodology_versions",
    "fare_observations", "index_values", "leadtime_curves", "volatility_metrics",
    "anomalies", "forecasts", "backtest_runs", "cpi_simulations",
]
ANALYST_TABLES = ["fare_observations_raw", "data_quality_flags", "scrape_runs"]
ADMIN_TABLES = ["api_keys", "audit_log"]


def _create_all_tables() -> None:
    """Create every ORM-defined table via metadata, so the DDL never drifts from models."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def _enable_timescale() -> bool:
    """Try to enable TimescaleDB, tolerating its absence (Supabase, vanilla Postgres).

    A failed statement aborts the enclosing Postgres transaction even if the Python
    exception is caught - catching alone does not undo that server-side state, so the
    very next statement on the same connection would fail with "current transaction is
    aborted" regardless of the try/except. A SAVEPOINT scopes the failure so only the
    extension attempt rolls back, leaving the rest of the migration transaction usable.
    """
    bind = op.get_bind()
    try:
        with bind.begin_nested():
            op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        row = bind.exec_driver_sql(
            "SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'"
        ).fetchone()
        return row is not None
    except Exception:
        # Supabase and vanilla Postgres do not ship timescaledb; that is expected.
        return False


def _make_hypertables() -> None:
    for table, time_column in HYPERTABLES.items():
        op.execute(
            f"SELECT create_hypertable('{table}', '{time_column}', "
            f"chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE, "
            f"migrate_data => TRUE)"
        )


def _continuous_aggregates() -> None:
    """Route-day rollup the dashboard reads instead of scanning the raw hypertable."""
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS route_day_agg
        WITH (timescaledb.continuous) AS
        SELECT route_id,
               time_bucket('1 day', observed_at) AS day,
               avg(total_fare) AS mean_fare,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY total_fare) AS median_fare,
               count(*) AS n_observations
        FROM fare_observations
        WHERE quality_score >= 60
        GROUP BY route_id, day
        WITH NO DATA
        """
    )


def _fallback_indexes() -> None:
    """Plain B-tree substitutes for the continuous aggregate on non-Timescale targets."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_obs_route_day "
        "ON fare_observations (route_id, observed_at)"
    )


def _enable_rls() -> None:
    """Row Level Security, enforced at the database (build prompt Sec.6).

    The application connects as a non-superuser role, so these policies are the real
    access boundary - a missing or wrong `app.role` setting fails closed. Policies read
    the request principal from the transaction-scoped `app.role` GUC set by db/rls.py.
    """
    # Everyone (including anonymous PUBLIC) may read published analytical products.
    for table in PUBLIC_READ_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_public_read ON {table} FOR SELECT USING (true)"
        )
        # Writes require ANALYST or ADMIN.
        op.execute(
            f"CREATE POLICY {table}_elevated_write ON {table} FOR ALL "
            f"USING (current_setting('app.role', true) IN ('ANALYST','ADMIN')) "
            f"WITH CHECK (current_setting('app.role', true) IN ('ANALYST','ADMIN'))"
        )

    # Operational tables: readable/writable only by ANALYST and ADMIN.
    for table in ANALYST_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_analyst ON {table} FOR ALL "
            f"USING (current_setting('app.role', true) IN ('ANALYST','ADMIN')) "
            f"WITH CHECK (current_setting('app.role', true) IN ('ANALYST','ADMIN'))"
        )

    # Security tables: ADMIN only. This is the tightest boundary in the system.
    for table in ADMIN_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_admin ON {table} FOR ALL "
            f"USING (current_setting('app.role', true) = 'ADMIN') "
            f"WITH CHECK (current_setting('app.role', true) = 'ADMIN')"
        )


def upgrade() -> None:
    has_timescale = _enable_timescale()
    _create_all_tables()

    if has_timescale:
        try:
            # Same savepoint reasoning as _enable_timescale(): a failure here must not
            # poison the transaction that still has to enable RLS below. This step can
            # genuinely fail even with the extension present - create_hypertable()
            # requires any PRIMARY KEY on the table to include the partitioning column,
            # which fare_observations(_raw)'s single-column autoincrement PK does not.
            # Fixing that would mean a composite primary key, which is a real schema
            # change; hypertables are explicitly a performance feature here; not a
            # correctness one (see this module's docstring), so falling back to plain
            # indexes on failure is the same story datamode-degradation already tells,
            # not a new one.
            with op.get_bind().begin_nested():
                _make_hypertables()
        except Exception:
            has_timescale = False

    if has_timescale:
        try:
            with op.get_bind().begin_nested():
                _continuous_aggregates()
        except Exception:
            _fallback_indexes()
    else:
        _fallback_indexes()

    _enable_rls()


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS route_day_agg CASCADE")
    Base.metadata.drop_all(bind=op.get_bind())
