"""Bead data model — the atomic unit of the Beads audit trail (§3.2).

A bead is an immutable content-addressed snapshot pointing at:

    (previous_bead_hash, change_payload, timestamp, tenant_hash, operation_type)

The bead's `bead_hash` is `sha256(canonical_serialize(bead_contents))` — the
caller never supplies it; it is computed at construction time by
`content_hash.compute_bead_hash()`.

Beads form a Merkle chain per worktree. Under managed single-tenant, one
worktree per process means one chain per process. The genesis bead has
`previous_bead_hash == None`.

What goes into a bead (§3.2):
    - store_task_outcome write
    - store_decision write
    - store_fact write (ref to Mem0 fact id + minimal payload)
    - delete operation (hashed criteria per Req #33)
    - flag_and_quarantine operation

What does NOT go into a bead:
    - Pure retrievals
    - Telemetry events
    - Cache operations
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BeadOperationType(str, Enum):
    """Discriminator for the five write-side operations that produce beads."""

    GENESIS = "genesis"
    STORE_TASK_OUTCOME = "store_task_outcome"
    STORE_DECISION = "store_decision"
    STORE_FACT = "store_fact"
    DELETE = "delete"
    QUARANTINE = "quarantine"


class _BeadPayload(BaseModel):
    """Base class for all bead payloads.

    Concrete payloads (one per BeadOperationType) carry operation-specific
    content. They are all frozen Pydantic models with strict typing and no
    extra fields — canonical serialization depends on deterministic field
    ordering and no hidden state.

    Phase 3B-i ships a minimal payload set sufficient for the five
    operation types. Phase 3B/3C may extend individual payloads with extra
    context; each extension requires a payload-level `schema_version` bump
    so downstream replay knows how to interpret the change_payload dict.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    payload_schema_version: int = 1


class GenesisPayload(_BeadPayload):
    """Payload for the genesis bead (first bead in a chain).

    Carries the tenant identity stamp the worktree was created under so
    later replays can detect tampering (a mismatch between genesis
    `tenant_hash` and the DeploymentManifest hash hard-fails the process
    at boot per §3.3).
    """

    operation: Literal[BeadOperationType.GENESIS] = BeadOperationType.GENESIS
    note: str = "genesis"


class StoreTaskOutcomePayload(_BeadPayload):
    """Payload for a `store_task_outcome` audit bead.

    Carries the task signature hash + outcome summary. The FULL outcome
    is held in the primary store (Atelier); the bead is the durable audit
    record that "something was stored" with enough information to replay
    state if needed.
    """

    operation: Literal[BeadOperationType.STORE_TASK_OUTCOME] = BeadOperationType.STORE_TASK_OUTCOME
    entry_id: str
    task_signature_hash: str
    quality_score: float
    cost_usd: float


class StoreDecisionPayload(_BeadPayload):
    """Payload for a `store_decision` audit bead."""

    operation: Literal[BeadOperationType.STORE_DECISION] = BeadOperationType.STORE_DECISION
    entry_id: str
    decision_summary: str
    confidence: float


class StoreFactPayload(_BeadPayload):
    """Payload for a `store_fact` audit bead.

    Stores only the Mem0 fact id + minimal summary, not the raw fact text
    (Mem0 holds the fact). Per §3.2 "store_fact write (reference to Mem0
    fact ID + minimal payload)".
    """

    operation: Literal[BeadOperationType.STORE_FACT] = BeadOperationType.STORE_FACT
    entry_id: str
    mem0_fact_id: str
    agent_id: str
    run_id: str


class DeletePayload(_BeadPayload):
    """Payload for a `delete` operation audit bead (Req #33).

    `criteria_hash` is a salted sha256 of the delete criteria — NEVER the
    raw criteria. §8.4 "no raw criteria in audit logs".
    """

    operation: Literal[BeadOperationType.DELETE] = BeadOperationType.DELETE
    job_id: str
    criteria_hash: str
    deleted_entry_count: int
    full_tenant: bool = False


class QuarantinePayload(_BeadPayload):
    """Payload for a `flag_and_quarantine` audit bead (§8.7).

    Carries the reason enum + a salted sha256 of any caller-supplied
    free-text. Free-text itself is PII-scrubbed before hashing.
    """

    operation: Literal[BeadOperationType.QUARANTINE] = BeadOperationType.QUARANTINE
    entry_id: str
    reason: str
    reason_hash: str


BeadPayload = (
    GenesisPayload
    | StoreTaskOutcomePayload
    | StoreDecisionPayload
    | StoreFactPayload
    | DeletePayload
    | QuarantinePayload
)


class Bead(BaseModel):
    """One bead in the Merkle chain.

    The `bead_hash` field is the content address — sha256 of the canonical
    serialization of every other field except `bead_hash` itself. Callers
    should NOT set `bead_hash` directly; use
    `content_hash.compute_bead_hash()` to derive it and then construct the
    Bead with the computed hash.

    Beads are frozen — once constructed they cannot be mutated. A new
    chain entry always means constructing a new Bead with the new state.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    bead_hash: str
    previous_bead_hash: str | None
    timestamp: datetime
    tenant_hash: str
    operation_type: BeadOperationType
    payload: BeadPayload


__all__ = [
    "Bead",
    "BeadOperationType",
    "BeadPayload",
    "DeletePayload",
    "GenesisPayload",
    "QuarantinePayload",
    "StoreDecisionPayload",
    "StoreFactPayload",
    "StoreTaskOutcomePayload",
]
