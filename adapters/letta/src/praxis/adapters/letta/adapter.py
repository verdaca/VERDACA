"""Letta adapter — Memory port implementation.

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3): SECONDARY adapter in
the dual-adapter Memory port pair. Wraps `letta-client` PyPI SDK 1.10.3
behind `MemoryPort`. Mem0 primary adapter at `adapters/mem0/` (shipped
34a4eca; B.2 is the substitute-readiness validator per
`port-contracts.md` v0.2.1 §3 substitute-readiness clause).

Authority caveat (Option D-refined per `project_verdaca_stage9_4_3`):
the spec docs `port-contracts.md` v0.2.1 + `ports-architecture.md` v0.3
live in `_bmad-output/implementation-artifacts/verdaca/stage9/` which
is gitignored. Substance-of-record for ADR-1 §3.6 DTO field shapes is
the commit body of `f843d44` (corrigendum) + `4b0a829` (port-file
convergence); local working surface is secondary. Sectional cites used
throughout per V8 Approach b discipline.

Server pre-1.0 caveat (Q-B2-Sub-9): SDK `letta-client` v1.10.3 is
post-1.0; server-side `letta` is pre-1.0 (v0.16.7 / 2026-03-31). SDK
stability is downstream of server schema; v0.x server may break compat
at v0.17.0+ and force SDK v2.0 bump.

Substrate composition (per Letta SDK survey 2026-05-03 + #3 SDK
introspection probes):
    store          — `client.agents.passages.create(agent_id, text, tags)`
                     directly maps `MemoryEntry.content -> text` (no
                     chat-format marshaling — survey §6.1 simplification
                     vs Mem0). Metadata round-trips via tags using
                     Sub-3 Option γ type-prefix encoding
                     `<key>=<value>:<type>`. Asserts len==1 single-
                     passage return per Amendment E disposition; raises
                     ContractViolation on 0 or N>1 cardinality.
    query          — `client.agents.passages.search(agent_id, query,
                     top_k)` returns `PassageSearchResponse` with
                     `count: int` and `results: List[Result]` where
                     `Result` carries `id / content / timestamp / tags`
                     ONLY — NO native `score` field per Amendment D
                     disposition (survey §5.2 misread the types-namespace;
                     actual return type at
                     `types.agents.passage_search_response.Result` has
                     no score; only the unused
                     `types.passage_search_response.PassageSearchResponseItem`
                     carries it). Confidence falls back to default-1.0
                     synthesis with adapter-private span emission per
                     hit (matches B.1 pattern verbatim, NOT rare-path).
    promote        — adapter-synthesized via promotion-state sidecar
                     passages on the same singleton agent (survey §5.3
                     Option B). Letta has no native passage-update; no
                     native promote/tier semantic — Q-B2-6 OVERRIDE
                     zero-cost. PS-1 threshold check raises
                     PromotionContractViolation BEFORE upstream call.
    revoke_promotion — sidecar promotion-state passage delete via
                     `client.agents.passages.delete(memory_id, agent_id)`.
                     Natural-key dedup per Q-B1-Sub-1
                     (sha256(promotion_id:reason)).
    migrate        — adapter-internal migrator registry (Q-MIGRATE-1 =
                     M.1; no Protocol-level migrator parameter); per-
                     passage delete-and-recreate (Letta has no
                     passage-update method). AP-8 offline-window
                     amortizes the cost (`port-contracts.md` v0.2.1
                     §3.5(a)). NO runtime span emission per Sub-10b
                     advisor disposition (B.1 silence symmetry);
                     migration.path = "delete_and_recreate" semantic
                     documented in `changelog.md` only.

Discriminator-tag taxonomy per Amendment A (sidecar passages share the
singleton agent with user passages; tags partition the namespace):
    verdaca.kind=user:str             — caller MemoryEntry-store passages
    verdaca.kind=promotion_state:str  — promotion-state sidecar passages
    verdaca.kind=idempotency:str      — AP-5 INTENT/SUCCESS sidecar
                                        passages

    `query()` filters sidecar passages by EXCLUDING the latter two
    kinds from raw search results. Filter is post-search client-side;
    if cardinality drops below top_k due to filtering, do NOT compensate
    with additional fetch (preserves M-T-MEM-QUERY-04 cardinality-drift
    contract). Promotion-state cache rehydrate at `on_init()` does the
    INVERSE — INCLUDES only promotion-state-tagged passages.

Singleton agent provisioning (Q-B2-Sub-1 (c) hybrid):
    Caller may DI an explicit `system_agent_id` at `__init__`. If None,
    `on_init()` auto-creates with deterministic name pattern
    `f"verdaca-memory-{sha256(api_key)[:8]}"` and model resolved from
    `system_agent_model` ctor kwarg → `VERDACA_LETTA_DEFAULT_MODEL` env
    → ContractViolation if neither resolves. NO silent fallback.

Tag-encoding convention (Sub-3 Option γ + Amendment B):
    `<key>=<value>:<type>` where `<type>` ∈ {str, int, float, bool}.
    Amendment B bans `=` and `:` in str values to prevent round-trip
    decode ambiguity; `_encode_tag()` raises `ContractViolation`
    (violation_class="value") if encountered. Caller MemoryEntry.metadata
    str values are subject to this constraint. Idempotency keys and
    correlation IDs that may carry caller-arbitrary characters are
    sha256-hashed before tag encoding (preserves dedup semantics; loses
    informational round-trip on rehydrate). DTO payloads with
    JSON-syntax `:` chars are stored in passage `text` field (no
    constraint), not as tag values. Stage 10 hardening: caller-arbitrary
    value support via base64-encoded escape per advisor disposition.

AP obligations (per `port-contracts.md` v0.2.1 §7 + AP names per
`ports-architecture.md` v0.3 §2.3):
    AP-3 TierNormalizer        — `_normalize_tier()` (query, promote)
    AP-4 ThresholdGuard        — inline PS-1 at `promote()` top
    AP-5 TwoPhaseIdempotencyCommit — `_idempotency_dedup()` +
                                  `_idempotency_write_intent()` +
                                  `_idempotency_write_success()` +
                                  `_reconcile_idempotency_cache()` at
                                  `on_init` via Letta-side
                                  `verdaca.kind=idempotency:str`-tagged
                                  passages (Q-B1-22 (i') inherited at
                                  34a4eca).
    AP-6 SpanAttributeContract — `_emit_promote_span()` 5 canonical
                                  attrs (PS-3 set-equality verbatim);
                                  `_emit_revoke_span()` 3-attr mirror
                                  per Q-B1-Sub-6;
                                  `_emit_confidence_synthesis_span()`
                                  adapter-private per-hit emission
                                  (Amendment D).
    AP-7 OpaqueIDWrapper       — `uuid.uuid4().hex` for `promotion_id`.
    AP-9 ConfidenceScaleNormalizer — default-1.0 synthesis only per
                                  Amendment D (no range-check codepath;
                                  Letta `Result` has no score field).

Idempotency profile (per `port-contracts.md` v0.2.1 §3 idempotency
table, identical to B.1 at 34a4eca):
    store              — sync, idempotent (idempotency_key required)
    query              — sync, idempotent (sequence return; no key)
    promote            — sync, idempotent (idempotency_key required
                         from rationale)
    revoke_promotion   — sync, idempotent (natural-key dedup per
                         Q-B1-Sub-1)
    migrate            — sync, NOT idempotent (single-fire per
                         version pair)

OTEL span discipline (per `port-contracts.md` v0.2.1 §3.4 PS-3 +
F-004 SpanRelabeler, identical to B.1 at 34a4eca for promote/revoke;
B.2-specific per-hit emission for confidence_synthesis per Amendment D):
    promote span name        — `verdaca.port.memory.promote`
                               5 canonical attributes EXACTLY (set-equality)
    revoke_promotion span    — `verdaca.port.memory.revoke_promotion`
                               3-attribute mirror per Q-B1-Sub-6
    confidence_synthesis span — `verdaca.port.memory.confidence_synthesis`
                               adapter-private; per-hit emission
                               (synthesis="default-1.0") per Amendment D
                               since Letta `Result` has no native score
    F-004 SpanRelabeler      — zero `letta.*` upstream-native span
                               names leak past adapter boundary

Error specializations (per `port-contracts.md` v0.2.1 §3.4):
    PromotionContractViolation — PS-1 threshold violation at promote()
    PromotionRevocationFailed  — PS-4 SLO violation at revoke_promotion()
                                 (sidecar absent or upstream-deleted)
    ContractViolation          — DTO/tier-normalization invariant
                                 violation; tag-encoding char ban per
                                 Amendment B; len==1 store assertion
                                 per Amendment E
    IdempotencyViolation       — AP-5 payload-equivalence mismatch
                                 (Q-B1-Sub-9)
    UpstreamUnavailable        — Letta health() probe / agents API
                                 failure at on_init()

Deprecation policy: see `ports-architecture.md` v0.3 §6 for
`API_VERSION` / `schema_version` bump rules.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar

from letta_client import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    Letta,
    NotFoundError,
)
from opentelemetry import trace

from praxis.adapters.letta.version_pin import UPSTREAM_NAME
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

_PORT_NAME = "memory"

# Discriminator tags per Amendment A. Verbatim string-form (NOT routed
# through `_encode_tag`) so that membership checks remain trivial:
# `_KIND_USER in passage.tags` etc.
_KIND_USER = "verdaca.kind=user:str"
_KIND_PROMOTION_STATE = "verdaca.kind=promotion_state:str"
_KIND_IDEMPOTENCY = "verdaca.kind=idempotency:str"

# System-tag key namespace per Sub-3 Option γ (`<key>=<value>:<type>`).
_TAG_TIER = "verdaca.tier"
_TAG_CONFIDENCE = "verdaca.confidence"
_TAG_SOURCE_SPAN_ID = "verdaca.source_span_id"
_TAG_SCHEMA_VERSION = "verdaca.schema_version"
_TAG_META_PREFIX = "verdaca.meta."  # caller MemoryEntry.metadata pass-through

# Promotion-state sidecar tag namespace.
_TAG_PROMOTION_TIER = "verdaca.promotion_state.tier"
_TAG_PROMOTION_ID = "verdaca.promotion_state.promotion_id"

# Idempotency-sidecar tag namespace.
_TAG_IDEMPOTENCY_KIND = "verdaca.idempotency.kind"
_TAG_IDEMPOTENCY_OPERATION = "verdaca.idempotency.operation"
_TAG_IDEMPOTENCY_KEY_HASH = "verdaca.idempotency.key_hash"
_TAG_IDEMPOTENCY_PAYLOAD_HASH = "verdaca.idempotency.payload_hash"

_VALID_TYPE_TOKENS = ("str", "int", "float", "bool")

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

    Sibling pattern: `Mem0Adapter._migrator_signature` at 34a4eca
    (`adapters/mem0/src/praxis/adapters/mem0/adapter.py:181-193`).
    """
    try:
        source = inspect.getsource(migrator)
    except (OSError, TypeError):
        source = repr(migrator)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _hash_caller_string(value: str) -> str:
    """Caller-supplied string → sha256 hex (Amendment B safety wrapper).

    Caller idempotency keys may carry arbitrary characters including
    `=` and `:` which violate Sub-3 Option γ tag encoding. Hashing
    preserves dedup semantics (same input → same hash → same cache key)
    while losing the informational round-trip. The original string is
    available at the call site for `IdempotencyViolation` reporting.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    """In-process AP-5 cache entry per Q-B1-Sub-9 payload-equivalence.

    Mirrors B.1 `_CacheEntry` at 34a4eca. The cache is keyed by
    (operation, key_hash) where key_hash = sha256(idempotency_key);
    `payload_hash` enables `IdempotencyViolation` raise on key-reuse
    with non-equivalent payload.
    """

    payload_hash: str
    prior_call_at: datetime
    dto: object


@dataclass(frozen=True, slots=True)
class _PromotionState:
    """Promotion-state cache entry per Amendment C.

    Rehydrated at `on_init()` from Letta-side passages tagged with
    `_KIND_PROMOTION_STATE`. Mutated on `promote()` / `revoke_promotion()`.
    Multi-LettaAdapter-instance staleness is a Stage 10 deferred concern
    (see `changelog.md`).

    `passage_id` — the user passage this state record points at.
    `sidecar_id` — the promotion-state sidecar passage's own ID
                   (needed for delete on revoke).
    `tier` — the post-promotion tier (overrides user passage's verdaca.tier
             on the query path).
    `promotion_id` — the AP-7 OpaqueIDWrapper-generated identifier.
    `rationale_json` — JSON-serialized PromotionRationale (informational).
    """

    passage_id: str
    sidecar_id: str
    tier: str
    promotion_id: str
    rationale_json: str


class LettaAdapter:
    """In-tree PyPI-pinned wrap of `letta-client` SDK against `MemoryPort`.

    Conforms to `praxis.ports.memory.MemoryPort` (verify via
    `isinstance(adapter, MemoryPort)`; the Protocol is `@runtime_checkable`).
    SECONDARY adapter in the dual-adapter pair (Mem0 primary at 34a4eca);
    substitute-readiness validator per `port-contracts.md` v0.2.1 §3.
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the
    # attribute, isinstance checks the candidate has it. Per 9.4.1
    # API_VERSION ClassVar bug lesson (executor playbook §9.C addendum;
    # B.1 precedent at `adapters/mem0/src/praxis/adapters/mem0/adapter.py:221`).
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        letta_client: Letta,
        system_agent_id: str | None = None,
        system_agent_model: str | None = None,
        migrators: dict[tuple[int, int], Callable[[dict], dict]] | None = None,
        default_correlation_id: str | None = None,
    ) -> None:
        """Construct an adapter.

        `letta_client` is the caller-constructed `Letta` instance per
        Q-B1-1 caller-DI symmetric discipline (B.1 precedent at 34a4eca).
        Letta SDK is non-eager (httpx wrapper) — caller pays trivial
        cost at construct; no LLM/embedder/vector-store init happens at
        `Letta()` build time (survey §3 contrast vs Mem0).

        `system_agent_id` is the Letta agent ID this adapter routes all
        port operations through (per Q-B2-Sub-1 (c) hybrid disposition).
        If None, `on_init()` auto-creates with deterministic name. If
        the caller pre-provisions an agent (e.g., for multi-tenant or
        test scenarios), supply via this kwarg.

        `system_agent_model` is the model identifier passed to
        `agents.create()` if auto-create fires. If None at auto-create
        time, `on_init()` resolves from `VERDACA_LETTA_DEFAULT_MODEL`
        env var; raises `ContractViolation` if neither resolves.

        `migrators` is the M.1 adapter-internal migrator registry per
        Q-MIGRATE-1 + Q-B1-Sub-7 inherited at 34a4eca.

        `default_correlation_id` per BeadsAdapter / TONLAdapter / B.1
        precedent.
        """
        self._letta = letta_client
        self._system_agent_id = system_agent_id
        self._system_agent_model = system_agent_model
        self._migrator_registry: dict[tuple[int, int], Callable[[dict], dict]] = (
            migrators or {}
        )
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        # Q-B1-22 (i') inherited at 34a4eca: in-process dict; rehydrated
        # at `on_init` from Letta-side `verdaca.kind=idempotency:str` passages.
        # Cache key is (operation, sha256(idempotency_key)) — see
        # `_hash_caller_string` for rationale.
        self._idempotency_cache: dict[tuple[str, str], _CacheEntry] = {}
        # Amendment C: promotion-state cache rehydrated at `on_init`.
        # Two indices: by promotion_id for revoke O(1); by passage_id
        # for query() tier-override O(1).
        self._promotion_by_id: dict[str, _PromotionState] = {}
        self._promotion_by_passage: dict[str, _PromotionState] = {}

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.3 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check + Letta liveness + agent
        provisioning + AP-5 + Amendment C reconciliation.

        Sub-5 disposition: unconditional `client.health()`. Mapping
        APIConnectionError / APITimeoutError / InternalServerError →
        UpstreamUnavailable; AuthenticationError → ContractViolation
        (config error, not transient).
        """
        if not isinstance(self, MemoryPort):
            raise RuntimeError("LettaAdapter does not conform to MemoryPort")

        # Sub-5: liveness probe.
        try:
            self._letta.health()
        except (APIConnectionError, APITimeoutError, InternalServerError) as exc:
            raise UpstreamUnavailable(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                last_known_health=_utc_now(),
            ) from exc
        except AuthenticationError as exc:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            ) from exc

        # Sub-1 (c): singleton agent provisioning.
        if self._system_agent_id is None:
            self._system_agent_id = self._resolve_or_create_system_agent()

        # Q-B1-22 (i') inherited: AP-5 reconciliation.
        self._reconcile_idempotency_cache()
        # Amendment C: promotion-state cache rehydrate.
        self._load_promotion_state_cache()

    def on_shutdown(self) -> None:
        """Lifecycle: Letta client cleanup if available.

        #3 Probe 6 confirmed: `Letta` instance exposes callable `close()`.
        Mirrors B.1 pattern (`adapters/mem0/.../adapter.py:295-304` at
        34a4eca).
        """
        close = getattr(self._letta, "close", None)
        if callable(close):
            close()

    # ------------------------------------------------------------------
    # MemoryPort surface (5 methods)
    # ------------------------------------------------------------------

    def store(self, entry: MemoryEntry) -> StoredMemory:
        """Per `port-contracts.md` v0.2.1 §3 store() spec + §3 idempotency
        table (idempotency_key REQUIRED).

        Letta-side: `client.agents.passages.create(agent_id, text, tags)`
        directly. text=entry.content (no chat-format marshaling — survey
        §6.1). tags carry verdaca.* round-trip per Sub-3 Option γ.
        Asserts len==1 single-passage return per Amendment E disposition.
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
        cached = self._idempotency_dedup(
            "store", entry.idempotency_key, payload_hash
        )
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent("store", entry.idempotency_key, payload_hash)

        # Marshal MemoryEntry → tags per Sub-3 Option γ.
        tags: list[str] = [_KIND_USER]
        tags.append(self._encode_tag(_TAG_TIER, "working"))
        tags.append(self._encode_tag(_TAG_CONFIDENCE, entry.confidence))
        tags.append(self._encode_tag(_TAG_SOURCE_SPAN_ID, entry.source_span_id))
        tags.append(self._encode_tag(_TAG_SCHEMA_VERSION, entry.schema_version))
        for k, v in entry.metadata.items():
            tags.append(self._encode_tag(f"{_TAG_META_PREFIX}{k}", v))

        response = self._letta.agents.passages.create(
            agent_id=self._system_agent_id,
            text=entry.content,
            tags=tags,
        )
        # Amendment E: single-passage assertion. Letta server-side
        # extraction may chunk a single-text input into 0 or N>1
        # passages; caller MUST configure server such that direct
        # text-insert returns exactly one passage. See changelog.md
        # "Caller-DI Letta instance configuration" for the constraint.
        if len(response) != 1 or response[0].id is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=entry.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )

        stored = StoredMemory(
            schema_version=entry.schema_version,
            correlation_id=entry.correlation_id,
            idempotency_key=entry.idempotency_key,
            stored_id=response[0].id,
        )
        now = _utc_now()
        self._idempotency_write_success(
            "store", entry.idempotency_key, payload_hash, now, stored
        )
        key_hash = _hash_caller_string(entry.idempotency_key)
        self._idempotency_cache[("store", key_hash)] = _CacheEntry(
            payload_hash=payload_hash,
            prior_call_at=now,
            dto=stored,
        )
        return stored

    def query(self, q: MemoryQuery) -> Sequence[MemoryHit]:
        """Per `port-contracts.md` v0.2.1 §3 query() spec.

        Amendment A: filter sidecar passages from raw search results;
        do NOT compensate for cardinality drop (preserves M-T-MEM-QUERY-04
        cardinality-drift contract).

        Amendment D: AP-9 default-1.0 synthesis only; Letta `Result`
        type carries no native `score` field. Adapter-private
        `verdaca.memory.confidence_synthesis` span fires per-hit
        (matches B.1 `_emit_degraded_signal_span` shape; renamed to
        `_emit_confidence_synthesis_span` for B.2 since it's no longer
        rare-path).

        Amendment C: promotion-state cache override on tier — if a
        promotion-state record exists for the hit's passage_id, use its
        tier instead of the user passage's `verdaca.tier`.
        """
        response = self._letta.agents.passages.search(
            agent_id=self._system_agent_id,
            query=q.query_text,
            top_k=q.k,
        )
        hits: list[MemoryHit] = []
        for item in response.results:
            tags = item.tags or []
            # Amendment A: exclude sidecar kinds.
            if _KIND_PROMOTION_STATE in tags or _KIND_IDEMPOTENCY in tags:
                continue
            tag_dict = self._decode_tags(tags)
            # Amendment C: promotion-state override on tier.
            promo = self._promotion_by_passage.get(item.id)
            if promo is not None:
                tier_raw = promo.tier
            else:
                tier_raw_any = tag_dict.get(_TAG_TIER, "working")
                tier_raw = tier_raw_any if isinstance(tier_raw_any, str) else "working"
            tier = self._normalize_tier(tier_raw, correlation_id=q.correlation_id)
            # Amendment D: default-1.0 synthesis (Letta Result has no score).
            confidence = 1.0
            self._emit_confidence_synthesis_span(
                hit_id=item.id, synthesis="default-1.0"
            )
            hits.append(
                MemoryHit(
                    schema_version=q.schema_version,
                    correlation_id=q.correlation_id,
                    idempotency_key=q.idempotency_key,
                    hit_id=item.id,
                    content=item.content,
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
        (confidence-threshold) + PS-3 (5-attribute OTEL span set-equality)
        + §3 idempotency table (idempotency_key REQUIRED from rationale).

        AP-4 ThresholdGuard runs BEFORE any upstream call per PS-1
        verbatim. Survey §5.3 + Q-B2-6 OVERRIDE: synthesis via
        promotion-state sidecar passages; Letta has no native promote
        nor passage-update.
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
        payload_hash = _compute_payload_hash(
            "promote", hit_id, target_tier, rationale
        )
        cached = self._idempotency_dedup(
            "promote", rationale.idempotency_key, payload_hash
        )
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent(
            "promote", rationale.idempotency_key, payload_hash
        )

        # tier_from: Amendment C cache override else "working".
        existing = self._promotion_by_passage.get(hit_id)
        tier_from = existing.tier if existing is not None else "working"
        tier_from = self._normalize_tier(
            tier_from, correlation_id=rationale.correlation_id
        )
        promotion_id = uuid.uuid4().hex  # AP-7 OpaqueIDWrapper

        # Sidecar passage: tags carry tier+promotion_id; rationale JSON
        # lives in passage `text` to avoid Amendment B `:` ban
        # (rationale.model_dump_json() contains JSON `:` chars).
        rationale_dict = rationale.model_dump()
        sidecar_text = json.dumps(
            {"hit_id": hit_id, "rationale": rationale_dict}
        )
        sidecar_tags = [
            _KIND_PROMOTION_STATE,
            self._encode_tag(_TAG_PROMOTION_ID, promotion_id),
            self._encode_tag(_TAG_PROMOTION_TIER, target_tier.value),
        ]
        sidecar_response = self._letta.agents.passages.create(
            agent_id=self._system_agent_id,
            text=sidecar_text,
            tags=sidecar_tags,
        )
        if len(sidecar_response) != 1 or sidecar_response[0].id is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=rationale.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        sidecar_id = sidecar_response[0].id

        # Amendment C cache invalidate-and-update.
        new_state = _PromotionState(
            passage_id=hit_id,
            sidecar_id=sidecar_id,
            tier=target_tier.value,
            promotion_id=promotion_id,
            rationale_json=json.dumps(rationale_dict),
        )
        prior = self._promotion_by_passage.get(hit_id)
        if prior is not None:
            self._promotion_by_id.pop(prior.promotion_id, None)
        self._promotion_by_passage[hit_id] = new_state
        self._promotion_by_id[promotion_id] = new_state

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
        key_hash = _hash_caller_string(rationale.idempotency_key)
        self._idempotency_cache[("promote", key_hash)] = _CacheEntry(
            payload_hash=payload_hash,
            prior_call_at=now,
            dto=promoted,
        )
        return promoted

    def revoke_promotion(self, promotion_id: str, reason: str) -> RevokedPromotion:
        """Per `port-contracts.md` v0.2.1 §3 revoke_promotion() + §3.4
        PS-4 (time-bounded SLO).

        Q-B1-Sub-1 natural-key dedup (no idempotency_key parameter).
        Letta-side: simple delete of promotion-state sidecar passage
        (Letta supports `passages.delete`; no read-merge-update needed
        unlike B.1).
        """
        dedup_key = hashlib.sha256(
            f"{promotion_id}:{reason}".encode("utf-8")
        ).hexdigest()
        payload_hash = _compute_payload_hash(
            "revoke_promotion", promotion_id, reason
        )
        cached = self._idempotency_dedup(
            "revoke_promotion", dedup_key, payload_hash
        )
        if cached is not None:
            return cached  # type: ignore[return-value]

        self._idempotency_write_intent(
            "revoke_promotion", dedup_key, payload_hash
        )

        # Amendment C cache lookup; PS-4 raises if absent.
        state = self._promotion_by_id.get(promotion_id)
        if state is None:
            raise PromotionRevocationFailed(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                promotion_id=promotion_id,
            )
        tier_from = self._normalize_tier(
            state.tier, correlation_id=self._default_correlation_id
        )

        # Delete the sidecar passage on Letta.
        try:
            self._letta.agents.passages.delete(
                memory_id=state.sidecar_id,
                agent_id=self._system_agent_id,
            )
        except NotFoundError as exc:
            # Sidecar already gone server-side; treat as PS-4 SLO miss.
            raise PromotionRevocationFailed(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                promotion_id=promotion_id,
            ) from exc

        # Amendment C cache invalidate.
        self._promotion_by_id.pop(promotion_id, None)
        self._promotion_by_passage.pop(state.passage_id, None)

        # AP-6 3-attribute mirror per Q-B1-Sub-6.
        self._emit_revoke_span(
            hit_id=state.passage_id,
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
        # dedup_key is already sha256-hex; use directly as cache key
        # (no double-hash via _hash_caller_string).
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

        Q-MIGRATE-1 = M.1 inherited at 34a4eca: adapter-internal
        `_migrator_registry` lookup; no Protocol-level `migrator`
        parameter.

        Letta-side: per-passage delete-and-recreate (no native
        passage-update method per survey §5.5). AP-8 offline-window
        amortizes the cost (`port-contracts.md` v0.2.1 §3.5(a)).

        Sub-10b advisor disposition: NO runtime span emission
        (B.1 silence symmetry); migration.path = "delete_and_recreate"
        semantic documented in `changelog.md` only.
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

        entries_migrated = 0
        from_version_tag = self._encode_tag(_TAG_SCHEMA_VERSION, from_version)
        # Cursor pagination over user passages.
        after: str | None = None
        while True:
            page = self._letta.agents.passages.list(
                agent_id=self._system_agent_id,
                limit=100,
                after=after,
            )
            if not page:
                break
            for passage in page:
                if passage.id is None:
                    continue
                tags = passage.tags or []
                # Filter to user passages at from_version.
                if _KIND_USER not in tags:
                    continue
                if from_version_tag not in tags:
                    continue
                migrated = migrator(
                    {"text": passage.text, "tags": list(tags)}
                )
                # Delete-and-recreate per asymmetry #1.
                self._letta.agents.passages.delete(
                    memory_id=passage.id,
                    agent_id=self._system_agent_id,
                )
                created = self._letta.agents.passages.create(
                    agent_id=self._system_agent_id,
                    text=migrated.get("text", passage.text),
                    tags=list(migrated.get("tags", tags)),
                )
                if len(created) != 1 or created[0].id is None:
                    raise ContractViolation(
                        port_name=_PORT_NAME,
                        correlation_id=self._default_correlation_id,
                        occurred_at=_utc_now(),
                        upstream_name=UPSTREAM_NAME,
                        violation_class="invariant",
                    )
                entries_migrated += 1
            after = page[-1].id
            if after is None:
                break

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
    # Internal helpers — agent provisioning + cache rehydrate
    # ------------------------------------------------------------------

    def _resolve_or_create_system_agent(self) -> str:
        """Q-B2-Sub-1 (c) hybrid: deterministic-name lookup; auto-create
        if absent. NO silent fallback — raise ContractViolation on
        unresolvable model.
        """
        api_key = getattr(self._letta, "api_key", None) or ""
        seed = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]
        agent_name = f"verdaca-memory-{seed}"
        # Existence check via name filter.
        try:
            page = self._letta.agents.list(name=agent_name)
        except (APIConnectionError, APITimeoutError, InternalServerError) as exc:
            raise UpstreamUnavailable(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                last_known_health=_utc_now(),
            ) from exc
        for agent in page:
            agent_id = getattr(agent, "id", None)
            if (
                getattr(agent, "name", None) == agent_name
                and isinstance(agent_id, str)
            ):
                return agent_id
        # Auto-create.
        model = self._system_agent_model or os.environ.get(
            "VERDACA_LETTA_DEFAULT_MODEL"
        )
        if model is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        try:
            created = self._letta.agents.create(name=agent_name, model=model)
        except (APIConnectionError, APITimeoutError, InternalServerError) as exc:
            raise UpstreamUnavailable(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                last_known_health=_utc_now(),
            ) from exc
        created_id = getattr(created, "id", None)
        if not isinstance(created_id, str):
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )
        return created_id

    def _load_promotion_state_cache(self) -> None:
        """Amendment C: rehydrate promotion-state caches from Letta-side
        sidecar passages.

        INVERSE filter from `query()` Amendment A: include only passages
        carrying `_KIND_PROMOTION_STATE`. Cursor-paginate the singleton
        agent's passages; decode tags + parse text-as-JSON for hit_id +
        rationale.
        """
        after: str | None = None
        while True:
            page = self._letta.agents.passages.list(
                agent_id=self._system_agent_id,
                limit=100,
                after=after,
            )
            if not page:
                break
            for passage in page:
                if passage.id is None:
                    continue
                tags = passage.tags or []
                if _KIND_PROMOTION_STATE not in tags:
                    continue
                tag_dict = self._decode_tags(tags)
                tier_any = tag_dict.get(_TAG_PROMOTION_TIER)
                promotion_id_any = tag_dict.get(_TAG_PROMOTION_ID)
                if not (
                    isinstance(tier_any, str)
                    and isinstance(promotion_id_any, str)
                ):
                    continue
                # text carries JSON `{"hit_id": ..., "rationale": ...}`.
                try:
                    text_obj = json.loads(passage.text)
                except (json.JSONDecodeError, ValueError):
                    continue
                hit_id = text_obj.get("hit_id") if isinstance(text_obj, dict) else None
                if not isinstance(hit_id, str):
                    continue
                rationale_dict = text_obj.get("rationale", {})
                state = _PromotionState(
                    passage_id=hit_id,
                    sidecar_id=passage.id,
                    tier=tier_any,
                    promotion_id=promotion_id_any,
                    rationale_json=json.dumps(rationale_dict),
                )
                self._promotion_by_id[promotion_id_any] = state
                self._promotion_by_passage[hit_id] = state
            after = page[-1].id
            if after is None:
                break

    # ------------------------------------------------------------------
    # Internal helpers — tag encoding/decoding (Sub-3 Option γ + Amendment B)
    # ------------------------------------------------------------------

    def _encode_tag(self, key: str, value: str | int | float | bool) -> str:
        """Sub-3 Option γ encoding `<key>=<value>:<type>`.

        Amendment B: ban `=` and `:` in str values to prevent
        round-trip decode ambiguity. Raises ContractViolation
        (violation_class="value") on violation. Caller MemoryEntry.metadata
        str values + caller-supplied source_span_id values are subject
        to this constraint. See `changelog.md` "Tag-encoding convention"
        for the constraint scope.
        """
        # bool MUST be checked before int (isinstance(True, int) == True).
        if isinstance(value, bool):
            type_token = "bool"
            value_str = "true" if value else "false"
        elif isinstance(value, int):
            type_token = "int"
            value_str = str(value)
        elif isinstance(value, float):
            type_token = "float"
            value_str = repr(value)  # round-trip-preserving for binary float
        elif isinstance(value, str):
            if "=" in value or ":" in value:
                raise ContractViolation(
                    port_name=_PORT_NAME,
                    correlation_id=self._default_correlation_id,
                    occurred_at=_utc_now(),
                    upstream_name=UPSTREAM_NAME,
                    violation_class="value",
                )
            type_token = "str"
            value_str = value
        else:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="type",
            )
        return f"{key}={value_str}:{type_token}"

    def _decode_tags(self, tags: list[str]) -> dict[str, str | int | float | bool]:
        """Sub-3 Option γ decode.

        Tags lacking `<key>=<value>:<type>` shape are skipped silently.
        Discriminator tags (`_KIND_USER` etc.) are full key=value:type
        tokens and decode cleanly into the dict; non-conforming legacy
        or malformed tags are ignored gracefully.
        """
        decoded: dict[str, str | int | float | bool] = {}
        for tag in tags:
            idx_colon = tag.rfind(":")
            if idx_colon == -1:
                continue
            kv_part = tag[:idx_colon]
            type_token = tag[idx_colon + 1 :]
            if type_token not in _VALID_TYPE_TOKENS:
                continue
            idx_eq = kv_part.find("=")
            if idx_eq == -1:
                continue
            key = kv_part[:idx_eq]
            value_str = kv_part[idx_eq + 1 :]
            value: str | int | float | bool
            if type_token == "str":
                value = value_str
            elif type_token == "int":
                try:
                    value = int(value_str)
                except ValueError:
                    continue
            elif type_token == "float":
                try:
                    value = float(value_str)
                except ValueError:
                    continue
            else:  # bool
                if value_str == "true":
                    value = True
                elif value_str == "false":
                    value = False
                else:
                    continue
            decoded[key] = value
        return decoded

    # ------------------------------------------------------------------
    # Internal helpers — AP-3 / AP-5 (mirrors B.1 at 34a4eca)
    # ------------------------------------------------------------------

    def _normalize_tier(
        self,
        raw: str,
        *,
        correlation_id: str,
    ) -> str:
        """AP-3 TierNormalizer (mirrors B.1 at 34a4eca).

        Per `ports/src/praxis/ports/memory.py:69` MemoryHit.tier Literal +
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
        """AP-5 dedup with payload-equivalence per Q-B1-Sub-9.

        Cache key is `(operation, sha256(key))` per `_hash_caller_string`
        rationale. Returns cached DTO if matching; raises
        `IdempotencyViolation` (carrying the ORIGINAL `key` per the DTO
        contract) on payload-hash mismatch.
        """
        # revoke_promotion synthesizes its own dedup_key as sha256 hex
        # already; double-hashing would be incorrect. Distinguish by
        # operation: revoke_promotion's key IS already the hash.
        if operation == "revoke_promotion":
            key_hash = key  # already sha256 hex
        else:
            key_hash = _hash_caller_string(key)
        cached = self._idempotency_cache.get((operation, key_hash))
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
    ) -> None:
        """AP-5 INTENT sidecar write per Q-B1-22 (i') + Q-B1-Sub-9.

        Persists `(operation, sha256(key), payload_hash)` to the
        singleton agent as a passage tagged with `_KIND_IDEMPOTENCY`.
        On startup, `_reconcile_idempotency_cache()` detects
        INTENT-without-SUCCESS and ROLLBACKs per Q-B1-Sub-2.

        Note: caller-supplied `key` may carry arbitrary chars; hashed
        via `_hash_caller_string` for tag encoding (Amendment B safety).
        """
        if operation == "revoke_promotion":
            key_hash = key
        else:
            key_hash = _hash_caller_string(key)
        tags = [
            _KIND_IDEMPOTENCY,
            self._encode_tag(_TAG_IDEMPOTENCY_KIND, "intent"),
            self._encode_tag(_TAG_IDEMPOTENCY_OPERATION, operation),
            self._encode_tag(_TAG_IDEMPOTENCY_KEY_HASH, key_hash),
            self._encode_tag(_TAG_IDEMPOTENCY_PAYLOAD_HASH, payload_hash),
        ]
        self._letta.agents.passages.create(
            agent_id=self._system_agent_id,
            text=f"[verdaca.idempotency.intent] {operation}",
            tags=tags,
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

        Persists `(operation, sha256(key), payload_hash)` as tags;
        `result_dto` (JSON-serialized) + `prior_call_at_us` (int
        microseconds) live in the passage `text` field as a JSON
        envelope (avoids Amendment B `:` ban on JSON syntax).
        """
        if operation == "revoke_promotion":
            key_hash = key
        else:
            key_hash = _hash_caller_string(key)
        result_dto_json = (
            result_dto.model_dump_json()
            if hasattr(result_dto, "model_dump_json")
            else json.dumps(_canonicalize(result_dto))
        )
        prior_call_at_us = int(prior_call_at.timestamp() * 1_000_000)
        text_envelope = json.dumps(
            {
                "result_dto": json.loads(result_dto_json),
                "prior_call_at_us": prior_call_at_us,
            }
        )
        tags = [
            _KIND_IDEMPOTENCY,
            self._encode_tag(_TAG_IDEMPOTENCY_KIND, "success"),
            self._encode_tag(_TAG_IDEMPOTENCY_OPERATION, operation),
            self._encode_tag(_TAG_IDEMPOTENCY_KEY_HASH, key_hash),
            self._encode_tag(_TAG_IDEMPOTENCY_PAYLOAD_HASH, payload_hash),
        ]
        self._letta.agents.passages.create(
            agent_id=self._system_agent_id,
            text=text_envelope,
            tags=tags,
        )

    def _reconcile_idempotency_cache(self) -> None:
        """AP-5 reconciliation per Q-B1-22 (i') + Q-B1-Sub-2 + Q-B1-Sub-9.

        Reads idempotency-sidecar passages; ROLLBACKs orphan INTENTs
        (delete from Letta); rehydrates `_idempotency_cache` from
        SUCCESS records.

        ROLLBACK over COMPLETE per Q-B1-Sub-2 rationale (B.1 commit body
        at 34a4eca verbatim): intent records carry only
        `(operation, key_hash, payload_hash)` — NOT the full input DTO.
        COMPLETE would require re-deriving operation input from upstream
        state (fragile, operation-specific). ROLLBACK preserves PS-2
        idempotency invariant.
        """
        intents: dict[tuple[str, str], str] = {}  # (op, key_hash) → passage_id
        successes: dict[tuple[str, str], dict[str, Any]] = {}
        # (op, key_hash) → {"passage_id": ..., "payload_hash": ...,
        #                    "prior_call_at_us": ..., "result_dto": ...}
        after: str | None = None
        while True:
            page = self._letta.agents.passages.list(
                agent_id=self._system_agent_id,
                limit=100,
                after=after,
            )
            if not page:
                break
            for passage in page:
                if passage.id is None:
                    continue
                tags = passage.tags or []
                if _KIND_IDEMPOTENCY not in tags:
                    continue
                tag_dict = self._decode_tags(tags)
                kind = tag_dict.get(_TAG_IDEMPOTENCY_KIND)
                op = tag_dict.get(_TAG_IDEMPOTENCY_OPERATION)
                key_hash = tag_dict.get(_TAG_IDEMPOTENCY_KEY_HASH)
                payload_hash = tag_dict.get(_TAG_IDEMPOTENCY_PAYLOAD_HASH)
                if not (
                    isinstance(kind, str)
                    and isinstance(op, str)
                    and isinstance(key_hash, str)
                    and isinstance(payload_hash, str)
                ):
                    continue
                op_key = (op, key_hash)
                if kind == "intent":
                    intents[op_key] = passage.id
                elif kind == "success":
                    try:
                        envelope = json.loads(passage.text)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if not isinstance(envelope, dict):
                        continue
                    successes[op_key] = {
                        "passage_id": passage.id,
                        "payload_hash": payload_hash,
                        "prior_call_at_us": envelope.get("prior_call_at_us"),
                        "result_dto": envelope.get("result_dto"),
                    }
            after = page[-1].id
            if after is None:
                break

        # ROLLBACK orphan INTENTs (no matching SUCCESS).
        for op_key, intent_passage_id in intents.items():
            if op_key not in successes:
                try:
                    self._letta.agents.passages.delete(
                        memory_id=intent_passage_id,
                        agent_id=self._system_agent_id,
                    )
                except NotFoundError:
                    # Already gone server-side; reconciliation idempotent.
                    pass

        # Rehydrate cache from SUCCESS records.
        for op_key, success in successes.items():
            prior_call_at_us = success.get("prior_call_at_us")
            result_dto = success.get("result_dto")
            payload_hash = success.get("payload_hash")
            if not (
                isinstance(prior_call_at_us, int)
                and isinstance(result_dto, dict)
                and isinstance(payload_hash, str)
            ):
                continue
            prior_call_at = datetime.fromtimestamp(
                prior_call_at_us / 1_000_000, tz=timezone.utc
            )
            operation = op_key[0]
            try:
                dto = self._deserialize_result_dto(operation, result_dto)
            except ContractViolation:
                continue
            self._idempotency_cache[op_key] = _CacheEntry(
                payload_hash=payload_hash,
                prior_call_at=prior_call_at,
                dto=dto,
            )

    def _deserialize_result_dto(
        self,
        operation: str,
        data: dict[str, Any],
    ) -> object:
        """Reconstruct cached DTO from sidecar SUCCESS-record JSON envelope."""
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

    # ------------------------------------------------------------------
    # Internal helpers — AP-6 OTEL spans
    # ------------------------------------------------------------------

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

        Mirrors B.1 `_emit_promote_span` at 34a4eca verbatim — substrate-
        neutral per substitute-readiness clause (`port-contracts.md`
        v0.2.1 §3). Per §3.4 PS-3: span MUST carry exactly the 5
        canonical attributes — missing any is a ContractViolation; extra
        attributes outside the set are non-conformant. Q-B3-4
        disposition: `verdaca.memory.confidence_synthesis` is NOT on
        this span (adapter-private degraded-signal observability,
        query-only).
        """
        with _tracer.start_as_current_span("verdaca.port.memory.promote") as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.tier_from", tier_from)
            span.set_attribute("verdaca.memory.tier_to", tier_to)
            span.set_attribute("verdaca.memory.threshold_met", threshold_met)
            span.set_attribute(
                "verdaca.memory.threshold_required", threshold_required
            )

    def _emit_revoke_span(
        self,
        *,
        hit_id: str,
        tier_from: str,
        tier_to: str,
    ) -> None:
        """AP-6 3-attribute mirror span for revoke_promotion per Q-B1-Sub-6.

        Mirrors B.1 `_emit_revoke_span` at 34a4eca verbatim. PS-3
        set-equality is promote-specific (per §3.4 PS-3 wording "Every
        promote call..."); revoke emits a 3-attribute subset mirroring
        the tier transition. F-004 SpanRelabeler: only
        `verdaca.port.memory.*` names leave the adapter.
        """
        with _tracer.start_as_current_span(
            "verdaca.port.memory.revoke_promotion"
        ) as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.tier_from", tier_from)
            span.set_attribute("verdaca.memory.tier_to", tier_to)

    def _emit_confidence_synthesis_span(
        self,
        *,
        hit_id: str,
        synthesis: str,
    ) -> None:
        """Adapter-private confidence-synthesis observability per
        Q-B3-4 + Amendment D.

        Renamed from B.1's `_emit_degraded_signal_span` since on Letta
        side this is per-hit emission (NOT rare-path) — Letta `Result`
        type carries no native `score` field, so default-1.0 synthesis
        fires on every query() hit. NOT on AP-6 promote canonical
        5-attribute set; adapter-private per Q-B3-4.
        """
        with _tracer.start_as_current_span(
            "verdaca.port.memory.confidence_synthesis"
        ) as span:
            span.set_attribute("verdaca.memory.hit_id", hit_id)
            span.set_attribute("verdaca.memory.confidence_synthesis", synthesis)


__all__ = ["LettaAdapter"]
