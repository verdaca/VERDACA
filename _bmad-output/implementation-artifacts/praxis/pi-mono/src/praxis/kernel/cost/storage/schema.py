"""SQLAlchemy 2.0 declarative schema for Pi-Mono.

Columns use NUMERIC for cost math — never REAL/DOUBLE. Timestamps are TEXT
on SQLite (ISO 8601) and TIMESTAMPTZ on Postgres.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


NUM = Numeric(20, 10)


class PricingRow(Base):
    __tablename__ = "pricing"

    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    cache_retention_key: Mapped[str] = mapped_column(
        String(16), primary_key=True, default="none"
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    input_rate: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    output_rate: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cache_read_rate: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cache_write_rate: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    snapshot_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CostRecordRow(Base):
    __tablename__ = "cost_records"

    record_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(26), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)

    input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cache_read_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)

    cost_input: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cost_output: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cost_cache_read: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cost_cache_write: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    cost_total: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)

    pricing_effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    pricing_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_request_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latency_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

    stop_reason: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    cache_retention: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    lifecycle_state: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    amended_by_record_id: Mapped[str | None] = mapped_column(String(26), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("request_id", name="ux_cost_records_request_id"),
        Index("ix_cost_records_started_at", "started_at"),
        Index("ix_cost_records_session", "session_id", "started_at"),
        Index("ix_cost_records_workflow", "workflow_id", "started_at"),
        Index("ix_cost_records_agent", "agent", "started_at"),
        Index("ix_cost_records_provider_model", "provider", "model_id", "started_at"),
    )


class EventRow(Base):
    __tablename__ = "events_outbox"

    event_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    record_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_events_outbox_undelivered", "emitted_at"),
    )


class ReconciliationReportRow(Base):
    __tablename__ = "reconciliation_reports"

    invoice_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_internal: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    total_invoice: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    total_delta: Mapped[Decimal] = mapped_column(NUM, nullable=False)
    total_drift_pct: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    invoice_source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    invoice_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
