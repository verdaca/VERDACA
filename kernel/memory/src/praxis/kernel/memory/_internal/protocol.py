"""MemoryProtocol — the abstract contract all Memory backends implement.

This module is the SINGLE source of truth for the Memory layer's public shape.
Both the public facade (`praxis.kernel.memory.Memory` in Phase 3C) and every
private backend (Beads / Mem0 adapter / Atelier in Phase 3B) are measured
against this contract.

Design notes
------------

1.  **Location.** Protocol lives under `_internal/` because application code
    should never import or reference it by name — applications only touch the
    concrete `Memory` class from the public facade. Backends and the facade
    both import `MemoryProtocol` from here. This avoids a circular import
    between facade and backends.

2.  **Runtime-checkable.** Decorated with `@runtime_checkable` so the
    conformance test harness can use `isinstance(backend, MemoryProtocol)`
    for a coarse shape check, supplemented by `inspect.signature` for
    per-method signature verification.

3.  **Structural vs nominal.** Backends do NOT need to inherit from
    MemoryProtocol — duck typing is sufficient. The conformance test harness
    is the source of truth, not a class hierarchy. This keeps backends
    independent: a Beads store can be developed without importing anything
    from `_internal/protocol.py`.

4.  **Async.** Every method is `async`. Architecture §2.1 commits the Memory
    layer to asyncio. Backends that wrap sync libraries (SQLAlchemy core,
    Mem0 sync API) MUST wrap their sync calls in `asyncio.to_thread` or the
    equivalent — the protocol boundary is always awaitable.

5.  **Privacy invariant on every method.** Every method takes `tenant_id` as
    its first non-`self` parameter. The facade implementation compares it
    against `DeploymentManifest.tenant_id` before dispatching to backends
    (§8.2). Backends MAY trust that the tenant_id they receive has already
    been validated by the facade — but MUST still use it when scoping
    backend-native calls (Beads worktree path, Mem0 `user_id`, Atelier
    `tenant_hash` column). Defense in depth.

6.  **Errors.** Every method may raise:

    - `TenantIdentityError` (subclass of PermissionError) — caller-passed
      tenant_id does not match manifest. Hard-fails the process per §8.2.
    - `MemoryBackendError` (subclass of RuntimeError) — backend-level
      operational failure. Application code decides whether to retry.
    - `MemoryRecordNotFound` (subclass of LookupError) — lookup-by-id
      targets a non-existent record.
    - `MemoryQuotaExceeded` (subclass of plain Exception) — per-tenant
      entry ceiling crossed. Raised ONLY on the hard ceiling (NR-Q2 =
      250K). Soft-ceiling crossings (100K) are telemetry events, not
      exceptions. Read methods never raise this; only the three `store_*`
      methods do.

    Method-specific errors are documented per method below.

7.  **Draft / Record pattern.** The three `store_*` methods take a Draft
    type (caller-constructable, semantic fields only) and return a Record
    type (all Draft fields plus persistence columns: entry_id, tenant_hash,
    created_at, state_snapshot_version, schema_version). Callers never
    construct a Record directly. See `praxis.kernel.memory.models` for the
    Core/Draft/Record class composition.

Out of scope for Phase 3A (A3.3.4):
  - No default implementations — this is a Protocol, not an ABC template.
  - No learning-loop surface — that is the Stage 5 MAC contract.
  - No `auto_capture_*` hooks — also Stage 5.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from praxis.kernel.memory.models import (
    DecisionDraft,
    DecisionRecord,
    DeleteCriteria,
    DeleteResult,
    ExportCriteria,
    ExportResult,
    FactDraft,
    FactRecord,
    HealthReport,
    QuarantineReason,
    QuarantineResult,
    RetrievalResult,
    TaskOutcomeDraft,
    TaskOutcomeRecord,
    TaskSignature,
)


@runtime_checkable
class MemoryProtocol(Protocol):
    """The unified Memory contract (§2.1).

    Every backend and the composed facade must satisfy this protocol. The
    conformance test harness in `tests/memory/test_protocol_contract.py`
    verifies method presence + signature for each registered fixture.
    """

    # ------------------------------------------------------------------ write

    async def store_task_outcome(
        self,
        tenant_id: str,
        task: TaskSignature,
        outcome: TaskOutcomeDraft,
    ) -> TaskOutcomeRecord:
        """Persist a completed task's outcome to the TENANT scope (§2.1, Req #12).

        Preconditions
        -------------
        - `tenant_id` must equal `DeploymentManifest.tenant_id` (facade checks).
        - `task` (TaskSignature) and `outcome` (TaskOutcomeDraft) are frozen
          Pydantic models; `models.py` enforces field validation.

        Postconditions
        --------------
        - A new `TaskOutcomeRecord` exists in the tenant-scoped backing store.
        - Returned record's `signature` equals the input `task`, and its
          outcome-core fields equal the input `outcome`.
        - `entry_id`, `tenant_hash`, `created_at`, `state_snapshot_version`
          are freshly stamped by the Memory layer.
        - Scope is always TENANT; there is no way to write to the seed corpus
          via this method (Req #13, Req #16).
        - A `TelemetryEvent(type="task_outcome_stored")` is emitted.
        - If soft entry-ceiling (NR-Q2 = 100K) is crossed: a warning-level
          telemetry event is emitted BUT the write succeeds.

        Errors
        ------
        - `TenantIdentityError` — tenant_id mismatch.
        - `MemoryBackendError` — underlying write failed.
        - `MemoryQuotaExceeded` — hard entry-ceiling (NR-Q2 = 250K) crossed;
          write is rejected with no partial application.
        """
        ...

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        """Capture an Atelier-style decision record (§5.1).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `decision.captured_at` is set; `ttl_days >= 0`.

        Postconditions
        --------------
        - `DecisionRecord` persisted with fresh `entry_id`, `tenant_hash`,
          `created_at`, `state_snapshot_version`.
        - Returned record's core fields equal the input `decision`.
        - `TelemetryEvent(type="decision_captured")` emitted.
        - Soft ceiling: warning telemetry, write succeeds (symmetric to
          `store_task_outcome`).

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `MemoryQuotaExceeded`.
        """
        ...

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactDraft,
    ) -> FactRecord:
        """Write a Mem0 fact under three-axis scoping (§2.1, §4.4).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `agent_id` is a known agent (validated by caller; facade does not
          re-validate against Stage 4 registry).
        - `run_id` is a ULID generated at workflow start.

        Postconditions
        --------------
        - Fact is ingested into the tenant-scoped Mem0 collection with
          `user_id=manifest.tenant_hash`, `agent_id=agent_id`, `run_id=run_id`.
        - Returned `FactRecord` has fresh persistence columns.
        - PII pre-redaction has been applied (Req #18).
        - Cost event emitted: `CostEvent(type="record_created",
          component="memory.mem0.fact_extraction")` (§4.4).
        - Soft ceiling: warning telemetry, write succeeds.

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `MemoryQuotaExceeded`.
        """
        ...

    # ------------------------------------------------------------------ read

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: TaskSignature,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> RetrievalResult:
        """Cross-session retrieval of similar prior tasks (§2.1, Req #22, #57).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `top_k >= 1`, `0.0 <= min_similarity <= 1.0`.

        Postconditions
        --------------
        - Returns at most `top_k` hits, each with `similarity >= min_similarity`.
        - `source_distribution.tenant_hits + source_distribution.seed_hits`
          equals `len(hits)` — every hit is attributed (Req #22).
        - A `TelemetryEvent(type="retrieval_completed")` is emitted with
          allowlisted fields only (§8.4): NO query content, NO result IDs,
          NO embeddings.
        - A `CostEvent(type="retrieval_cache_hit")` is emitted iff the
          retrieval used a warm cache (Req #57).

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`.
        - `ValueError` if `top_k < 1` or `min_similarity` outside [0, 1].
        """
        ...

    async def retrieve_decisions(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Semantic retrieval over captured decisions (§5.3).

        Preconditions
        -------------
        - `tenant_id` matches manifest; `top_k >= 1`.
        - `query` is non-empty after strip.

        Postconditions
        --------------
        - Returns at most `top_k` hits.
        - Results are scored by the §5.3 five-factor function
          (semantic × recency × confidence × state × importance).
        - QUARANTINED and EXPIRED states contribute zero score and are
          therefore absent from the result set.
        - Telemetry: `retrieval_completed` (allowlisted fields only).

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `ValueError`.
        """
        ...

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Semantic retrieval over Mem0 facts scoped to a run (§2.1, §4.3).

        Preconditions
        -------------
        - `tenant_id` matches manifest; `top_k >= 1`.
        - `(agent_id, run_id)` are the Mem0 three-axis scope within the tenant.

        Postconditions
        --------------
        - Returns at most `top_k` hits, each scoped to the given
          `(tenant_id, agent_id, run_id)` triple.
        - No cross-tenant or cross-run leakage possible via this method
          (Mem0 collection + three-axis scoping).
        - Telemetry: `retrieval_completed`.

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `ValueError`.
        """
        ...

    # ------------------------------------------------------------------ GDPR

    async def delete(
        self,
        tenant_id: str,
        criteria: DeleteCriteria,
    ) -> DeleteResult:
        """Right-to-erasure cascade across all backends (§8.5, Req #24–#35).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `criteria` is well-formed (at least one of `entry_ids` non-empty or
          `full_tenant=True`).

        Postconditions
        --------------
        - A durable `memory_jobs` row was created and checkpointed through
          each substep listed in §8.5.
        - Method returns ONLY after all substeps report `SUCCEEDED`
          (Req #25). Synchronous embedding purge is complete (Req #34).
        - Cache-invalidation pub/sub acks have been aggregated before return
          (Req #27).
        - Post-delete verification query returns zero hits (Req #26).
        - A salted-hash audit log entry exists with the criteria hash, NOT
          the raw criteria (Req #33).
        - If `full_tenant=True`: `crypto_shred_initiated=True` in the result,
          per-tenant backup key destruction job has been started
          (completes async within 7 days per NR-C-A1).

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`.
        - `ValueError` if `criteria` specifies neither entry_ids nor full_tenant.
        """
        ...

    async def export(
        self,
        tenant_id: str,
        criteria: ExportCriteria,
    ) -> ExportResult:
        """GDPR Article 15 right-to-access export (§8.6, Req #37).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `criteria` is well-formed (symmetric to DeleteCriteria).

        Postconditions
        --------------
        - An artifact file exists at `ExportResult.artifact_path` containing
          all matching records.
        - The artifact is in the tenant-local artifact store with an access
          token (Req #32).
        - Two-tenant isolation test (§8.6, Req #37) passes — the artifact
          contains ONLY the requesting tenant's data.
        - Telemetry: `export_completed`.

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `ValueError`.
        """
        ...

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult:
        """In-place quarantine with embedding strip (§8.7, Req #35, FM3.10).

        Preconditions
        -------------
        - `tenant_id` matches manifest.
        - `entry_id` references an existing non-quarantined record.

        Postconditions
        --------------
        - Target record's state is QUARANTINED.
        - Target record's embedding column is NULL (in-place strip — the
          FM3.10 override of Round 1's state-only treatment).
        - `QuarantineResult.embedding_stripped` is True.
        - A new `state_snapshot_version` is stamped; the previous version
          is returned for replay.
        - A salted-hash audit log entry records the quarantine (Req #33,
          §8.7) with PII-scrubbed free_text.
        - A quarantine-operation bead is appended to the Beads audit trail
          (§8.7).
        - Cache invalidation pub/sub fired (Req #50).

        Errors
        ------
        - `TenantIdentityError`, `MemoryBackendError`, `MemoryRecordNotFound`.
        """
        ...

    # ----------------------------------------------------------- observability

    async def health(self) -> HealthReport:
        """Process-wide operational health check (§2.1).

        Intentionally has NO `tenant_id` parameter. Health is a property
        of the Memory process (pool liveness, backend reachability,
        manifest freshness), NOT of any individual tenant's data. Called
        by load balancers, k8s liveness probes, and monitoring without
        tenant context. Forcing a tenant_id here would be semantically
        wrong — there is no "health of tenant X" under managed
        single-tenant because the tenant boundary IS the process boundary.

        Preconditions
        -------------
        - None beyond normal facade initialization.

        Postconditions
        --------------
        - Returns a `HealthReport` with per-backend status and an overall
          roll-up.
        - Does NOT emit telemetry (health checks are probed by ops
          infrastructure and would drown the telemetry channel).

        Errors
        ------
        - Never raises. A backend failure is reported as `HealthStatus.DOWN`
          in the relevant `BackendHealth` entry, not as an exception.
        """
        ...


__all__ = ["MemoryProtocol"]
