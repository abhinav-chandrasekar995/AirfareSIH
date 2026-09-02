"""Fare observation tables.

Two tables, deliberately: `fare_observations_raw` is immutable and append-only, and
`fare_observations` holds the cleaned derived record. Cleaning never overwrites raw
(build prompt Sec.4), which is what lets the entire index be recomputed under a new
methodology without re-scraping a single page.

Both are TimescaleDB hypertables in production; the hypertable conversion lives in the
Alembic migration rather than here, because it is DDL SQLAlchemy does not model.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.reference import Airline, Route, Source


class FareObservationRaw(Base):
    """Tier 0. Untouched adapter output. Never updated, never deleted."""

    __tablename__ = "fare_observations_raw"

    raw_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.source_id"), nullable=False)
    scrape_run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    route_code: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(20), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_raw_source_time", "source_id", "observed_at"),
        Index("idx_raw_route_time", "route_code", "observed_at"),
    )


class FareObservation(Base):
    """Tier 1. Cleaned, decomposed, quality-scored. The analytical core."""

    __tablename__ = "fare_observations"

    observation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_id: Mapped[int | None] = mapped_column(BigInteger)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.source_id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"), nullable=False)
    airline_id: Mapped[int] = mapped_column(ForeignKey("airlines.airline_id"), nullable=False)

    flight_number: Mapped[str] = mapped_column(String(10), nullable=False)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lead_days: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_bucket: Mapped[str] = mapped_column(String(4), nullable=False)
    fare_class: Mapped[str] = mapped_column(String(20), default="ECONOMY", nullable=False)

    # Fare decomposition. The consumer-facing total is what the index measures; the
    # components are what make the movement explainable.
    base_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    taxes: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    udf: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    airport_charges: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    convenience_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    seats_available: Mapped[int | None] = mapped_column(Integer)
    availability_status: Mapped[str] = mapped_column(String(20), default="UNKNOWN", nullable=False)

    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    imputed_fields: Mapped[list[str] | None] = mapped_column(ARRAY(String(40)))
    quality_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, index=True)
    quality_band: Mapped[str] = mapped_column(String(10), nullable=False)

    pipeline_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship(lazy="selectin")
    route: Mapped[Route] = relationship(lazy="selectin")
    airline: Mapped[Airline] = relationship(lazy="selectin")

    __table_args__ = (
        # The natural key. A source quoting the same itinerary at the same instant is
        # one observation, however many times the collector saw it.
        UniqueConstraint(
            "source_id",
            "route_id",
            "flight_number",
            "departure_datetime",
            "fare_class",
            "observed_at",
            name="uq_observation_natural_key",
        ),
        CheckConstraint("total_fare > 0", name="chk_total_fare_positive"),
        CheckConstraint("lead_days >= 0", name="chk_lead_days"),
        CheckConstraint("quality_score BETWEEN 0 AND 100", name="chk_quality_range"),
        CheckConstraint("lead_bucket IN ('T1','T7','T15','T30','T45')", name="chk_lead_bucket"),
        CheckConstraint("quality_band IN ('HIGH','MEDIUM','LOW')", name="chk_quality_band"),
        Index("idx_obs_route_time", "route_id", "observed_at"),
        Index("idx_obs_route_lead_time", "route_id", "lead_bucket", "observed_at"),
        Index("idx_obs_airline_time", "airline_id", "observed_at"),
    )
