"""Operational and security tables: collection audit, data-quality flags, API keys,
and the audit log. Every one of these carries RLS policies (build prompt Sec.6)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScrapeRun(Base):
    """One collection attempt against one source. The audit trail for Stage 1."""

    __tablename__ = "scrape_runs"

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.source_id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_valid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    adapter_version: Mapped[str] = mapped_column(String(20), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(20), default="SCHEDULER", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING','SUCCESS','PARTIAL','FAILED','SKIPPED_ROBOTS','SKIPPED_CHALLENGE')",
            name="chk_scrape_status",
        ),
        CheckConstraint("triggered_by IN ('SCHEDULER','MANUAL')", name="chk_triggered_by"),
    )


class DataQualityFlag(Base):
    """Where scraper anomalies land, kept strictly separate from market anomalies."""

    __tablename__ = "data_quality_flags"

    flag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_ref: Mapped[str] = mapped_column(String(50), nullable=False)
    flag_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("scope_type IN ('SOURCE','ROUTE','PIPELINE')", name="chk_dq_scope"),
        CheckConstraint("severity IN ('INFO','WARNING','CRITICAL')", name="chk_dq_severity"),
        Index("idx_dq_flags_scope", "scope_type", "scope_ref"),
    )


class ApiKey(Base):
    """API credentials. Only the Argon2 hash is stored; the raw key is shown once at
    creation and is unrecoverable afterwards."""

    __tablename__ = "api_keys"

    key_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key_prefix: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(150), nullable=False)
    owner_org: Mapped[str | None] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(String(20), default="PUBLIC", nullable=False)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    daily_quota: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("role IN ('PUBLIC','ANALYST','ADMIN')", name="chk_api_key_role"),
    )


class AuditLog(Base):
    """Append-only record of every sensitive action (build prompt Sec.6)."""

    __tablename__ = "audit_log"

    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    actor_key_id: Mapped[int | None] = mapped_column(BigInteger)
    actor_label: Mapped[str | None] = mapped_column(String(150))
    action: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(30))
    target_ref: Mapped[str | None] = mapped_column(String(50))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
