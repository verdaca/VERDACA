"""Public Pydantic input / output models for the Memory facade.

Every model is frozen (`ConfigDict(frozen=True)`) per architecture §2.2 —
records are values, not handles. Post-construction mutation is forbidden.

This module is the ONE place application code is allowed to construct Memory
inputs and destructure Memory outputs. It sits at the public surface of
`praxis.kernel.memory`; it does NOT import from `_internal`.

Draft / Record pattern
----------------------

For every persisted entity the module exposes two types:

  - `*Draft`  — the caller-constructable input: semantic fields only, no
                persistence columns. Inherits `_FrozenModel`.
  - `*Record` — the value returned by the Memory layer after persisting:
                all Draft fields PLUS the persistence columns from
                `_PersistedRecord`. Inherits `_FrozenModel` indirectly.

The three store methods on `MemoryProtocol` take a Draft and return a
Record. This is consistent across `store_task_outcome`, `store_decision`,
and `store_fact`. Callers never construct a Record directly and therefore
never populate fields that only the Memory layer is allowed to stamp
(entry_id, tenant_hash, created_at, state_snapshot_version).

Shared semantic fields live on a `_{Name}Core` Pydantic base. Draft and
Record both inherit from the Core, which keeps the two in lock-step with
zero field duplication.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Bases
# =============================================================================


class _FrozenModel(BaseModel):
    """Shared config: frozen, strict, no extra fields.

    All Memory models inherit from this. Extra fields are rejected at
    validation time so silent schema drift between layers is impossible.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class _PersistedRecord(_FrozenModel):
    """Mixin-style base for records the Memory layer has persisted.

    Architecture §2.2 names three implicit columns for persisted records;
    this base extends that set with `entry_id` (the primary key without
    which the protocol's get/delete methods couldn't work) and
    `created_at` (the Memory-layer stamp, distinct from any caller-supplied
    semantic timestamp like `DecisionDraft.captured_at`).

    Fields
    ------
    entry_id
        Memory-assigned primary key. Callers never supply this.
    tenant_hash
        Derived from the deployment manifest at write time (Req #6).
        Startup sample-scan uses this for drift detection.
    schema_version
        Version of the PERSISTED STORAGE LAYOUT. Distinct from any
        input-schema version on caller-constructed Drafts (e.g.
        `TaskSignature.schema_version`). The two can legitimately
        diverge: a caller speaking TaskSignature input-schema v1.2 may
        produce records stored under persistence layout v2.0.
    state_snapshot_version
        Opaque token returned on retrieval for deterministic replay
        (Req #44).
    created_at
        Timestamp the Memory layer stamped when persisting.
    """

    entry_id: str
    tenant_hash: str
    schema_version: int = 1
    state_snapshot_version: str
    created_at: datetime


# =============================================================================
# Enums / Literals
# =============================================================================


#: Discriminator for retrieval hits. Type-safe via `Literal` — consumers can
#: `match hit.record_type: case "decision": ...` without importing any Pydantic
#: discriminator machinery. Each Record type also carries a class-level
#: default of its own Literal so records are self-describing.
RecordType = Literal["task_outcome", "decision", "fact"]


class OutcomeStatus(str, Enum):
    """Later-filled status of a decision outcome (§2.2 DecisionRecord)."""

    PENDING = "pending"
    VALIDATED = "validated"
    REFUTED = "refuted"
    ABANDONED = "abandoned"


class QuarantineReason(str, Enum):
    """Structured quarantine reason enum (Req #45, §8.7)."""

    PII_LEAK = "pii_leak"
    HALLUCINATION = "hallucination"
    OUTDATED = "outdated"
    POISONED = "poisoned"
    OTHER = "other"


class DeleteSubstepStatus(str, Enum):
    """State of one substep in the delete cascade (§8.5)."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class HealthStatus(str, Enum):
    """Coarse health status for the facade aggregate."""

    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


# =============================================================================
# Leaf value objects
# =============================================================================


class ReasoningStep(_FrozenModel):
    """One entry in a TaskOutcome's reasoning trace."""

    step_index: int
    agent_id: str
    summary: str


class DissentRecord(_FrozenModel):
    """An alternative view that the deliberation surfaced but did not adopt."""

    dissenter_agent_id: str
    position: str
    rationale: str


class EvidenceItem(_FrozenModel):
    """One piece of evidence that backed a decision."""

    source: str
    excerpt: str


# =============================================================================
# TaskSignature (input to retrieve / store task outcomes)
# =============================================================================


class TaskSignature(_FrozenModel):
    """Canonical fingerprint of a task for cross-session retrieval (§2.2).

    Two task invocations with the same TaskSignature are considered "the
    same task" for retrieval/learning purposes. Callers construct this
    from the user prompt + resolved agent set + context fingerprint.
    """

    task_type: str
    """High-level task category, e.g. 'strategic_advisory'."""

    input_hash: str
    """sha256 of canonicalized user input. Deterministic."""

    agents_involved: tuple[str, ...]
    """Sorted tuple of agent IDs. Tuple (not list) because models are frozen."""

    context_fingerprint: str
    """Rolling hash of retrieved context. Differs when the world changes."""

    schema_version: int = Field(
        default=1,
        description=(
            "Version of the TaskSignature INPUT schema used by the caller. "
            "Distinct from _PersistedRecord.schema_version which tracks the "
            "STORAGE LAYOUT of persisted records. The two can legitimately "
            "diverge: a caller using TaskSignature v1.2 may produce records "
            "stored under persistence layout v2.0."
        ),
    )


# =============================================================================
# TaskOutcome Draft / Record
# =============================================================================


class _TaskOutcomeCore(_FrozenModel):
    """Shared semantic fields for TaskOutcomeDraft and TaskOutcomeRecord."""

    quality_score: float
    quality_confidence: float
    cost_usd: float
    reasoning_trace: list[ReasoningStep]
    approach_summary: str
    dissents: list[DissentRecord] = []


class TaskOutcomeDraft(_TaskOutcomeCore):
    """Input to `store_task_outcome` — caller-constructed outcome fields.

    Contains only the semantic outcome content. The TaskSignature is
    passed as a separate argument to `store_task_outcome`, not bundled
    into this Draft.
    """


class TaskOutcomeRecord(_TaskOutcomeCore, _PersistedRecord):
    """Persisted task outcome returned from `store_task_outcome`.

    Bundles the outcome content, the signature used to look it up, and
    the persistence columns (entry_id, tenant_hash, created_at, etc.)
    that only the Memory layer is allowed to stamp.
    """

    record_type: Literal["task_outcome"] = "task_outcome"
    signature: TaskSignature


# =============================================================================
# Decision Draft / Record
# =============================================================================


class _DecisionCore(_FrozenModel):
    """Shared semantic fields for DecisionDraft and DecisionRecord."""

    decision: str
    rationale: str
    alternatives_considered: list[str]
    evidence: list[EvidenceItem]
    confidence: float
    outcome: OutcomeStatus | None = None
    captured_at: datetime
    """Caller-supplied 'when I captured this decision' timestamp. Distinct
    from `_PersistedRecord.created_at` which is stamped by the Memory layer."""
    ttl_days: int = 365


class DecisionDraft(_DecisionCore):
    """Input to `store_decision` — caller-constructed decision fields."""


class DecisionRecord(_DecisionCore, _PersistedRecord):
    """Persisted Atelier-style decision record returned from `store_decision`."""

    record_type: Literal["decision"] = "decision"


# =============================================================================
# Fact Draft / Record
# =============================================================================


class _FactCore(_FrozenModel):
    """Shared semantic fields for FactDraft and FactRecord."""

    fact: str
    source_excerpt: str | None = None


class FactDraft(_FactCore):
    """Input to `store_fact` — caller-constructed fact content.

    The Mem0 three-axis scoping (user_id, agent_id, run_id) is NOT carried
    in the Draft — those are passed to `store_fact` as separate arguments
    (tenant_id, agent_id, run_id) and the Mem0 adapter assembles them at
    its boundary.
    """


class FactRecord(_FactCore, _PersistedRecord):
    """Persisted Mem0 fact returned from `store_fact`."""

    record_type: Literal["fact"] = "fact"


# =============================================================================
# Retrieval
# =============================================================================


class SourceDistribution(_FrozenModel):
    """Breakdown of retrieval result origins for telemetry (§8.4, Req #22).

    Every `retrieve_*` call emits this alongside the hit list so operators
    can see tenant-corpus vs seed-corpus balance without seeing query
    content. Per §8.4 philosophy: typed submodel, never a raw dict.
    """

    tenant_hits: int
    seed_hits: int


class RetrievalHit(_FrozenModel):
    """One result row returned from any retrieve_* method.

    `record_type` is a Literal discriminator — consumers branch with
    `match hit.record_type` without importing any discriminator machinery.
    `record` carries the polymorphic payload typed as a union.
    """

    entry_id: str
    similarity: float
    record_type: RecordType
    record: TaskOutcomeRecord | DecisionRecord | FactRecord


class RetrievalResult(_FrozenModel):
    """Container returned by every retrieve_* method."""

    hits: list[RetrievalHit]
    source_distribution: SourceDistribution
    retrieval_latency_ms: float


# =============================================================================
# GDPR delete
# =============================================================================


class DeleteCriteria(_FrozenModel):
    """Criteria for a right-to-erasure cascade (§8.5, Req #24)."""

    entry_ids: list[str] = []
    full_tenant: bool = False


class DeleteResult(_FrozenModel):
    """Returned only after the full cascade finishes (§8.5)."""

    job_id: str
    deleted_entry_count: int
    substep_status: dict[str, DeleteSubstepStatus]
    crypto_shred_initiated: bool = False


# =============================================================================
# GDPR export (Article 15)
# =============================================================================


class ExportCriteria(_FrozenModel):
    """Criteria for a right-to-access export (§8.6, Req #37)."""

    entry_ids: list[str] = []
    full_tenant: bool = False


class ExportResult(_FrozenModel):
    """Returned by Memory.export (§8.6)."""

    artifact_path: str
    record_count: int
    access_token: str


# =============================================================================
# Quarantine
# =============================================================================


class QuarantineResult(_FrozenModel):
    """Returned by Memory.flag_and_quarantine (§8.7)."""

    entry_id: str
    previous_state_snapshot_version: str
    new_state_snapshot_version: str
    embedding_stripped: bool
    """Must be True on success — FM3.10 override mandates in-place strip (Req #35)."""


# =============================================================================
# Health
# =============================================================================


class BackendHealth(_FrozenModel):
    """Per-backend health line item."""

    backend: str
    status: HealthStatus
    detail: str | None = None


class HealthReport(_FrozenModel):
    """Result of Memory.health() — aggregated across all backends."""

    overall: HealthStatus
    backends: list[BackendHealth]
    manifest_last_reverified_at: datetime


# =============================================================================
# Errors
# =============================================================================


class TenantIdentityError(PermissionError):
    """Raised when the tenant_id argument does not match the deployment manifest.

    Per §8.2 this is a defense-in-depth check: under managed single-tenant
    the application should never pass a mismatched tenant_id, so a raise
    here indicates a bug and is intended to hard-fail the process.
    """


class MemoryBackendError(RuntimeError):
    """Raised when a backend reports an unrecoverable operational error.

    Wraps vendor-specific exceptions (Mem0, SQLAlchemy, pgvector) at the
    adapter boundary so those types never leak into application code.
    """


class MemoryRecordNotFound(LookupError):
    """Raised when a lookup by entry_id returns no result."""


class MemoryQuotaExceeded(Exception):
    """Raised when a tenant has exceeded the per-tenant entry ceiling.

    Base class is plain `Exception` — NOT `MemoryBackendError` (this is
    not an operational failure), NOT `PermissionError` (not a privacy
    violation). Quota exhaustion is its own fourth error category:
    a policy condition.

    Raised by
    ---------
    - `store_task_outcome`, `store_decision`, `store_fact` — raise on
      HARD ceiling (NR-Q2 ratified at 250K). The Memory layer never
      partially applies a store that exceeds the hard ceiling.
    - Soft ceiling (NR-Q2 ratified at 100K): NOT raised as an exception;
      the store succeeds and a warning-level telemetry event is emitted
      for MAC (Stage 5) to pick up and drive the experience-library
      compaction workflow.

    Never raised by
    ---------------
    - Read methods (`retrieve_*`, `export`) — quota governs writes only.
    - `delete` and `flag_and_quarantine` — both decrease the count.
    - `health` — observational only.

    Attributes
    ----------
    tenant_id : str
        The tenant whose ceiling tripped. Redundant with the current
        process's tenant, but carried explicitly so MAC error-handling
        does not need to reach for DeploymentManifest singletons.
    current_count : int
        Count observed at the time the write was rejected.
    ceiling_type : Literal["soft", "hard"]
        Which ceiling was crossed. For the exception-raising case this
        is always "hard" — soft crossings are telemetry only — but the
        field is kept so downstream tooling can handle the warning-log
        projection uniformly with exception projections.
    ceiling_value : int
        The numeric value of the ceiling that was crossed (100_000 or
        250_000 per NR-Q2, at the time of writing).
    """

    def __init__(
        self,
        tenant_id: str,
        current_count: int,
        ceiling_type: Literal["soft", "hard"],
        ceiling_value: int,
    ) -> None:
        self.tenant_id = tenant_id
        self.current_count = current_count
        self.ceiling_type = ceiling_type
        self.ceiling_value = ceiling_value
        super().__init__(
            f"Tenant {tenant_id} exceeded {ceiling_type} ceiling: {current_count}/{ceiling_value}"
        )


__all__ = [
    "BackendHealth",
    "DecisionDraft",
    "DecisionRecord",
    "DeleteCriteria",
    "DeleteResult",
    "DeleteSubstepStatus",
    "DissentRecord",
    "EvidenceItem",
    "ExportCriteria",
    "ExportResult",
    "FactDraft",
    "FactRecord",
    "HealthReport",
    "HealthStatus",
    "MemoryBackendError",
    "MemoryQuotaExceeded",
    "MemoryRecordNotFound",
    "OutcomeStatus",
    "QuarantineReason",
    "QuarantineResult",
    "ReasoningStep",
    "RecordType",
    "RetrievalHit",
    "RetrievalResult",
    "SourceDistribution",
    "TaskOutcomeDraft",
    "TaskOutcomeRecord",
    "TaskSignature",
    "TenantIdentityError",
]
