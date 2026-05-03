"""Mem0 adapter — Memory port implementation.

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3): primary adapter in the
dual-adapter Memory port pair. Wraps `mem0ai` PyPI SDK 1.0.11 behind
`MemoryPort`. Letta secondary adapter at `adapters/letta/` (Phase B.2)
provides substitute-readiness per `port-contracts.md` v0.2.1 §3
substitute-readiness clause.

Authority caveat (Option D-refined per project_verdaca_stage9_4_3): the
spec docs `port-contracts.md` v0.2.1 + `ports-architecture.md` v0.3 live
in `_bmad-output/implementation-artifacts/verdaca/stage9/` which is
gitignored. The canonical substance for ADR-1 §3.6 DTO field shapes is
the commit body of `f843d44` (corrigendum) + `4b0a829` (port-file
convergence); local working surface is secondary. Sectional cites used
throughout per V8 Approach b discipline.

Substrate composition (per Mem0 SDK survey 2026-05-02 §4 + N3-a-rev probe):
    store          — `Memory.add(messages, metadata=..., user_id=..., infer=False)`
                     marshals MemoryEntry into chat-format message; round-trips
                     all 4 MemoryEntry fields via metadata (verdaca.* keys)
                     per advisor prior #1 lossless round-trip
    query          — `Memory.search(query, limit=..., user_id=...)`; AP-3
                     tier normalization adapter-side; AP-9 confidence-clamp
                     adapter-side; primary path (a) `confidence = hit["score"]`
                     when score is exposed by Mem0 (per N2 finding)
    promote        — adapter-synthesized via read-merge-update on Mem0
                     metadata (N3-a-rev: `update(memory_id, data=existing_content,
                     metadata=merged_metadata)`); PS-1 threshold check raises
                     PromotionContractViolation BEFORE any upstream call
    revoke_promotion — adapter-synthesized via search-by-promotion_id +
                     read-merge-update; natural-key dedup per Q-B1-Sub-1
                     (signature has no `idempotency_key` parameter); PS-4
                     SLO contract surfaced as PromotionRevocationFailed
    migrate        — adapter-internal migrator registry (Q-MIGRATE-1 = M.1;
                     no Protocol-level migrator parameter); per-entry
                     read-merge-update with schema_version bump

AP obligations (per `port-contracts.md` v0.2.1 §7 Hand-off Hooks → Amelia
9.4.3 paragraph; AP names per `ports-architecture.md` v0.3 §2.3 table):
    AP-3 TierNormalizer        — `_normalize_tier()`; query + promote
    AP-4 ThresholdGuard        — inline PS-1 check at promote() top
    AP-5 TwoPhaseIdempotencyCommit — `_idempotency_dedup()` +
                                  `_idempotency_write_intent()` +
                                  `_idempotency_write_success()` +
                                  `_reconcile_idempotency_cache()` at on_init
    AP-6 SpanAttributeContract — `_emit_promote_span()` (5 canonical attrs;
                                  PS-3 set-equality verbatim);
                                  `_emit_revoke_span()` (3-attribute mirror
                                  per Q-B1-Sub-6); `_emit_degraded_signal_span()`
                                  (adapter-private per Q-B3-4, rare-path)
    AP-7 OpaqueIDWrapper       — `uuid.uuid4().hex` for promotion_id at promote()
    AP-9 ConfidenceScaleNormalizer — inline `max(0.0, min(1.0, confidence))`
                                  clamp at query()

Idempotency profile (per `port-contracts.md` v0.2.1 §3 idempotency table):
    store              — sync, idempotent (idempotency_key required)
    query              — sync, idempotent (sequence return; no key)
    promote            — sync, idempotent (idempotency_key required from rationale)
    revoke_promotion   — sync, idempotent (natural-key dedup per Q-B1-Sub-1)
    migrate            — sync (long-running OK), NOT idempotent (single-fire
                         per version pair; no AP-5 dedup)

PS-2 v0.2 durability (per `port-contracts.md` v0.2.1 §3.4 PS-2): in-memory
caches are non-conformant absent reconciliation. This adapter ships
Q-B1-22 disposition (i'): in-process dict cache rehydrated at on_init by
reading INTENT/SUCCESS records from Mem0 sidecar metadata. AP-5
TwoPhaseIdempotencyCommit pattern verbatim per PS-2 wording.

OTEL span discipline (per `port-contracts.md` v0.2.1 §3.4 PS-3 + F-004):
    promote span name        — `verdaca.port.memory.promote`
                               5 canonical attributes EXACTLY (set-equality)
    revoke_promotion span    — `verdaca.port.memory.revoke_promotion`
                               3-attribute mirror per Q-B1-Sub-6
    confidence_synthesis span — `verdaca.port.memory.confidence_synthesis`
                               adapter-private; emitted ONLY on degraded-signal
                               query path (synthesis="default-1.0" per Q-B3-4)
    F-004 SpanRelabeler      — zero `mem0.*` upstream-native span names leak
                               past adapter boundary

Error specializations (per `port-contracts.md` v0.2.1 §3.4):
    PromotionContractViolation — PS-1 threshold violation at promote()
    PromotionRevocationFailed  — PS-4 SLO violation at revoke_promotion()
    ContractViolation          — DTO/tier-normalization invariant violation
    IdempotencyViolation       — AP-5 payload-equivalence mismatch (Q-B1-Sub-9)
    UpstreamUnavailable        — Mem0 liveness probe failure at on_init()

Deprecation policy: see `ports-architecture.md` v0.3 §6 for `API_VERSION` /
`schema_version` bump rules.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar

from mem0 import Memory
from opentelemetry import trace

from praxis.ports.common import (
    ContractViolation,
    IdempotencyViolation,
    UpstreamUnavailable,
)
from praxis.ports.memory import (
    MemoryEntry,
    MemoryHit,
    MemoryPort,
    MemoryQuery,
    MigrationReport,
    PromotedMemory,
    PromotionContractViolation,
    PromotionRationale,
    PromotionRevocationFailed,
    PromotionTier,
    RevokedPromotion,
    StoredMemory,
)

from praxis.adapters.mem0.version_pin import UPSTREAM_NAME

_PORT_NAME = "memory"

# User-id partitioning per Q-B1-Sub-10 (Sub-3 fallback engaged).
_VERDACA_USER_ID = "verdaca.system.user"
_VERDACA_SIDECAR_USER_ID = "verdaca.system.idempotency"

# Mem0 metadata key namespace (dot-form per Q-B1-Sub-5 PASS).
_TIER_KEY = "verdaca.tier"
_PROMOTION_ID_KEY = "verdaca.promotion_id"
_PROMOTION_RATIONALE_KEY = "verdaca.promotion_rationale"
_CONFIDENCE_KEY = "verdaca.confidence"
_SOURCE_SPAN_ID_KEY = "verdaca.source_span_id"
_SCHEMA_VERSION_KEY = "verdaca.schema_version"
_CORRELATION_ID_KEY = "verdaca.correlation_id"

# Idempotency-sidecar metadata schema (Q-B1-22 (i') + Q-B1-Sub-9).
_IDEMPOTENCY_KIND_KEY = "verdaca.idempotency.kind"
_IDEMPOTENCY_OPERATION_KEY = "verdaca.idempotency.operation"
_IDEMPOTENCY_KEY_KEY = "verdaca.idempotency.key"
_IDEMPOTENCY_RESULT_DTO_KEY = "verdaca.idempotency.result_dto"
_IDEMPOTENCY_PAYLOAD_HASH_KEY = "verdaca.idempotency.payload_hash"
_IDEMPOTENCY_PRIOR_CALL_AT_KEY = "verdaca.idempotency.prior_call_at"

_tracer = trace.get_tracer(__name__)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _canonicalize(value: Any) -> Any:
    """Make a value JSON-serializable canonically for AP-5 payload-hash."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "value") and not isinstance(value, (str, int, float, bool)):
        return value.value
    if isinstance(value, dict):
        return {k: _canonicalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v) for v in value]
    return value


def _compute_payload_hash(operation: str, *fields: Any) -> str:
    """Canonical sha256 over (operation, *fields) for AP-5 payload-equivalence
    per Q-B1-Sub-9.
    """
    canonical = json.dumps(
        {"operation": operation, "fields": [_canonicalize(f) for f in fields]},
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _migrator_signature(migrator: Callable[[dict], dict]) -> str:
    """Stable hash of a migrator's source for `MigrationReport.migrator_signature`.

    Sibling pattern: `BeadsAdapter._migrator_signature` at
    `adapters/beads/src/praxis/adapters/beads/adapter.py:56-66`.
    `inspect.getsource()` with `repr()` fallback for built-ins / lambdas
    without source / C-extension callables.
    """
    try:
        source = inspect.getsource(migrator)
    except (OSError, TypeError):
        source = repr(migrator)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    """In-process AP-5 cache entry per Q-B1-Sub-9 payload-equivalence.

    `payload_hash` enables `IdempotencyViolation` raise on key-reuse with
    non-equivalent payload (per `common.py` IdempotencyViolation contract).
    `prior_call_at` carries the datetime needed for the violation DTO.
    """

    payload_hash: str
    prior_call_at: datetime
    dto: object


class Mem0Adapter:
    """In-tree PyPI-pinned wrap of `mem0ai` SDK against `MemoryPort`.

    Conforms to `praxis.ports.memory.MemoryPort` (verify via
    `isinstance(adapter, MemoryPort)`; the Protocol is `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the attribute,
    # isinstance checks the candidate has it. Per 9.4.1 API_VERSION ClassVar
    # bug lesson (executor playbook §9.C addendum).
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        mem0_client: Memory,
        user_id: str = _VERDACA_USER_ID,
        migrators: dict[tuple[int, int], Callable[[dict], dict]] | None = None,
        default_correlation_id: str | None = None,
    ) -> None:
        """Construct an adapter.

        `mem0_client` is the caller-constructed Mem0 `Memory` instance per
        Q-B1-1 caller-DI disposition. Mem0 lifecycle (embedder, LLM, vector
        store, auth) is the caller's responsibility. See `changelog.md` for
        the two caller-config constraints (vector dim alignment, infer=False
        sidecar mode).

        `user_id` partitions the user-memory corpus per Q-B1-Sub-10. Default
        `_VERDACA_USER_ID` is stable across all caller correlation_ids; caller
        threads per-call correlation through Mem0 metadata as
        `verdaca.correlation_id` key, NOT as user_id (preserves cross-session
        retrieval).

        `migrators` is the M.1 adapter-internal migrator registry per
        Q-MIGRATE-1 disposition + Q-B1-Sub-7. Maps `(from_version, to_version)
        → Callable[[dict], dict]`. Empty default at v0.1.0 (no schema-version
        migrations needed at first ship).

        `default_correlation_id` per BeadsAdapter:82-95 / TONLAdapter:77-101
        precedent.
        """
        self._mem0 = mem0_client
        self._user_id = user_id
        self._migrator_registry: dict[tuple[int, int], Callable[[dict], dict]] = (
            migrators or {}
        )
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        # Q-B1-22 (i'): in-process dict cache; rehydrated at on_init from
        # Mem0 sidecar metadata per AP-5 reconciliation.
        self._idempotency_cache: dict[tuple[str, str], _CacheEntry] = {}

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.3 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check + Mem0 liveness + AP-5 reconciliation.

        Sibling precedent: `BeadsAdapter:101-110`, `TONLAdapter:107-117` do
        NOT have upstream healthcheck (both substrates in-process). Mem0
        adapter is the FIRST adapter with upstream-network dependencies;
        `Memory.search()` against the sidecar-user_id partition serves as a
        lightweight liveness probe (raises on Mem0 init / connectivity
        failure; no API cost beyond a single embedded query).
        """
        if not isinstance(self, MemoryPort):
            raise RuntimeError("Mem0Adapter does not conform to MemoryPort")

        # Mem0 liveness probe.
        try:
            self._mem0.get_all(user_id=_VERDACA_SIDECAR_USER_ID)
        except Exception as exc:
            raise UpstreamUnavailable(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                last_known_health=_utc_now(),
            ) from exc

        # AP-5 reconciliation per Q-B1-22 (i').
        self._reconcile_idempotency_cache()

    def on_shutdown(self) -> None:
        """Lifecycle: Mem0 client cleanup if available.

        Mem0 v1.0.11 exposes `Memory.close()` per N3-a probe (12 public
        methods include `close`); call it if the caller's Mem0 instance
        supports it. No-op if not callable.
        """
        close = getattr(self._mem0, "close", None)
        if callable(close):
            close()

    # ------------------------------------------------------------------
    # MemoryPort surface (5 methods)
    # ------------------------------------------------------------------

    def store(self, entry: MemoryEntry) -> StoredMemory:
        """Per `port-contracts.md` v0.2.1 §3 store() spec + §3 idempotency
        table (idempotency_key REQUIRED).

        Marshaling per advisor prior #1 (lossless round-trip): wrap
        `entry.content` into `[{"role":"user","content":...}]` chat format;
        round-trip the other 3 MemoryEntry fields via Mem0 metadata
        (`verdaca.confidence`, `verdaca.source_span_id`, `verdaca.schema_version`).
        """
        if entry.idempotency_key is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=entry.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        payload_hash = _compute_payload_hash("store", entry)
        cached = self._idempotency_dedup("store", entry.idempotency_key, payload_hash)
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent(
            "store", entry.idempotency_key, payload_hash, entry.correlation_id
        )

        merged_metadata: dict[str, Any] = {
            **entry.metadata,
            _TIER_KEY: "working",
            _CONFIDENCE_KEY: entry.confidence,
            _SOURCE_SPAN_ID_KEY: entry.source_span_id,
            _SCHEMA_VERSION_KEY: entry.schema_version,
            _CORRELATION_ID_KEY: entry.correlation_id,
        }
        result = self._mem0.add(
            messages=[{"role": "user", "content": entry.content}],
            metadata=merged_metadata,
            user_id=self._user_id,
            infer=False,
        )
        stored_id = result["results"][0]["id"]  # N1: `id`, not `memory_id`

        stored = StoredMemory(
            schema_version=entry.schema_version,
            correlation_id=entry.correlation_id,
            idempotency_key=entry.idempotency_key,
            stored_id=stored_id,
        )
        now = _utc_now()
        self._idempotency_write_success(
            "store", entry.idempotency_key, payload_hash, now, stored
        )
        self._idempotency_cache[("store", entry.idempotency_key)] = _CacheEntry(
            payload_hash=payload_hash,
            prior_call_at=now,
            dto=stored,
        )
        return stored

    def query(self, q: MemoryQuery) -> Sequence[MemoryHit]:
        """Per `port-contracts.md` v0.2.1 §3 query() spec + §3 idempotency
        table (idempotent, sequence return).

        AP-3 TierNormalizer per-hit; AP-9 ConfidenceScaleNormalizer clamp.
        Confidence-synthesis preference order per advisor prior #2 +
        N2 inversion: path (a) `hit["score"]` is primary (N2 verified Mem0
        v1.0.11 search returns `score` field with cosine similarity); path
        (c) default-1.0 + adapter-private span fires only when score absent
        (rare-path observability per Q-B3-4 disposition).
        """
        results = self._mem0.search(
            query=q.query_text,
            limit=q.k,
            user_id=self._user_id,
        )
        hits: list[MemoryHit] = []
        for hit in results.get("results", []):
            tier = self._normalize_tier(
                (hit.get("metadata") or {}).get(_TIER_KEY, "working"),
                correlation_id=q.correlation_id,
            )
            score = hit.get("score")
            if score is not None:
                confidence = float(score)
            else:
                confidence = 1.0
                self._emit_degraded_signal_span(
                    hit_id=hit["id"], synthesis="default-1.0"
                )
            # AP-9 ConfidenceScaleNormalizer belt-and-braces clamp.
            confidence = max(0.0, min(1.0, confidence))
            hits.append(
                MemoryHit(
                    schema_version=q.schema_version,
                    correlation_id=q.correlation_id,
                    idempotency_key=q.idempotency_key,
                    hit_id=hit["id"],  # N1: `id`, not `memory_id`
                    content=hit["memory"],
                    confidence=confidence,
                    tier=tier,
                )
            )
        return hits

    def promote(
        self,
        hit_id: str,
        target_tier: PromotionTier,
        rationale: PromotionRationale,
    ) -> PromotedMemory:
        """Per `port-contracts.md` v0.2.1 §3 promote() + §3.4 PS-1
        (confidence-threshold) + PS-3 (5-attribute OTEL span set-equality) +
        §3 idempotency table (idempotency_key REQUIRED from rationale).

        AP-4 ThresholdGuard runs BEFORE any upstream call per PS-1 verbatim
        ("The adapter MAY NOT silently lower the threshold..."). N3-a-rev
        read-merge-update pattern preserves Mem0 entry id stability
        (no delete+re-add).
        """
        # AP-4 ThresholdGuard (PS-1).
        if rationale.threshold_met < rationale.threshold_required:
            raise PromotionContractViolation(
                port_name=_PORT_NAME,
                correlation_id=rationale.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                requested_threshold=rationale.threshold_required,
                actual_confidence=rationale.threshold_met,
            )
        if rationale.idempotency_key is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=rationale.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        payload_hash = _compute_payload_hash("promote", hit_id, target_tier, rationale)
        cached = self._idempotency_dedup(
            "promote", rationale.idempotency_key, payload_hash
        )
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent(
            "promote", rationale.idempotency_key, payload_hash, rationale.correlation_id
        )

        # N3-a-rev (Q-B1-Sub-8): read existing → merge metadata → update.
        existing = self._mem0.get(memory_id=hit_id)
        existing_metadata = existing.get("metadata") or {}
        tier_from = self._normalize_tier(
            existing_metadata.get(_TIER_KEY, "working"),
            correlation_id=rationale.correlation_id,
        )
        promotion_id = uuid.uuid4().hex  # AP-7 OpaqueIDWrapper
        merged_metadata = {
            **existing_metadata,
            _TIER_KEY: target_tier.value,
            _PROMOTION_ID_KEY: promotion_id,
            _PROMOTION_RATIONALE_KEY: rationale.model_dump_json(),
        }
        self._mem0.update(
            memory_id=hit_id,
            data=existing["memory"],
            metadata=merged_metadata,
        )

        # AP-6 PS-3 5-attribute canonical span (set-equality verbatim).
        self._emit_promote_span(
            hit_id=hit_id,
            tier_from=tier_from,
            tier_to=target_tier.value,
            threshold_met=rationale.threshold_met,
            threshold_required=rationale.threshold_required,
        )

        promoted = PromotedMemory(
            schema_version=rationale.schema_version,
            correlation_id=rationale.correlation_id,
            idempotency_key=rationale.idempotency_key,
            promotion_id=promotion_id,
        )
        now = _utc_now()
        self._idempotency_write_success(
            "promote", rationale.idempotency_key, payload_hash, now, promoted
        )
        self._idempotency_cache[("promote", rationale.idempotency_key)] = _CacheEntry(
            payload_hash=payload_hash,
            prior_call_at=now,
            dto=promoted,
        )
        return promoted

    def revoke_promotion(self, promotion_id: str, reason: str) -> RevokedPromotion:
        """Per `port-contracts.md` v0.2.1 §3 revoke_promotion() + §3.4 PS-4
        (time-bounded SLO).

        Q-B1-Sub-1 natural-key dedup: signature has no `idempotency_key`;
        derive `dedup_key = sha256(f"{promotion_id}:{reason}")`. N3-a-rev
        read-merge-update strips promotion-marker keys + sets tier back to
        "working".
        """
        # Q-B1-Sub-1 natural-key dedup.
        dedup_key = hashlib.sha256(
            f"{promotion_id}:{reason}".encode("utf-8")
        ).hexdigest()
        payload_hash = _compute_payload_hash("revoke_promotion", promotion_id, reason)
        cached = self._idempotency_dedup("revoke_promotion", dedup_key, payload_hash)
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent(
            "revoke_promotion", dedup_key, payload_hash, self._default_correlation_id
        )

        # Locate by adapter-side filter loop. Mem0 v1.0.11 filter syntax for
        # nested-dotted metadata keys not verified at v0.1.0; adapter-side
        # filter is portable. O(n) scan; Stage 10 may optimize per changelog.
        results = self._mem0.search(query="", user_id=self._user_id)
        found: dict[str, Any] | None = None
        for r in results.get("results", []):
            if (r.get("metadata") or {}).get(_PROMOTION_ID_KEY) == promotion_id:
                found = r
                break
        if found is None:
            raise PromotionRevocationFailed(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                promotion_id=promotion_id,
            )

        existing_metadata = found.get("metadata") or {}
        tier_from = self._normalize_tier(
            existing_metadata.get(_TIER_KEY, "working"),
            correlation_id=self._default_correlation_id,
        )
        stripped_metadata: dict[str, Any] = {
            k: v
            for k, v in existing_metadata.items()
            if k not in (_PROMOTION_ID_KEY, _PROMOTION_RATIONALE_KEY)
        }
        stripped_metadata[_TIER_KEY] = "working"
        self._mem0.update(
            memory_id=found["id"],  # N1: `id`, not `memory_id`
            data=found["memory"],
            metadata=stripped_metadata,
        )

        # AP-6 3-attribute mirror per Q-B1-Sub-6 (PS-3 set-equality is
        # promote-specific; revoke emits subset).
        self._emit_revoke_span(
            hit_id=found["id"],
            tier_from=tier_from,
            tier_to="working",
        )

        revoked = RevokedPromotion(
            schema_version=1,
            correlation_id=self._default_correlation_id,
            idempotency_key=None,
            promotion_id=promotion_id,
            reason=reason,
        )
        now = _utc_now()
        self._idempotency_write_success(
            "revoke_promotion", dedup_key, payload_hash, now, revoked
        )
        self._idempotency_cache[("revoke_promotion", dedup_key)] = _CacheEntry(
            payload_hash=payload_hash,
            prior_call_at=now,
            dto=revoked,
        )
        return revoked

    def migrate(self, from_version: int, to_version: int) -> MigrationReport:
        """Per `port-contracts.md` v0.2.1 §3 migrate() — adapter-authored
        schema-version migration + §3 idempotency table (NOT idempotent;
        single-fire per version pair).

        Q-MIGRATE-1 = M.1: adapter-internal `_migrator_registry` lookup.
        No Protocol-level `migrator` parameter (no fresh corrigendum).
        N3-a-rev per-entry read-merge-update.

        Note: per ADR-1 §3.5 the AP-8 TwoWindowMigration playbook is for
        adapter SUBSTITUTION (Mem0 → Letta corpus migration). This method
        is within-adapter schema-version migration; AP-8 does not apply.
        """
        migrator = self._migrator_registry.get((from_version, to_version))
        if migrator is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )

        all_entries = self._mem0.get_all(user_id=self._user_id)
        candidates = [
            e
            for e in all_entries.get("results", [])
            if (e.get("metadata") or {}).get(_SCHEMA_VERSION_KEY) == from_version
        ]

        entries_migrated = 0
        for entry in candidates:
            migrated = migrator(entry)
            existing_metadata = entry.get("metadata") or {}
            merged_metadata: dict[str, Any] = {
                **existing_metadata,
                _SCHEMA_VERSION_KEY: to_version,
                **(migrated.get("metadata") or {}),
            }
            self._mem0.update(
                memory_id=entry["id"],  # N1: `id`, not `memory_id`
                data=migrated.get("memory", entry["memory"]),
                metadata=merged_metadata,
            )
            entries_migrated += 1

        return MigrationReport(
            schema_version=1,
            correlation_id=self._default_correlation_id,
            idempotency_key=None,
            from_version=from_version,
            to_version=to_version,
            entries_migrated=entries_migrated,
            migrator_signature=_migrator_signature(migrator),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_tier(
        self,
        raw: str,
        *,
        correlation_id: str,
    ) -> str:
        """AP-3 TierNormalizer.

        Per `ports/src/praxis/ports/memory.py:64-69` MemoryHit.tier Literal +
        ADR-1 §3 v0.2 tier-normalization clause: unmapped upstream tiers
        raise `ContractViolation` at adapter boundary.
        """
        if raw not in {"working", "session", "promoted"}:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        return raw

    def _idempotency_dedup(
        self,
        operation: str,
        key: str,
        payload_hash: str,
    ) -> object | None:
        """AP-5 dedup with payload-equivalence check per Q-B1-Sub-9.

        Returns cached DTO if `(op, key)` cached AND `payload_hash` matches.
        Returns `None` if `(op, key)` not cached. Raises `IdempotencyViolation`
        if `(op, key)` cached but `payload_hash` mismatch (per `common.py`
        IdempotencyViolation contract: "Idempotency key was reused with
        non-equivalent payload. Indicates caller bug OR replay-storm.
        Adapter MUST NOT retry; caller MUST reconcile.").
        """
        cached = self._idempotency_cache.get((operation, key))
        if cached is None:
            return None
        if cached.payload_hash != payload_hash:
            raise IdempotencyViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                idempotency_key=key,
                prior_call_at=cached.prior_call_at,
            )
        return cached.dto

    def _idempotency_write_intent(
        self,
        operation: str,
        key: str,
        payload_hash: str,
        input_correlation_id: str,
    ) -> None:
        """AP-5 INTENT sidecar write per Q-B1-22 (i') + Q-B1-Sub-9.

        Persists `(operation, key, payload_hash, input_correlation_id)` to
        Mem0 sidecar partition (user_id=`_VERDACA_SIDECAR_USER_ID`) so
        on_init reconciliation can detect INTENT-without-SUCCESS state and
        ROLLBACK per Q-B1-Sub-2 disposition.
        """
        self._mem0.add(
            messages=[
                {
                    "role": "user",
                    "content": f"[verdaca.idempotency.intent] {operation} {key}",
                }
            ],
            metadata={
                _IDEMPOTENCY_KIND_KEY: "intent",
                _IDEMPOTENCY_OPERATION_KEY: operation,
                _IDEMPOTENCY_KEY_KEY: key,
                _IDEMPOTENCY_PAYLOAD_HASH_KEY: payload_hash,
                _CORRELATION_ID_KEY: input_correlation_id,
            },
            user_id=_VERDACA_SIDECAR_USER_ID,
            infer=False,
        )

    def _idempotency_write_success(
        self,
        operation: str,
        key: str,
        payload_hash: str,
        prior_call_at: datetime,
        result_dto: object,
    ) -> None:
        """AP-5 SUCCESS sidecar write per Q-B1-22 (i') + Q-B1-Sub-9.

        Persists `(operation, key, payload_hash, prior_call_at, result_dto)`
        so on_init reconciliation can rehydrate `_idempotency_cache` with
        full payload-equivalence + IdempotencyViolation support.
        """
        result_dto_json = (
            result_dto.model_dump_json()
            if hasattr(result_dto, "model_dump_json")
            else json.dumps(_canonicalize(result_dto))
        )
        self._mem0.add(
            messages=[
                {
                    "role": "user",
                    "content": f"[verdaca.idempotency.success] {operation} {key}",
                }
            ],
            metadata={
                _IDEMPOTENCY_KIND_KEY: "success",
                _IDEMPOTENCY_OPERATION_KEY: operation,
                _IDEMPOTENCY_KEY_KEY: key,
                _IDEMPOTENCY_RESULT_DTO_KEY: result_dto_json,
                _IDEMPOTENCY_PAYLOAD_HASH_KEY: payload_hash,
                _IDEMPOTENCY_PRIOR_CALL_AT_KEY: prior_call_at.isoformat(),
            },
            user_id=_VERDACA_SIDECAR_USER_ID,
            infer=False,
        )

    def _reconcile_idempotency_cache(self) -> None:
        """AP-5 reconciliation per Q-B1-22 (i') + Q-B1-Sub-2 + Q-B1-Sub-9.

        Reads INTENT/SUCCESS records from Mem0 sidecar partition; ROLLBACKs
        orphan INTENTs (delete from Mem0); rehydrates `_idempotency_cache`
        from SUCCESS records with `(payload_hash, prior_call_at, dto)` tuple
        for full Q-B1-Sub-9 IdempotencyViolation support.

        ROLLBACK over COMPLETE per Q-B1-Sub-2 rationale: intent records carry
        only `(operation, key, payload_hash, input_correlation_id)` — NOT the
        full input DTO. COMPLETE would require re-deriving operation input
        from upstream state (fragile, operation-specific). ROLLBACK preserves
        PS-2 idempotency invariant; caller-retry with same payload returns
        cached cleanly; caller-retry with different payload raises
        IdempotencyViolation.
        """
        sidecar = self._mem0.get_all(user_id=_VERDACA_SIDECAR_USER_ID)
        intents: dict[tuple[str, str], dict] = {}
        successes: dict[tuple[str, str], dict] = {}
        for record in sidecar.get("results", []):
            meta = record.get("metadata") or {}
            kind = meta.get(_IDEMPOTENCY_KIND_KEY)
            if kind not in ("intent", "success"):
                continue
            op = meta.get(_IDEMPOTENCY_OPERATION_KEY)
            key = meta.get(_IDEMPOTENCY_KEY_KEY)
            if op is None or key is None:
                continue
            op_key = (op, key)
            if kind == "intent":
                intents[op_key] = record
            else:
                successes[op_key] = record

        # ROLLBACK orphan INTENTs.
        for op_key, intent_record in intents.items():
            if op_key not in successes:
                self._mem0.delete(memory_id=intent_record["id"])

        # Rehydrate cache from SUCCESS records.
        for op_key, success_record in successes.items():
            meta = success_record.get("metadata") or {}
            result_dto_json = meta.get(_IDEMPOTENCY_RESULT_DTO_KEY)
            payload_hash = meta.get(_IDEMPOTENCY_PAYLOAD_HASH_KEY)
            prior_call_at_iso = meta.get(_IDEMPOTENCY_PRIOR_CALL_AT_KEY)
            if not (result_dto_json and payload_hash and prior_call_at_iso):
                continue
            prior_call_at = datetime.fromisoformat(prior_call_at_iso)
            operation = op_key[0]
            dto = self._deserialize_result_dto(operation, result_dto_json)
            self._idempotency_cache[op_key] = _CacheEntry(
                payload_hash=payload_hash,
                prior_call_at=prior_call_at,
                dto=dto,
            )

    def _deserialize_result_dto(self, operation: str, json_str: str) -> object:
        """Reconstruct cached DTO from sidecar SUCCESS-record JSON."""
        data = json.loads(json_str)
        dto_cls: type
        if operation == "store":
            dto_cls = StoredMemory
        elif operation == "promote":
            dto_cls = PromotedMemory
        elif operation == "revoke_promotion":
            dto_cls = RevokedPromotion
        else:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        return dto_cls(**data)

    def _emit_promote_span(
        self,
        *,
        hit_id: str,
        tier_from: str,
        tier_to: str,
        threshold_met: float,
        threshold_required: float,
    ) -> None:
        """AP-6 PS-3 5-attribute canonical span (set-equality verbatim).

        Per `port-contracts.md` v0.2.1 §3.4 PS-3: span MUST carry exactly
        the 5 canonical attributes — missing any is a ContractViolation;
        extra attributes outside the set are non-conformant. Q-B3-4
        disposition: `verdaca.memory.confidence_synthesis` is NOT on this
        span (adapter-private degraded-signal observability, query-only).
        """
        with _tracer.start_as_current_span("verdaca.port.memory.promote") as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.tier_from", tier_from)
            span.set_attribute("verdaca.memory.tier_to", tier_to)
            span.set_attribute("verdaca.memory.threshold_met", threshold_met)
            span.set_attribute("verdaca.memory.threshold_required", threshold_required)

    def _emit_revoke_span(
        self,
        *,
        hit_id: str,
        tier_from: str,
        tier_to: str,
    ) -> None:
        """AP-6 3-attribute mirror span for revoke_promotion per Q-B1-Sub-6.

        PS-3 set-equality is promote-specific (per §3.4 PS-3 wording "Every
        promote call..."); revoke emits a 3-attribute subset mirroring the
        tier transition. F-004 SpanRelabeler: only `verdaca.port.memory.*`
        names leave the adapter.
        """
        with _tracer.start_as_current_span(
            "verdaca.port.memory.revoke_promotion"
        ) as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.tier_from", tier_from)
            span.set_attribute("verdaca.memory.tier_to", tier_to)

    def _emit_degraded_signal_span(
        self,
        *,
        hit_id: str,
        synthesis: str,
    ) -> None:
        """Adapter-private degraded-signal observability per Q-B3-4.

        Emitted ONLY on query() degraded-signal path (`synthesis="default-1.0"`
        when Mem0 search result lacks `score` field) per advisor prior #2 +
        N2 inversion. NOT on AP-6 promote canonical set; NOT on common-case
        query path. Per N2 finding (Mem0 v1.0.11 search exposes `score`),
        this span fires rarely — genuine rare-event observability.
        """
        with _tracer.start_as_current_span(
            "verdaca.port.memory.confidence_synthesis"
        ) as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.confidence_synthesis", synthesis)


__all__ = ["Mem0Adapter"]
