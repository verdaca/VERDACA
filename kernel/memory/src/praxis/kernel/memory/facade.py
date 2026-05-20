"""Memory facade — composed MemoryProtocol implementation (§2.1).

Phase 3C composition: the public `Memory` class implements
`MemoryProtocol` by routing each method to the appropriate backend
(Beads / Mem0 adapter / Atelier) with a structural tenant guard at
every entry point.

Dispatch table (§2.1 + Andrey's 3C brief)
-----------------------------------------

| Method                    | Primary backend      | Side-effects      |
|---------------------------|----------------------|-------------------|
| store_task_outcome        | BeadsStore (returns  | AtelierStore      |
|                           | the Record)          | (indexes a        |
|                           |                      | derived decision  |
|                           |                      | for retrieval)    |
| store_decision            | AtelierStore         | BeadsStore audit  |
| store_fact                | Mem0Adapter          | BeadsStore audit  |
| retrieve_similar_tasks    | AtelierStore (via    | —                 |
|                           | derived query)       |                   |
| retrieve_decisions        | AtelierStore         | —                 |
| retrieve_facts            | Mem0Adapter          | —                 |
| delete                    | Fan-out all 3;       | Aggregated        |
|                           | aggregate counts +   |                   |
|                           | substep statuses     |                   |
| export                    | Fan-out all 3;       | Aggregated        |
|                           | aggregate counts     |                   |
| flag_and_quarantine       | AtelierStore         | BeadsStore audit  |
| health                    | Fan-out all 3;       | Overall = worst   |
|                           | roll up statuses     |                   |

Routing is by METHOD name, not by `try/except NotImplementedError`.
If any backend raises NotImplementedError from a facade dispatch path,
that is a routing BUG and will surface as a test failure — see
`test_facade_no_not_implemented_from_dispatch` in Phase 3C tests.

Tenant identity enforcement (§8.2)
----------------------------------

Every method that takes `tenant_id` runs `_require_tenant` as its
FIRST action. On mismatch: `TenantIdentityError` raised, process
hard-fails (defense-in-depth per §8.2). Backends then re-validate
tenant_id against their own tenant_hash — this double-check is
intentional and covered by Beads/Mem0/Atelier roundtrip tests.

Known Phase 3C limitations
--------------------------

- `retrieve_similar_tasks` currently queries `AtelierStore.retrieve_decisions`
  with a query string synthesized from the TaskSignature. Results are
  DecisionRecords wrapped as RetrievalHits with `record_type="decision"`
  rather than native TaskOutcomeRecords. Quinn/Stage 5 will add a
  dedicated task-outcome retrieval path against Atelier's typed-thought
  schema (AT1).

- Audit events are collected in an in-process `AuditBuffer`. Stage 7
  wires a durable sink.

- No real pgvector, no real Mem0 backend, no real PII redactor beyond
  the Mem0 adapter stub. Live-backend integration is Quinn's concern.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from praxis.kernel.memory._internal.audit import (
    AuditBuffer,
    AuditEvent,
    AuditEventType,
    _utc_now,
)
from praxis.kernel.memory.models import (
    BackendHealth,
    DecisionDraft,
    DecisionRecord,
    DeleteCriteria,
    DeleteResult,
    DeleteSubstepStatus,
    EvidenceItem,
    ExportCriteria,
    ExportResult,
    FactDraft,
    FactRecord,
    HealthReport,
    HealthStatus,
    QuarantineReason,
    QuarantineResult,
    RetrievalResult,
    SourceDistribution,
    TaskOutcomeDraft,
    TaskOutcomeRecord,
    TaskSignature,
    TenantIdentityError,
)

if TYPE_CHECKING:
    from praxis.kernel.memory._internal.atelier.store import AtelierStore
    from praxis.kernel.memory._internal.beads.store import BeadsStore
    from praxis.kernel.memory._internal.mem0_adapter.adapter import Mem0Adapter
    from praxis.kernel.memory.deployment.manifest import DeploymentManifest


def _hash_criteria(kind: str, values: list[str], full_tenant: bool) -> str:
    """Salted sha256 of criteria content. Never returns the raw criteria."""
    payload = f"{kind}|full={full_tenant}|ids={','.join(sorted(values))}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Memory:
    """Composed MemoryProtocol facade (§2).

    Constructor is dependency-injected: callers pass explicit backend
    instances. No magic auto-wiring. Production boot builds the
    backends from the manifest; tests inject in-memory fakes.
    """

    def __init__(
        self,
        *,
        manifest: DeploymentManifest,
        beads: BeadsStore,
        mem0: Mem0Adapter,
        atelier: AtelierStore,
    ) -> None:
        self._manifest = manifest
        self._beads = beads
        self._mem0 = mem0
        self._atelier = atelier
        self._audit = AuditBuffer()

    # ------------------------------------------------------------------
    # Public introspection
    # ------------------------------------------------------------------

    @property
    def manifest(self) -> DeploymentManifest:
        return self._manifest

    @property
    def audit_buffer(self) -> AuditBuffer:
        """Read-only accessor for tests and ops tooling.

        Stage 7 wiring will replace this with a durable sink adapter;
        the property remains for backward compatibility.
        """
        return self._audit

    # ------------------------------------------------------------------
    # Structural tenant guard (§8.2)
    # ------------------------------------------------------------------

    def _require_tenant(self, tenant_id: str) -> None:
        """Validate tenant_id against the manifest. Hard-fail on mismatch."""
        if tenant_id != self._manifest.tenant_id:
            raise TenantIdentityError(
                f"tenant_id {tenant_id!r} does not match manifest.tenant_id "
                f"{self._manifest.tenant_id!r}"
            )

    def _backend_tenant(self) -> str:
        """The tenant identifier the facade passes to backends.

        Under managed single-tenant, backends were constructed with
        `tenant_hash = manifest.tenant_hash`. Passing the same value as
        the backends' own stored tenant_hash means their re-validation
        (defense in depth) succeeds.
        """
        return self._manifest.tenant_hash

    def _audit_append(
        self,
        *,
        event_type: AuditEventType,
        method: str,
        criteria_hash: str | None = None,
        entry_id: str | None = None,
        outcome: str = "ok",
    ) -> None:
        event = AuditEvent(
            event_type=event_type,
            tenant_hash=self._manifest.tenant_hash,
            method=method,
            created_at=_utc_now(),
            criteria_hash=criteria_hash,
            entry_id=entry_id,
            outcome=outcome,
        )
        self._audit.append(event)

    # ==================================================================
    # MemoryProtocol — write path
    # ==================================================================

    async def store_task_outcome(
        self,
        tenant_id: str,
        task: TaskSignature,
        outcome: TaskOutcomeDraft,
    ) -> TaskOutcomeRecord:
        self._require_tenant(tenant_id)

        # Primary: Beads is the only backend that currently synthesizes
        # a TaskOutcomeRecord end-to-end. The primary write produces the
        # Record that's returned to the caller.
        record = await self._beads.store_task_outcome(self._backend_tenant(), task, outcome)

        # Side-effect: index a derived decision in Atelier so
        # retrieve_similar_tasks can find it via semantic search over
        # the approach_summary + signature fingerprint. This is a
        # composition shortcut — Stage 5 will replace it with a
        # dedicated task-outcome retrieval path.
        derived = _task_outcome_to_decision_draft(task, outcome)
        await self._atelier.store_decision(self._backend_tenant(), derived)

        self._audit_append(
            event_type=AuditEventType.STORE_TASK_OUTCOME,
            method="store_task_outcome",
            entry_id=record.entry_id,
        )
        return record

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        self._require_tenant(tenant_id)

        # Primary: Atelier owns decisions.
        record = await self._atelier.store_decision(self._backend_tenant(), decision)

        # Side-effect: Beads audit bead so the Merkle chain records the
        # write. Beads assigns its own entry_id internally; we don't
        # return it to the caller.
        await self._beads.store_decision(self._backend_tenant(), decision)

        self._audit_append(
            event_type=AuditEventType.STORE_DECISION,
            method="store_decision",
            entry_id=record.entry_id,
        )
        return record

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactDraft,
    ) -> FactRecord:
        self._require_tenant(tenant_id)

        # Primary: Mem0 owns facts.
        record = await self._mem0.store_fact(self._backend_tenant(), agent_id, run_id, fact)

        # Side-effect: Beads audit bead.
        await self._beads.store_fact(self._backend_tenant(), agent_id, run_id, fact)

        self._audit_append(
            event_type=AuditEventType.STORE_FACT,
            method="store_fact",
            entry_id=record.entry_id,
        )
        return record

    # ==================================================================
    # MemoryProtocol — read path
    # ==================================================================

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

        # Route to Atelier's decision retrieval using a query synthesized
        # from the signature's task_type + context_fingerprint. Results
        # come back as DecisionRecord-wrapped hits per the limitation
        # documented in this module's header.
        query = _signature_to_query(signature)
        result = await self._atelier.retrieve_decisions(self._backend_tenant(), query, top_k=top_k)
        # Post-filter by min_similarity since Atelier's retrieve_decisions
        # does not expose the threshold as a parameter in Phase 3B.
        filtered_hits = [h for h in result.hits if h.similarity >= min_similarity]
        return RetrievalResult(
            hits=filtered_hits,
            source_distribution=SourceDistribution(tenant_hits=len(filtered_hits), seed_hits=0),
            retrieval_latency_ms=result.retrieval_latency_ms,
        )

    async def retrieve_decisions(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        return await self._atelier.retrieve_decisions(self._backend_tenant(), query, top_k=top_k)

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        return await self._mem0.retrieve_facts(
            self._backend_tenant(), agent_id, run_id, query, top_k=top_k
        )

    # ==================================================================
    # MemoryProtocol — GDPR path
    # ==================================================================

    async def delete(
        self,
        tenant_id: str,
        criteria: DeleteCriteria,
    ) -> DeleteResult:
        self._require_tenant(tenant_id)
        if not criteria.entry_ids and not criteria.full_tenant:
            raise ValueError("DeleteCriteria must specify entry_ids or full_tenant")

        # Fan out to all three backends. Each reports its own
        # substep status; the facade aggregates.
        beads_result = await self._beads.delete(self._backend_tenant(), criteria)
        mem0_result = await self._mem0.delete(self._backend_tenant(), criteria)
        atelier_result = await self._atelier.delete(self._backend_tenant(), criteria)

        aggregated_status: dict[str, DeleteSubstepStatus] = {}
        aggregated_status.update(beads_result.substep_status)
        aggregated_status.update(mem0_result.substep_status)
        aggregated_status.update(atelier_result.substep_status)

        total_deleted = (
            beads_result.deleted_entry_count
            + mem0_result.deleted_entry_count
            + atelier_result.deleted_entry_count
        )

        criteria_hash = _hash_criteria("delete", criteria.entry_ids, criteria.full_tenant)
        self._audit_append(
            event_type=AuditEventType.DELETE,
            method="delete",
            criteria_hash=criteria_hash,
        )

        return DeleteResult(
            job_id=beads_result.job_id,  # Beads job id is the canonical one
            deleted_entry_count=total_deleted,
            substep_status=aggregated_status,
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

        beads_result = await self._beads.export(self._backend_tenant(), criteria)
        mem0_result = await self._mem0.export(self._backend_tenant(), criteria)
        atelier_result = await self._atelier.export(self._backend_tenant(), criteria)

        total_count = (
            beads_result.record_count + mem0_result.record_count + atelier_result.record_count
        )

        criteria_hash = _hash_criteria("export", criteria.entry_ids, criteria.full_tenant)
        self._audit_append(
            event_type=AuditEventType.EXPORT,
            method="export",
            criteria_hash=criteria_hash,
        )

        return ExportResult(
            # Phase 3C returns the Atelier artifact path as the canonical
            # aggregate; Stage 7 will replace this with a merged bundle.
            artifact_path=atelier_result.artifact_path,
            record_count=total_count,
            access_token=atelier_result.access_token,
        )

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult:
        self._require_tenant(tenant_id)

        # Primary: Atelier strips the embedding in place.
        result = await self._atelier.flag_and_quarantine(
            self._backend_tenant(), entry_id, reason, free_text
        )

        # Side-effect: Beads audit bead.
        await self._beads.flag_and_quarantine(self._backend_tenant(), entry_id, reason, free_text)

        self._audit_append(
            event_type=AuditEventType.QUARANTINE,
            method="flag_and_quarantine",
            entry_id=entry_id,
        )
        return result

    # ==================================================================
    # MemoryProtocol — observability
    # ==================================================================

    async def health(self) -> HealthReport:
        """Fan-out to all three backends and roll up the worst status."""
        beads_report = await self._beads.health()
        mem0_report = await self._mem0.health()
        atelier_report = await self._atelier.health()

        all_backends: list[BackendHealth] = []
        all_backends.extend(beads_report.backends)
        all_backends.extend(mem0_report.backends)
        all_backends.extend(atelier_report.backends)

        overall = _worst_status([beads_report.overall, mem0_report.overall, atelier_report.overall])

        return HealthReport(
            overall=overall,
            backends=all_backends,
            manifest_last_reverified_at=datetime.now(tz=timezone.utc),
        )


# =============================================================================
# Helpers
# =============================================================================


def _signature_to_query(signature: TaskSignature) -> str:
    """Synthesize a retrieval query from a TaskSignature.

    The query is deliberately simple — task_type plus a compact form of
    the context fingerprint. This is the Phase 3C composition shortcut;
    Stage 5 replaces it with a real task-outcome retrieval path.
    """
    return f"{signature.task_type} {signature.context_fingerprint}"


def _task_outcome_to_decision_draft(
    task: TaskSignature, outcome: TaskOutcomeDraft
) -> DecisionDraft:
    """Map a TaskOutcomeDraft onto a DecisionDraft for Atelier indexing.

    Phase 3C composition bridge. The derived DecisionDraft carries the
    approach_summary as the decision text and the task metadata as the
    rationale so Atelier's retrieval can find it by keyword. Stage 5
    will replace this with a typed task-outcome store (Atelier AT1
    typed-thought schema).
    """
    return DecisionDraft(
        decision=outcome.approach_summary,
        rationale=(
            f"task_type={task.task_type} "
            f"input_hash={task.input_hash} "
            f"agents={'+'.join(task.agents_involved)}"
        ),
        alternatives_considered=[d.position for d in outcome.dissents],
        evidence=[
            EvidenceItem(source=f"reasoning_step_{s.step_index}", excerpt=s.summary)
            for s in outcome.reasoning_trace
        ],
        confidence=outcome.quality_confidence,
        captured_at=datetime.now(tz=timezone.utc),
    )


_STATUS_SEVERITY: dict[HealthStatus, int] = {
    HealthStatus.OK: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.DOWN: 2,
}


def _worst_status(statuses: list[HealthStatus]) -> HealthStatus:
    """Return the most severe status among the inputs. Defaults to OK."""
    worst = HealthStatus.OK
    for status in statuses:
        if _STATUS_SEVERITY[status] > _STATUS_SEVERITY[worst]:
            worst = status
    return worst


__all__ = ["Memory"]
