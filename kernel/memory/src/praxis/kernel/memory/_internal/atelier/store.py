"""AtelierStore — decision memory backend (§5).

Phase 3B-iii minimum-viable implementation. Uses an in-memory dict for
storage (like BeadsStore Phase 3B-i) so the protocol logic is testable
without a live Postgres + pgvector stack. The Phase 3C facade composition
will swap in a real PostgresAtelierStore backed by the NR-SC-R2 engine;
only the storage layer changes, not the scoring or the protocol surface.

"Embeddings" in this store are naive word-sets. `similarity(a, b)` is
Jaccard over the word sets of the decision + rationale. This is NOT real
semantic search — it is deliberately transparent so property tests can
reason about it. Quinn's Step 3.4 will add pgvector integration tests
against a real embedding model.

Quarantine semantics (§8.7, Req #35, FM3.10 override)
------------------------------------------------------

`flag_and_quarantine` strips the embedding in place. In this store the
embedding IS the word set, so "stripping" means replacing it with an
empty frozenset. After quarantine:

  - `state` → QUARANTINED
  - `embedding` → empty (cannot be used for retrieval)
  - `state_weight` in scoring → 0.0 → retrieval score is zero regardless
    of other factors

The multiplicative scoring formula (§5.3) guarantees that quarantined
entries never surface in retrieval, even if Jaccard similarity somehow
equals 1.0 on a residual query. Property tests cover this.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock

from praxis.kernel.memory._internal.atelier.scoring import (
    STATE_WEIGHT_ACTIVE,
    STATE_WEIGHT_QUARANTINED,
    score_decision,
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
    MemoryRecordNotFound,
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


def _new_id() -> str:
    return uuid.uuid4().hex


_WORD_RE = re.compile(r"\w+")


def _tokenize(text: str) -> frozenset[str]:
    """Case-insensitive word set. Used as a naive 'embedding' stand-in."""
    return frozenset(w.lower() for w in _WORD_RE.findall(text))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Symmetric set-similarity in [0, 1]. Empty sets → 0.0."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union


class _AtelierEntryState(str, Enum):
    """Internal state machine for stored decisions."""

    ACTIVE = "active"
    QUARANTINED = "quarantined"


@dataclass
class _StoredDecision:
    """In-memory decision row — mirrors the §5.1 schema minus deferred fields."""

    entry_id: str
    tenant_hash: str
    draft: DecisionDraft
    embedding: frozenset[str]
    state: _AtelierEntryState = _AtelierEntryState.ACTIVE
    importance: float = 0.5  # author-assessed; default mirrors AT5 config
    created_at: datetime = field(default_factory=_utc_now)
    state_snapshot_version: str = field(default_factory=_new_id)
    reason_hash: str | None = None


class AtelierStore:
    """Minimum-viable Atelier decision store + MemoryProtocol surface."""

    def __init__(self, *, tenant_hash: str) -> None:
        self._tenant_hash = tenant_hash
        self._decisions: dict[str, _StoredDecision] = {}
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Tenant guard
    # ------------------------------------------------------------------

    def _require_tenant(self, tenant_id: str) -> None:
        if tenant_id != self._tenant_hash:
            raise TenantIdentityError(
                f"tenant_id {tenant_id!r} does not match AtelierStore "
                f"tenant_hash {self._tenant_hash!r}"
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _embed_draft(draft: DecisionDraft) -> frozenset[str]:
        """Compose the 'embedding' from the fields §5.3 scores against."""
        parts = [draft.decision, draft.rationale]
        for ev in draft.evidence:
            parts.append(ev.excerpt)
        return _tokenize(" ".join(parts))

    def _to_record(self, entry: _StoredDecision) -> DecisionRecord:
        return DecisionRecord(
            entry_id=entry.entry_id,
            tenant_hash=entry.tenant_hash,
            schema_version=1,
            state_snapshot_version=entry.state_snapshot_version,
            created_at=entry.created_at,
            decision=entry.draft.decision,
            rationale=entry.draft.rationale,
            alternatives_considered=entry.draft.alternatives_considered,
            evidence=entry.draft.evidence,
            confidence=entry.draft.confidence,
            outcome=entry.draft.outcome,
            captured_at=entry.draft.captured_at,
            ttl_days=entry.draft.ttl_days,
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
        raise NotImplementedError(
            "Phase 3B-iii AtelierStore is decision-shaped only; the "
            "Phase 3C facade routes task outcomes through a dedicated "
            "capture path that composes both Atelier and Beads."
        )

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        self._require_tenant(tenant_id)
        entry_id = _new_id()
        embedding = self._embed_draft(decision)

        entry = _StoredDecision(
            entry_id=entry_id,
            tenant_hash=self._tenant_hash,
            draft=decision,
            embedding=embedding,
        )

        def _insert() -> None:
            with self._lock:
                self._decisions[entry_id] = entry

        await asyncio.to_thread(_insert)
        return self._to_record(entry)

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactDraft,
    ) -> FactRecord:
        self._require_tenant(tenant_id)
        raise NotImplementedError("Facts are Mem0's territory — route via the facade.")

    # ------------------------------------------------------------------
    # MemoryProtocol — read path
    # ------------------------------------------------------------------

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: TaskSignature,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> RetrievalResult:
        self._require_tenant(tenant_id)
        raise NotImplementedError("Phase 3B-iii: retrieve_similar_tasks routes via facade.")

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

        query_embedding = _tokenize(query)
        start = _utc_now()

        def _compute() -> list[RetrievalHit]:
            with self._lock:
                entries = list(self._decisions.values())

            scored: list[tuple[float, _StoredDecision]] = []
            for entry in entries:
                sim = _jaccard(query_embedding, entry.embedding)
                state_weight = (
                    STATE_WEIGHT_ACTIVE
                    if entry.state is _AtelierEntryState.ACTIVE
                    else STATE_WEIGHT_QUARANTINED
                )
                score = score_decision(
                    semantic_similarity=sim,
                    state_weight=state_weight,
                    confidence=entry.draft.confidence,
                    importance=entry.importance,
                )
                if score > 0.0:
                    scored.append((score, entry))

            scored.sort(key=lambda pair: pair[0], reverse=True)
            hits: list[RetrievalHit] = []
            for score, entry in scored[:top_k]:
                hits.append(
                    RetrievalHit(
                        entry_id=entry.entry_id,
                        similarity=score,
                        record_type="decision",
                        record=self._to_record(entry),
                    )
                )
            return hits

        hits = await asyncio.to_thread(_compute)
        latency_ms = (_utc_now() - start).total_seconds() * 1000.0

        return RetrievalResult(
            hits=hits,
            source_distribution=SourceDistribution(tenant_hits=len(hits), seed_hits=0),
            retrieval_latency_ms=latency_ms,
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
        raise NotImplementedError("Facts are Mem0's territory — route via the facade.")

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

        def _delete_sync() -> int:
            with self._lock:
                if criteria.full_tenant:
                    removed = len(self._decisions)
                    self._decisions.clear()
                    return removed
                removed = 0
                for entry_id in criteria.entry_ids:
                    if self._decisions.pop(entry_id, None) is not None:
                        removed += 1
                return removed

        deleted = await asyncio.to_thread(_delete_sync)

        return DeleteResult(
            job_id=_new_id(),
            deleted_entry_count=deleted,
            substep_status={"atelier_decisions_delete": DeleteSubstepStatus.SUCCEEDED},
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

        def _collect() -> int:
            with self._lock:
                if criteria.full_tenant:
                    return len(self._decisions)
                return sum(1 for eid in criteria.entry_ids if eid in self._decisions)

        record_count = await asyncio.to_thread(_collect)

        return ExportResult(
            artifact_path=os.path.join(tempfile.gettempdir(), f"atelier-export-{_new_id()}.json"),
            record_count=record_count,
            access_token=_new_id(),
        )

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult:
        """§8.7 in-place quarantine with embedding strip (R-04 critical).

        Idempotent: re-quarantining an already-quarantined entry succeeds
        and produces a new state_snapshot_version. The unconditional
        replacement below is what makes this safe — quarantined state
        plus empty embedding end up identical on the second call.
        """
        self._require_tenant(tenant_id)

        def _quarantine_sync() -> tuple[str, str]:
            with self._lock:
                entry = self._decisions.get(entry_id)
                if entry is None:
                    raise MemoryRecordNotFound(entry_id)

                previous_version = entry.state_snapshot_version
                new_version = _new_id()
                reason_hash = _hash_reason(reason, free_text)

                replaced = _StoredDecision(
                    entry_id=entry.entry_id,
                    tenant_hash=entry.tenant_hash,
                    draft=entry.draft,
                    # Req #35 / FM3.10 override: embedding stripped in place.
                    embedding=frozenset(),
                    state=_AtelierEntryState.QUARANTINED,
                    importance=entry.importance,
                    created_at=entry.created_at,
                    state_snapshot_version=new_version,
                    reason_hash=reason_hash,
                )
                self._decisions[entry_id] = replaced
                return previous_version, new_version

        previous, new = await asyncio.to_thread(_quarantine_sync)

        return QuarantineResult(
            entry_id=entry_id,
            previous_state_snapshot_version=previous,
            new_state_snapshot_version=new,
            embedding_stripped=True,
        )

    # ------------------------------------------------------------------
    # MemoryProtocol — observability
    # ------------------------------------------------------------------

    async def health(self) -> HealthReport:
        return HealthReport(
            overall=HealthStatus.OK,
            backends=[
                BackendHealth(
                    backend="atelier",
                    status=HealthStatus.OK,
                    detail=f"decisions={len(self._decisions)}",
                )
            ],
            manifest_last_reverified_at=_utc_now(),
        )

    # ------------------------------------------------------------------
    # Test-only introspection
    # ------------------------------------------------------------------

    def _debug_get_entry(self, entry_id: str) -> _StoredDecision | None:
        return self._decisions.get(entry_id)


def _hash_reason(reason: QuarantineReason, free_text: str | None) -> str:
    payload = f"{reason.value}|{free_text or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["AtelierStore"]
