"""SQLAlchemy 2.0 declarative schema for Runtime's durable jobs infrastructure.

Architecture §4.2.2 (jobs_queue) + §4.2.3 (outbox_drain_retries).

These tables live in the SAME Postgres instance as Pi-Mono's events_outbox
(see §4.2.1 composition requirement — shared-DB topology is a correctness
requirement for Path A atomicity, not an optimization).

RuntimeBase is a separate DeclarativeBase from Pi-Mono's Base so metadata
management stays independent.  Both are created via the same engine at
Orchestrator boot.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class RuntimeBase(DeclarativeBase):
    """Separate base for Runtime-owned tables (jobs + drain retries).

    Must NOT inherit from Pi-Mono's Base — they are independent metadatas
    that share a database, not a Python class hierarchy.
    """


class JobType(str, Enum):
    RETENTION_SHRED = "retention_shred"
    RETENTION_CASCADE = "retention_cascade"
    QUARANTINE_PROMOTE = "quarantine_promote"
    BACKUP_REWRITE = "backup_rewrite"


class JobState(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    POISONED = "poisoned"


class FailureReason(str, Enum):
    TRANSIENT_BACKEND = "transient_backend"
    BACKEND_TIMEOUT = "backend_timeout"
    INVARIANT_VIOLATION = "invariant_violation"
    TENANT_DRIFT = "tenant_drift"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


class JobsQueue(RuntimeBase):
    """Durable retention jobs substrate (arch §4.2.2).

    Single table per deployment-scoped Postgres (§4.2.6).
    """

    __tablename__ = "jobs_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default=JobState.PENDING.value)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)

    claim_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    claim_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    parent_job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("jobs_queue.id"), nullable=True
    )
    dedup_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    retry_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint("tenant_hash <> ''", name="tenant_hash_not_empty"),
        CheckConstraint("retry_count >= 0", name="retry_bounds"),
        UniqueConstraint("tenant_hash", "dedup_key", name="idx_jobs_dedup"),
        Index(
            "idx_jobs_pending_pickup",
            "next_retry_at",
            "created_at",
            postgresql_where="state = 'pending'",
        ),
        Index(
            "idx_jobs_orphan_reclaim",
            "claim_expires_at",
            postgresql_where="state = 'claimed'",
        ),
        Index(
            "idx_jobs_parent",
            "parent_job_id",
            postgresql_where="parent_job_id IS NOT NULL",
        ),
    )


class OutboxDrainRetries(RuntimeBase):
    """Per-event retry state for Path B tick-drain failures (arch §4.2.3)."""

    __tablename__ = "outbox_drain_retries"

    audit_event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    __table_args__ = (
        Index(
            "idx_outbox_retries_pending",
            "next_retry_at",
            postgresql_where="state = 'pending'",
        ),
    )


__all__ = [
    "RuntimeBase",
    "JobsQueue",
    "OutboxDrainRetries",
    "JobType",
    "JobState",
    "FailureReason",
]
