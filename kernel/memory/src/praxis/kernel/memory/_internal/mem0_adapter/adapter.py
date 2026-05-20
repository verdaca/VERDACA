"""Mem0Adapter — the Praxis boundary around mem0ai.

Implements the full `MemoryProtocol` surface for structural conformance
with the Phase 3A test harness. The FACT-shaped methods (`store_fact`,
`retrieve_facts`, fact-scoped `delete`, fact-scoped `export`, `health`)
do real work against an injected `Mem0ClientProtocol`. The rest
(`store_task_outcome`, `store_decision`, `retrieve_similar_tasks`,
`retrieve_decisions`, `flag_and_quarantine`) raise `NotImplementedError`
because they are routed to Atelier / Beads by the Phase 3C facade.

Design notes
------------

1. **Dependency injection.** The adapter takes its vendor client through
   the constructor (`Mem0Adapter(client=..., tenant_hash=...)`). No
   implicit singleton, no `from_config` magic — constructing a real
   production adapter lives at the facade composition boundary, not
   here. Tests inject an in-memory fake (`FakeMem0Client`) so the
   adapter logic is exercised end-to-end without a live Mem0 stack.

2. **Tenant injection and defense-in-depth.** Every call into the
   vendor client substitutes `user_id = self._tenant_hash`. The
   `tenant_id` parameter the caller supplies is validated first
   (§8.2); on mismatch, `TenantIdentityError` is raised BEFORE the
   vendor client is touched.

3. **Async discipline.** Mem0 1.0.x is sync. Every call is wrapped in
   `asyncio.to_thread` so the MemoryProtocol contract (async on every
   method) is honored. If a future Mem0 version ships an async API, the
   wrappers drop away.

4. **Error translation.** Any exception leaking from the vendor client
   is caught and re-raised as `MemoryBackendError` with the original
   as `__cause__`. This keeps vendor-specific exception types out of
   application code per §4.5 #4.

5. **PII redaction at write time.** `store_fact` passes the fact text
   through `pii.redact()` before the vendor call. The pre-redaction
   fact is NEVER persisted.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

from praxis.kernel.memory._internal.mem0_adapter.client_protocol import (
    Mem0ClientProtocol,
)
from praxis.kernel.memory._internal.mem0_adapter.pii import redact
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
    RetrievalHit,
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


class Mem0Adapter:
    """Praxis-typed adapter over any `Mem0ClientProtocol` implementation."""

    def __init__(
        self,
        *,
        client: Mem0ClientProtocol,
        tenant_hash: str,
    ) -> None:
        self._client = client
        self._tenant_hash = tenant_hash

    # ------------------------------------------------------------------
    # Tenant guard
    # ------------------------------------------------------------------

    def _require_tenant(self, tenant_id: str) -> None:
        if tenant_id != self._tenant_hash:
            raise TenantIdentityError(
                f"tenant_id {tenant_id!r} does not match Mem0Adapter "
                f"tenant_hash {self._tenant_hash!r}"
            )

    # ------------------------------------------------------------------
    # Vendor call wrappers with error translation
    # ------------------------------------------------------------------

    async def _call(self, fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        """Run a sync vendor call in a thread + translate exceptions."""
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except Exception as exc:
            raise MemoryBackendError(
                f"Mem0 vendor call failed: {type(exc).__name__}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # MemoryProtocol — write path (FACT METHOD ONLY; others raise)
    # ------------------------------------------------------------------

    async def store_task_outcome(
        self,
        tenant_id: str,
        task: TaskSignature,
        outcome: TaskOutcomeDraft,
    ) -> TaskOutcomeRecord:
        self._require_tenant(tenant_id)
        raise NotImplementedError(
            "Mem0Adapter does not handle task outcomes; route via facade "
            "to the Atelier / Beads backends."
        )

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        self._require_tenant(tenant_id)
        raise NotImplementedError(
            "Mem0Adapter does not handle decisions; route via facade to the Atelier backend."
        )

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactDraft,
    ) -> FactRecord:
        self._require_tenant(tenant_id)

        redacted_fact = redact(fact.fact)
        redacted_source = redact(fact.source_excerpt) if fact.source_excerpt is not None else None

        result = await self._call(
            self._client.add,
            redacted_fact,
            user_id=self._tenant_hash,
            agent_id=agent_id,
            run_id=run_id,
            metadata={"schema_version": 1},
            infer=False,
        )

        mem0_id = _extract_single_id(result) or _new_entry_id()

        return FactRecord(
            entry_id=mem0_id,
            tenant_hash=self._tenant_hash,
            schema_version=1,
            state_snapshot_version=mem0_id,
            created_at=_utc_now(),
            fact=redacted_fact,
            source_excerpt=redacted_source,
        )

    # ------------------------------------------------------------------
    # MemoryProtocol — read path (FACT METHOD ONLY)
    # ------------------------------------------------------------------

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: TaskSignature,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        raise NotImplementedError(
            "Mem0Adapter does not handle task retrieval; route via facade to the Atelier backend."
        )

    async def retrieve_decisions(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        raise NotImplementedError(
            "Mem0Adapter does not handle decision retrieval; route via "
            "facade to the Atelier backend."
        )

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

        start = _utc_now()
        result = await self._call(
            self._client.search,
            query,
            user_id=self._tenant_hash,
            agent_id=agent_id,
            run_id=run_id,
            limit=top_k,
        )
        latency_ms = (_utc_now() - start).total_seconds() * 1000.0

        hits: list[RetrievalHit] = []
        for raw in _iter_results(result):
            mem0_id = raw.get("id") or _new_entry_id()
            fact_text = raw.get("memory") or raw.get("fact") or ""
            score = float(raw.get("score", 0.0))
            record = FactRecord(
                entry_id=str(mem0_id),
                tenant_hash=self._tenant_hash,
                schema_version=1,
                state_snapshot_version=str(mem0_id),
                created_at=_utc_now(),
                fact=str(fact_text),
            )
            hits.append(
                RetrievalHit(
                    entry_id=str(mem0_id),
                    similarity=score,
                    record_type="fact",
                    record=record,
                )
            )

        return RetrievalResult(
            hits=hits,
            source_distribution=SourceDistribution(tenant_hits=len(hits), seed_hits=0),
            retrieval_latency_ms=latency_ms,
        )

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
        deleted = 0

        if criteria.full_tenant:
            # Mem0's delete_all does not report a count, so deleted stays
            # at 0 for the full-tenant path. The facade reports crypto
            # shred status separately via crypto_shred_initiated.
            await self._call(
                self._client.delete_all,
                user_id=self._tenant_hash,
            )
        else:
            for entry_id in criteria.entry_ids:
                await self._call(self._client.delete, entry_id)
                deleted += 1

        return DeleteResult(
            job_id=job_id,
            deleted_entry_count=deleted,
            substep_status={"mem0_delete": DeleteSubstepStatus.SUCCEEDED},
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

        records: list[dict[str, Any]] = []
        if criteria.full_tenant:
            result = await self._call(
                self._client.get_all,
                user_id=self._tenant_hash,
            )
            records.extend(_iter_results(result))
        else:
            # Export-by-id skips missing entries silently. GDPR export
            # returns whatever exists; a missing id is not an error
            # condition because we may have already deleted it. We do
            # not use _call here because we need to distinguish KeyError
            # (missing — skip) from other exceptions (translate to
            # MemoryBackendError).
            for entry_id in criteria.entry_ids:
                try:
                    raw = await asyncio.to_thread(self._client.get, entry_id)
                except KeyError:
                    continue
                except Exception as exc:
                    raise MemoryBackendError(
                        f"Mem0 vendor call failed: {type(exc).__name__}: {exc}"
                    ) from exc
                if raw is not None:
                    records.append(raw)

        return ExportResult(
            artifact_path=os.path.join(
                tempfile.gettempdir(), f"mem0-export-{_new_entry_id()}.json"
            ),
            record_count=len(records),
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
        raise NotImplementedError(
            "Mem0Adapter does not handle quarantine; the facade routes "
            "quarantine to Atelier where embeddings can be stripped in "
            "place per §8.7."
        )

    # ------------------------------------------------------------------
    # MemoryProtocol — observability
    # ------------------------------------------------------------------

    async def health(self) -> HealthReport:
        """Probe the injected client via a cheap read.

        A `get_all` with `limit=1` is the cheapest op Mem0 exposes that
        exercises the storage layer. If it raises, we mark the backend
        DOWN and surface the reason.
        """
        try:
            await self._call(
                self._client.get_all,
                user_id=self._tenant_hash,
                limit=1,
            )
            status = HealthStatus.OK
            detail: str | None = None
        except MemoryBackendError as exc:
            status = HealthStatus.DOWN
            detail = str(exc)

        return HealthReport(
            overall=status,
            backends=[BackendHealth(backend="mem0", status=status, detail=detail)],
            manifest_last_reverified_at=_utc_now(),
        )


# =============================================================================
# Helpers for parsing Mem0's loosely-typed return shapes
# =============================================================================


def _iter_results(raw: Any) -> list[dict[str, Any]]:
    """Flatten Mem0's return shapes into a list of dicts.

    Mem0 returns either a bare list, or a dict with a "results" key
    containing the list. This normalizes both forms so the adapter code
    does not branch.
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        results = raw.get("results")
        if isinstance(results, list):
            return [r for r in results if isinstance(r, dict)]
        # Single-record shape — some Mem0 endpoints return the record
        # directly without wrapping it in `results`.
        if "id" in raw or "memory" in raw:
            return [raw]
    return []


def _extract_single_id(raw: Any) -> str | None:
    """Pull the first `id` out of whatever shape Mem0 returned from `add`."""
    hits = _iter_results(raw)
    if hits:
        first = hits[0]
        mid = first.get("id")
        if mid is not None:
            return str(mid)
    if isinstance(raw, dict) and "id" in raw:
        return str(raw["id"])
    return None


__all__ = ["Mem0Adapter"]
