"""BeadsStore — append-only content-addressed audit log (§3.6).

Phase 3B-i implementation notes
-------------------------------

BeadsStore is the audit-trail backend for the Memory facade. Its
MemoryProtocol implementation covers the WRITE side (store_*, delete,
flag_and_quarantine) by appending a corresponding bead to the Merkle
chain. The READ side (retrieve_*, export) returns empty results because
Beads is not a semantic retrieval store — Atelier (decisions) and Mem0
(facts) own that responsibility.

The in-memory `dict[str, Bead]` backing store is the Phase 3B-i storage.
Postgres-backed storage via the NR-SC-R2 engine
(`praxis.kernel.memory._internal.common.db`) is a later amelioration; the
Bead model and hashing logic are identical, only the persistence layer
changes. That is an intentional abstraction: Phase 3B-i proves the
algorithms; a later phase swaps the storage.

In Phase 3C facade composition, BeadsStore is called as a side-channel:
the facade's store_task_outcome dispatches the primary write to Atelier
AND fires a BeadsStore.store_task_outcome(...) audit bead. The Record
returned by the facade is Atelier's; Beads-standalone tests use Beads'
own synthesized Record to satisfy the MemoryProtocol signature.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
import uuid
from datetime import datetime, timezone
from threading import Lock

from praxis.kernel.memory._internal.beads.content_hash import compute_bead_hash
from praxis.kernel.memory._internal.beads.models import (
    Bead,
    BeadOperationType,
    DeletePayload,
    GenesisPayload,
    QuarantinePayload,
    StoreDecisionPayload,
    StoreFactPayload,
    StoreTaskOutcomePayload,
)
from praxis.kernel.memory.models import (
    BackendHealth,
    DecisionDraft,
    DecisionRecord,
    DeleteCriteria,
    DeleteResult,
    DeleteSubstepStatus,
    ExportCriteria,
    ExportResult,
    FactDraft,
    FactRecord,
    HealthReport,
    HealthStatus,
    MemoryBackendError,
    QuarantineReason,
    QuarantineResult,
    RetrievalResult,
    SourceDistribution,
    TaskOutcomeDraft,
    TaskOutcomeRecord,
    TaskSignature,
    TenantIdentityError,
)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_entry_id() -> str:
    return uuid.uuid4().hex


class BeadsStore:
    """Append-only Merkle chain of beads + minimal MemoryProtocol surface.

    Parameters
    ----------
    tenant_hash
        The tenant this store is scoped to. Set once at construction —
        BeadsStore is per-process per §3.3.

    Attributes
    ----------
    head
        Hash of the most recently appended bead. `None` before genesis.
    """

    def __init__(self, *, tenant_hash: str) -> None:
        self._tenant_hash = tenant_hash
        self._beads: dict[str, Bead] = {}
        self._head: str | None = None
        self._lock = Lock()
        self._seed_genesis()

    # ------------------------------------------------------------------
    # Public chain API (non-protocol)
    # ------------------------------------------------------------------

    @property
    def tenant_hash(self) -> str:
        return self._tenant_hash

    @property
    def head(self) -> str | None:
        """Hash of the most recently appended bead, or None before genesis."""
        return self._head

    def __len__(self) -> int:
        return len(self._beads)

    def get_bead(self, bead_hash: str) -> Bead | None:
        """Look up a bead by its content hash. Returns None if absent."""
        return self._beads.get(bead_hash)

    def iter_chain(self) -> list[Bead]:
        """Walk the chain from genesis to head. Returns a list in order.

        Used by `replay` and by the doctor check that the chain has no
        orphaned beads or broken parent pointers.
        """
        ordered: list[Bead] = []
        cursor = self._head
        while cursor is not None:
            bead = self._beads[cursor]
            ordered.append(bead)
            cursor = bead.previous_bead_hash
        return list(reversed(ordered))

    # ------------------------------------------------------------------
    # Internal chain append (the core invariant — everything routes here)
    # ------------------------------------------------------------------

    def _append(
        self,
        operation_type: BeadOperationType,
        payload: object,
    ) -> Bead:
        """Construct, hash, and append a new bead.

        Thread-safe via the instance lock — concurrent calls from
        parallel agents within the same process serialize on append.
        """
        with self._lock:
            timestamp = _utc_now()
            bead_hash = compute_bead_hash(
                previous_bead_hash=self._head,
                timestamp=timestamp.isoformat(),
                tenant_hash=self._tenant_hash,
                operation_type=operation_type,
                payload=payload,  # type: ignore[arg-type]
            )
            bead = Bead(
                bead_hash=bead_hash,
                previous_bead_hash=self._head,
                timestamp=timestamp,
                tenant_hash=self._tenant_hash,
                operation_type=operation_type,
                payload=payload,  # type: ignore[arg-type]
            )
            self._beads[bead_hash] = bead
            self._head = bead_hash
            return bead

    def _seed_genesis(self) -> None:
        """Create the first bead in the chain.

        Under §3.3 the genesis bead stamps the tenant identity so later
        replays detect worktree tampering.
        """
        self._append(BeadOperationType.GENESIS, GenesisPayload())

    # ------------------------------------------------------------------
    # Tenant guard — defense in depth (§8.2)
    # ------------------------------------------------------------------

    def _require_tenant(self, tenant_id: str) -> None:
        if tenant_id != self._tenant_hash:
            raise TenantIdentityError(
                f"tenant_id {tenant_id!r} does not match BeadsStore "
                f"tenant_hash {self._tenant_hash!r}"
            )

    # ------------------------------------------------------------------
    # MemoryProtocol — write path
    # ------------------------------------------------------------------

    async def store_task_outcome(
        self,
        tenant_id: str,
        task: TaskSignature,
        outcome: TaskOutcomeDraft,
    ) -> TaskOutcomeRecord:
        self._require_tenant(tenant_id)
        entry_id = _new_entry_id()

        # Compute a stable signature hash for the audit payload. The real
        # Stage 3 canonical hash algorithm is part of cross-session
        # learning (Stage 5) — here we use the input_hash as the
        # signature's identity under the constraint that callers
        # constructed `task` with a deterministic input_hash.
        payload = StoreTaskOutcomePayload(
            entry_id=entry_id,
            task_signature_hash=task.input_hash,
            quality_score=outcome.quality_score,
            cost_usd=outcome.cost_usd,
        )
        bead = await asyncio.to_thread(self._append, BeadOperationType.STORE_TASK_OUTCOME, payload)

        return TaskOutcomeRecord(
            entry_id=entry_id,
            tenant_hash=self._tenant_hash,
            schema_version=1,
            state_snapshot_version=bead.bead_hash,
            created_at=bead.timestamp,
            signature=task,
            quality_score=outcome.quality_score,
            quality_confidence=outcome.quality_confidence,
            cost_usd=outcome.cost_usd,
            reasoning_trace=outcome.reasoning_trace,
            approach_summary=outcome.approach_summary,
            dissents=outcome.dissents,
        )

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        self._require_tenant(tenant_id)
        entry_id = _new_entry_id()
        payload = StoreDecisionPayload(
            entry_id=entry_id,
            decision_summary=decision.decision[:256],
            confidence=decision.confidence,
        )
        bead = await asyncio.to_thread(self._append, BeadOperationType.STORE_DECISION, payload)
        return DecisionRecord(
            entry_id=entry_id,
            tenant_hash=self._tenant_hash,
            schema_version=1,
            state_snapshot_version=bead.bead_hash,
            created_at=bead.timestamp,
            decision=decision.decision,
            rationale=decision.rationale,
            alternatives_considered=decision.alternatives_considered,
            evidence=decision.evidence,
            confidence=decision.confidence,
            outcome=decision.outcome,
            captured_at=decision.captured_at,
            ttl_days=decision.ttl_days,
        )

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactDraft,
    ) -> FactRecord:
        self._require_tenant(tenant_id)
        entry_id = _new_entry_id()
        # The real Mem0 fact id comes from the Mem0 adapter (3B-ii). For
        # a standalone Beads store we mint one so the audit payload is
        # well-formed.
        mem0_fact_id = _new_entry_id()
        payload = StoreFactPayload(
            entry_id=entry_id,
            mem0_fact_id=mem0_fact_id,
            agent_id=agent_id,
            run_id=run_id,
        )
        bead = await asyncio.to_thread(self._append, BeadOperationType.STORE_FACT, payload)
        return FactRecord(
            entry_id=entry_id,
            tenant_hash=self._tenant_hash,
            schema_version=1,
            state_snapshot_version=bead.bead_hash,
            created_at=bead.timestamp,
            fact=fact.fact,
            source_excerpt=fact.source_excerpt,
        )

    # ------------------------------------------------------------------
    # MemoryProtocol — read path (not implemented — Beads is audit only)
    # ------------------------------------------------------------------

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: TaskSignature,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be in [0, 1]")
        return _empty_retrieval_result()

    async def retrieve_decisions(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not query.strip():
            raise ValueError("query must be non-empty")
        return _empty_retrieval_result()

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not query.strip():
            raise ValueError("query must be non-empty")
        return _empty_retrieval_result()

    # ------------------------------------------------------------------
    # MemoryProtocol — GDPR path
    # ------------------------------------------------------------------

    async def delete(
        self,
        tenant_id: str,
        criteria: DeleteCriteria,
    ) -> DeleteResult:
        self._require_tenant(tenant_id)
        if not criteria.entry_ids and not criteria.full_tenant:
            raise ValueError("DeleteCriteria must specify entry_ids or full_tenant")

        job_id = _new_entry_id()
        # A salted-hash of the criteria would be derived at the facade
        # boundary (§8.4). For standalone Beads the hash input is just
        # the set of ids — tests cover that the audit bead is appended.
        criteria_hash = _hash_delete_criteria(criteria)
        deleted_count = len(criteria.entry_ids)

        payload = DeletePayload(
            job_id=job_id,
            criteria_hash=criteria_hash,
            deleted_entry_count=deleted_count,
            full_tenant=criteria.full_tenant,
        )
        await asyncio.to_thread(self._append, BeadOperationType.DELETE, payload)

        return DeleteResult(
            job_id=job_id,
            deleted_entry_count=deleted_count,
            substep_status={"beads_audit_bead": DeleteSubstepStatus.SUCCEEDED},
            crypto_shred_initiated=criteria.full_tenant,
        )

    async def export(
        self,
        tenant_id: str,
        criteria: ExportCriteria,
    ) -> ExportResult:
        self._require_tenant(tenant_id)
        if not criteria.entry_ids and not criteria.full_tenant:
            raise ValueError("ExportCriteria must specify entry_ids or full_tenant")
        # Beads alone does not export records — the facade orchestrates
        # Atelier + Mem0 for the real export. Here we return a zero-record
        # marker to satisfy the protocol.
        return ExportResult(
            artifact_path=os.path.join(
                tempfile.gettempdir(), f"beads-export-{_new_entry_id()}.json"
            ),
            record_count=0,
            access_token=_new_entry_id(),
        )

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult:
        self._require_tenant(tenant_id)
        if not entry_id:
            raise MemoryBackendError("entry_id must be non-empty")

        # Real facade does PII-scrubbing + salted hash before calling
        # down; Beads just records the reason code + a non-cryptographic
        # hash placeholder so the audit payload is well-formed.
        reason_hash = _hash_quarantine_reason(reason, free_text)
        previous_head = self._head or ""

        payload = QuarantinePayload(
            entry_id=entry_id,
            reason=reason.value,
            reason_hash=reason_hash,
        )
        bead = await asyncio.to_thread(self._append, BeadOperationType.QUARANTINE, payload)

        return QuarantineResult(
            entry_id=entry_id,
            previous_state_snapshot_version=previous_head,
            new_state_snapshot_version=bead.bead_hash,
            embedding_stripped=True,
        )

    # ------------------------------------------------------------------
    # MemoryProtocol — observability
    # ------------------------------------------------------------------

    async def health(self) -> HealthReport:
        status = HealthStatus.OK if self._head is not None else HealthStatus.DEGRADED
        return HealthReport(
            overall=status,
            backends=[
                BackendHealth(
                    backend="beads",
                    status=status,
                    detail=f"chain_length={len(self._beads)}",
                )
            ],
            manifest_last_reverified_at=_utc_now(),
        )


# =============================================================================
# Helpers
# =============================================================================


def _empty_retrieval_result() -> RetrievalResult:
    return RetrievalResult(
        hits=[],
        source_distribution=SourceDistribution(tenant_hits=0, seed_hits=0),
        retrieval_latency_ms=0.0,
    )


def _hash_delete_criteria(criteria: DeleteCriteria) -> str:
    payload = f"full={criteria.full_tenant}|ids={','.join(sorted(criteria.entry_ids))}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_quarantine_reason(reason: QuarantineReason, free_text: str | None) -> str:
    payload = f"{reason.value}|{free_text or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["BeadsStore"]
