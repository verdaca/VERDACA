"""Memory port contract tests — 18 MAC-Ts.

Per `test-strategy.md` v0.2 §2.2.1 — 18 binding `M-T-MEM-*` MAC-Ts. Each
test below embeds its MAC-T ID in the function name (UPPER_CASE per
sibling-precedent at test_versioned_state_contract.py:83 +
test_serialization_contract.py:113); docstrings quote the §2.2.1
assertion language verbatim for auditability.

Discipline (per Stage 9.4.3 Phase B.3 hand-off):
- Stay strictly within the 18-ID scope. No 19th test, no parametric
  expansion beyond [mem0, letta], no opportunistic coverage.
- Test the public `MemoryPort` Protocol surface via the adapter — both
  adapters parametrically per ADR-9.2-V1 dual-adapter mandate. Two
  cross-adapter shadow-query tests (M-T-MEM-QUERY-03 set-equality,
  M-T-MEM-QUERY-04 cardinality-drift) consume both adapters in a single
  test function (NOT parametrized — they ASSERT cross-adapter parity).
- `@pytest.mark.no_waiver` ONLY on M-T-MEM-PROMO-01..04 per ratified
  allow-list entries #17–#20 (`test-strategy.md` v0.2 §6.1 lines
  465–468). NEVER on any other test (per
  feedback_no_waiver_discipline.md) regardless of how "non-waivable"
  the assertion language sounds.
- M-T-MEM-QUERY-04 (cardinality drift) is Tier 4 per
  `test-strategy.md` v0.2 §3.1 row 308 — Drift Monitor, weekly cron,
  non-blocking, alerts-only. No formal Memory-port Tier 4 marker is
  minted in §3.2 / §5.3 (gap surfaced in B.3 close memo for next
  ratification cycle); coverage is doc-only via this docstring + the
  test-function docstring.
- M-T-MEM-CORRELATION-01 requires LLM Proxy port (Stage 9.4.5
  prerequisite); body is `pytest.skip(...)` per `test-strategy.md`
  v0.2 §7.2 skip-template (verbatim substrings "documented
  degradation" + "ADR-4 §6 substitute-readiness").
- M-T-MEM-MIGRATE-02 (AP-8 two-window cross-adapter substitution) is
  stub-skip per the same §7.2 template (substitute-readiness scope).

Adapter test-mode construction (per Q-B3-2 + Q-B3-3 dispositions):
hand-written stateful fake clients inline (NOT MagicMock) — upstream
state must persist across adapter-instance lifecycle for PROMO-02
durability/reconciliation semantics.

Runner invocation contract (per Q-B3 advisor disposition GO Option α):
workspace .venv lacks `mem0ai` + `letta-client` pending Cleo 9.6
workspace registration (per B.1 close 34a4eca + B.2 close b14285b
commit bodies). Pre-Cleo invocation:

    uv run --with mem0ai==1.0.11 --with 'letta-client>=1.10,<2.0' \\
           --no-project pytest \\
           tests/src/praxis/contract_tests/ports/test_memory_contract.py -v

Post-Cleo (workspace registration landed): naked `pytest` works.
Probe 10 (workspace-pytest collection) carried forward in B.3 close
memo + commit body alongside Probes 1/2/3/7/8/9.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from letta_client import APIConnectionError
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pydantic import ValidationError

from praxis.adapters.letta import LettaAdapter
from praxis.adapters.letta import adapter as _letta_mod
from praxis.adapters.mem0 import Mem0Adapter
from praxis.adapters.mem0 import adapter as _mem0_mod
from praxis.ports.common import ContractViolation, UpstreamUnavailable
from praxis.ports.memory import (
    MemoryEntry,
    MemoryHit,
    MemoryPort,
    MemoryQuery,
    MigrationReport,
    PromotedMemory,
    PromotionContractViolation,
    PromotionRationale,
    PromotionTier,
    RevokedPromotion,
    StoredMemory,
)

_TEST_CORRELATION_ID = "test-correlation-mem-contract"
_LETTA_TEST_AGENT_ID = "test-singleton-agent"

# Mem0 sidecar partition (mirrors adapter constants — kept inline so the
# test file does not import `praxis.adapters.mem0.adapter` private names).
_MEM0_USER_ID_DEFAULT = "verdaca.system.user"
_MEM0_SIDECAR_USER_ID = "verdaca.system.idempotency"
_MEM0_TIER_KEY = "verdaca.tier"
_MEM0_PROMOTION_ID_KEY = "verdaca.promotion_id"
_MEM0_SCHEMA_VERSION_KEY = "verdaca.schema_version"
_MEM0_IDEMPOTENCY_KIND_KEY = "verdaca.idempotency.kind"
_MEM0_IDEMPOTENCY_OPERATION_KEY = "verdaca.idempotency.operation"
_MEM0_IDEMPOTENCY_KEY_KEY = "verdaca.idempotency.key"
_MEM0_IDEMPOTENCY_PAYLOAD_HASH_KEY = "verdaca.idempotency.payload_hash"

# Letta discriminator-tag literals (mirror adapter; kept inline).
_LETTA_KIND_USER = "verdaca.kind=user:str"
_LETTA_KIND_PROMOTION_STATE = "verdaca.kind=promotion_state:str"
_LETTA_KIND_IDEMPOTENCY = "verdaca.kind=idempotency:str"
_LETTA_TAG_TIER_PREFIX = "verdaca.tier="
_LETTA_TAG_SCHEMA_VERSION_PREFIX = "verdaca.schema_version="


# ---------------------------------------------------------------------------
# §1. Q-B3-19 disposition — letta_client.APIConnectionError ctor:
#     `(*, message: str = "Connection error.", request: httpx.Request)`
#     `request` is REQUIRED kw-only. Construct with a minimal httpx.Request
#     to satisfy the signature.
# ---------------------------------------------------------------------------


def _fake_letta_connection_error() -> APIConnectionError:
    """Build a real `letta_client.APIConnectionError` instance for the
    fake's `health()` failure path. Q-B3-19 ladder: signature confirmed
    `(*, message=..., request=httpx.Request)` so we MUST pass an
    httpx.Request; positional / no-arg variants would TypeError."""
    request = httpx.Request("GET", "http://fake-letta-down/")
    return APIConnectionError(message="fake-letta-down", request=request)


# ---------------------------------------------------------------------------
# §2. Mem0 stateful fake — duck-typed (Q-B3-15 LOCKED). Implements the
# subset of `mem0.Memory` surface that Mem0Adapter actually calls.
# ---------------------------------------------------------------------------


class _FakeMem0Memory:
    """Stateful fake of `mem0.Memory` driving Mem0Adapter through its full
    surface (store / query / promote / revoke / migrate + AP-5 sidecar
    INTENT/SUCCESS reconciliation). State persists across adapter-instance
    lifecycle so PROMO-02 two-instance pattern works."""

    def __init__(self, *, fail_health: bool = False) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._counter = 0
        self._fail_health = fail_health
        self.closed = False

    # --- record helpers (test-only, not part of Memory surface) ------------

    def _new_id(self) -> str:
        self._counter += 1
        return f"mem-{self._counter}"

    def seed(
        self,
        *,
        user_id: str,
        memory: str,
        metadata: dict[str, Any] | None = None,
        score: float = 0.85,
    ) -> str:
        memory_id = self._new_id()
        self._records[memory_id] = {
            "id": memory_id,
            "memory": memory,
            "metadata": dict(metadata or {}),
            "user_id": user_id,
            "score": score,
        }
        return memory_id

    # --- Memory-surface methods --------------------------------------------

    def add(
        self,
        messages: Any = None,
        *,
        metadata: dict[str, Any] | None = None,
        user_id: str,
        infer: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        memory_id = self._new_id()
        content = ""
        if isinstance(messages, list) and messages:
            first = messages[0]
            if isinstance(first, dict):
                content = first.get("content", "") or ""
        self._records[memory_id] = {
            "id": memory_id,
            "memory": content,
            "metadata": dict(metadata or {}),
            "user_id": user_id,
            "score": 0.85,
        }
        return {"results": [{"id": memory_id, "memory": content}]}

    def search(
        self,
        query: str = "",
        *,
        user_id: str,
        limit: int | None = None,
        filters: Any = None,
        **_: Any,
    ) -> dict[str, Any]:
        if self._fail_health:
            raise RuntimeError("fake-mem0-down")
        rows = [
            dict(r)
            for r in self._records.values()
            if r["user_id"] == user_id
        ]
        if limit is not None:
            rows = rows[:limit]
        return {"results": rows}

    def get(self, *, memory_id: str, **_: Any) -> dict[str, Any]:
        if memory_id not in self._records:
            return {"id": memory_id, "memory": "", "metadata": {}}
        return dict(self._records[memory_id])

    def update(
        self,
        *,
        memory_id: str,
        data: str,
        metadata: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        if memory_id in self._records:
            self._records[memory_id]["memory"] = data
            if metadata is not None:
                self._records[memory_id]["metadata"] = dict(metadata)
        return {"id": memory_id}

    def get_all(
        self,
        *,
        user_id: str,
        filters: Any = None,
        **_: Any,
    ) -> dict[str, Any]:
        if self._fail_health:
            raise RuntimeError("fake-mem0-down")
        return {
            "results": [
                dict(r)
                for r in self._records.values()
                if r["user_id"] == user_id
            ]
        }

    def delete(self, *, memory_id: str, **_: Any) -> None:
        self._records.pop(memory_id, None)

    def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# §3. Letta stateful fake — duck-typed (Q-B3-15 LOCKED). Implements the
# subset of `letta_client.Letta` surface that LettaAdapter actually calls.
# ---------------------------------------------------------------------------


@dataclass
class _FakePassage:
    """Mirrors letta_client passage shape used by the adapter (id / text /
    tags). NOTE: NO `score` field — Discovery 1 (B.2 close b14285b)."""

    id: str
    text: str
    tags: list[str] = field(default_factory=list)


@dataclass
class _FakeResult:
    """Mirrors `Result` from `types.agents.passage_search_response.Result`.
    Carries `id / content / tags` ONLY — Discovery 1 (no native `score`)."""

    id: str
    content: str
    tags: list[str] = field(default_factory=list)


@dataclass
class _FakePassageSearchResponse:
    """Mirrors `PassageSearchResponse(count: int, results: List[Result])`."""

    count: int
    results: list[_FakeResult]


class _FakeLettaPassagesNamespace:
    def __init__(self, store: dict[str, list[_FakePassage]]) -> None:
        self._store = store
        self._counter = 0
        self.cardinality_override: int | None = None  # Amendment E knob (test only)

    def _new_id(self) -> str:
        self._counter += 1
        return f"passage-{self._counter}"

    def create(
        self,
        *,
        agent_id: str,
        text: str,
        tags: list[str] | None = None,
    ) -> list[_FakePassage]:
        n = self.cardinality_override if self.cardinality_override is not None else 1
        if n == 0:
            return []
        out: list[_FakePassage] = []
        for _ in range(n):
            p = _FakePassage(id=self._new_id(), text=text, tags=list(tags or []))
            self._store.setdefault(agent_id, []).append(p)
            out.append(p)
        return out

    def search(
        self,
        *,
        agent_id: str,
        query: str,
        top_k: int,
    ) -> _FakePassageSearchResponse:
        # Realistic semantic-search approximation: real Letta ranks
        # passages by content-relevance against the query embedding.
        # AP-5 + Amendment C sidecar passages carry discriminator tags
        # (verdaca.kind=idempotency / =promotion_state) — semantically
        # distinct from user content (verdaca.kind=user). Rank user
        # passages above sidecars; stable within each bucket. The
        # adapter's Amendment A tag-filter still drops any sidecar
        # that lands inside top_k, but with this ranking the top_k
        # cap reaches user content first.
        sidecar_kinds = (
            "verdaca.kind=promotion_state:str",
            "verdaca.kind=idempotency:str",
        )
        def _is_sidecar(p: _FakePassage) -> bool:
            return any(t in (p.tags or []) for t in sidecar_kinds)
        all_passages = self._store.get(agent_id, [])
        ranked = sorted(
            enumerate(all_passages),
            key=lambda iv: (_is_sidecar(iv[1]), iv[0]),
        )
        results = [
            _FakeResult(id=p.id, content=p.text, tags=list(p.tags))
            for _, p in ranked[:top_k]
        ]
        return _FakePassageSearchResponse(count=len(results), results=results)

    def list(
        self,
        *,
        agent_id: str,
        limit: int = 100,
        after: str | None = None,
    ) -> list[_FakePassage]:
        page = self._store.get(agent_id, [])
        if after is not None:
            for i, p in enumerate(page):
                if p.id == after:
                    page = page[i + 1 :]
                    break
            else:
                page = []
        return list(page[:limit])

    def delete(self, *, memory_id: str, agent_id: str) -> None:
        bucket = self._store.get(agent_id, [])
        self._store[agent_id] = [p for p in bucket if p.id != memory_id]


class _FakeLettaAgentsNamespace:
    def __init__(self, store: dict[str, list[_FakePassage]]) -> None:
        self.passages = _FakeLettaPassagesNamespace(store)

    def list(self, *, name: str | None = None) -> list[Any]:
        return []  # singleton-agent path bypassed via explicit ctor kwarg

    def create(self, *, name: str, model: str | None = None, **_: Any) -> Any:
        raise AssertionError(
            "agents.create should not fire under explicit system_agent_id"
        )


class _FakeLetta:
    """Stateful fake of `letta_client.Letta` driving LettaAdapter through
    its full surface (health / agents / passages CRUD)."""

    def __init__(self, *, fail_health: bool = False) -> None:
        self._store: dict[str, list[_FakePassage]] = {}
        self._fail_health = fail_health
        self.agents = _FakeLettaAgentsNamespace(self._store)
        self.closed = False

    def health(self) -> None:
        if self._fail_health:
            raise _fake_letta_connection_error()

    def close(self) -> None:
        self.closed = True

    # --- helpers (test-only) ----------------------------------------------

    def seed_passage(
        self,
        *,
        agent_id: str,
        text: str,
        tags: list[str] | None = None,
    ) -> str:
        return self.agents.passages.create(
            agent_id=agent_id, text=text, tags=list(tags or [])
        )[0].id


# ---------------------------------------------------------------------------
# §4. Adapter factories — used by parametric fixture + PROMO-02 manual
# parametrize. Adapter is constructed but on_init is NOT auto-called by
# factories — callers decide (UNAVAIL-01 needs construct-without-init;
# the parametric `adapter` fixture calls on_init after construct).
# ---------------------------------------------------------------------------


def _make_mem0_adapter(
    *,
    fake: _FakeMem0Memory | None = None,
    fail_health: bool = False,
) -> tuple[_FakeMem0Memory, Mem0Adapter]:
    fake = fake if fake is not None else _FakeMem0Memory(fail_health=fail_health)
    adp = Mem0Adapter(
        mem0_client=fake,  # type: ignore[arg-type]
        default_correlation_id=_TEST_CORRELATION_ID,
    )
    return fake, adp


def _make_letta_adapter(
    *,
    fake: _FakeLetta | None = None,
    fail_health: bool = False,
) -> tuple[_FakeLetta, LettaAdapter]:
    fake = fake if fake is not None else _FakeLetta(fail_health=fail_health)
    adp = LettaAdapter(
        letta_client=fake,  # type: ignore[arg-type]
        system_agent_id=_LETTA_TEST_AGENT_ID,  # bypass auto-create probe path
        default_correlation_id=_TEST_CORRELATION_ID,
    )
    return fake, adp


# ---------------------------------------------------------------------------
# §5. otel_capture fixture (Q-B3-5 + Q-B3-18). Uses InMemorySpanExporter
# behind a fresh TracerProvider; rebinds module-level `_tracer` references
# in both adapter modules as a belt-and-braces fallback against
# proxy-redirect failure.
# ---------------------------------------------------------------------------


@pytest.fixture
def otel_capture() -> Iterator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    prior_provider = otel_trace.get_tracer_provider()
    prior_mem0_tracer = _mem0_mod._tracer
    prior_letta_tracer = _letta_mod._tracer
    otel_trace.set_tracer_provider(provider)
    # Q-B3-18 belt-and-braces: explicitly rebind module-level _tracer
    # references in case _ProxyTracer caching defeats provider redirect.
    _mem0_mod._tracer = provider.get_tracer(_mem0_mod.__name__)
    _letta_mod._tracer = provider.get_tracer(_letta_mod.__name__)
    try:
        yield exporter
    finally:
        _mem0_mod._tracer = prior_mem0_tracer
        _letta_mod._tracer = prior_letta_tracer
        otel_trace.set_tracer_provider(prior_provider)
        exporter.clear()


# ---------------------------------------------------------------------------
# §6. Parametric adapter fixture — yields a constructed + on_init-ed
# adapter for the 14 parametric tests. PROMO-02 + UNAVAIL-01 manage their
# own adapter lifecycle and do NOT use this fixture.
# ---------------------------------------------------------------------------


@pytest.fixture(params=["mem0", "letta"], ids=["mem0", "letta"])
def adapter(request: pytest.FixtureRequest) -> Iterator[MemoryPort]:
    if request.param == "mem0":
        fake, adp = _make_mem0_adapter()
    else:
        fake, adp = _make_letta_adapter()
    adp.on_init()
    yield adp
    adp.on_shutdown()


# ---------------------------------------------------------------------------
# §7. Test-only payload constructor (sibling pattern from VS:50–72 / SER:60–102).
# ---------------------------------------------------------------------------


def _entry(
    content: str = "test-content",
    *,
    idempotency_key: str = "test-key",
    metadata: dict[str, Any] | None = None,
    confidence: float = 0.9,
    schema_version: int = 1,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> MemoryEntry:
    return MemoryEntry(
        schema_version=schema_version,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        content=content,
        metadata=metadata if metadata is not None else {"source": "test"},
        confidence=confidence,
        source_span_id="test-span-1",
    )


def _query(query_text: str = "", *, k: int = 10) -> MemoryQuery:
    return MemoryQuery(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        idempotency_key=None,
        query_text=query_text,
        k=k,
    )


def _rationale(
    *,
    threshold_met: float = 0.9,
    threshold_required: float = 0.75,
    idempotency_key: str = "test-promo-key",
    correlation_id: str = _TEST_CORRELATION_ID,
) -> PromotionRationale:
    return PromotionRationale(
        schema_version=1,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        threshold_met=threshold_met,
        threshold_required=threshold_required,
        promoting_actor="test-actor",
        evidence_span_ids=["evidence-span-1"],
    )


# ===========================================================================
# §2.2.1 MAC-Ts — 18 tests (4 PROMO with @pytest.mark.no_waiver + 14 others)
# ===========================================================================


# ---------------------------------------------------------------------------
# 1. M-T-MEM-PROMO-01 — allow-list entry #17 (PS-1 confidence-threshold)
# ---------------------------------------------------------------------------
@pytest.mark.no_waiver  # entry #17 — PromotionContractViolation (test-strategy.md v0.2 §6.1 line 465)
def test_M_T_MEM_PROMO_01_threshold_violation(adapter: MemoryPort) -> None:
    """`promote()` with adversarial `threshold_met=0.4 < threshold_required=0.75`
    — `pytest.raises(PromotionContractViolation)`; exception carries
    `requested_threshold=0.75` and `actual_confidence=0.4`. Adapter MUST
    raise before any upstream call. Verbatim per requirements.md §6.3."""
    rat = _rationale(threshold_met=0.4, threshold_required=0.75, idempotency_key="promo-01")
    with pytest.raises(PromotionContractViolation) as exc_info:
        adapter.promote(
            hit_id="hit-irrelevant",
            target_tier=PromotionTier.SESSION,
            rationale=rat,
        )
    assert exc_info.value.requested_threshold == 0.75
    assert exc_info.value.actual_confidence == 0.4


# ---------------------------------------------------------------------------
# 2. M-T-MEM-PROMO-02 — allow-list entry #18 (PS-2 idempotent + durability)
# ---------------------------------------------------------------------------
# Q-B3-16 LOCKED: parametrize-on-function (NOT via fixture) keeps no_waiver
# count == 4 invariant intact. Test owns adapter-instance lifecycle to
# implement Q-B3-3 two-instance pattern (instance A → discard → instance B
# reconciles via on_init AP-5 → assert same promotion_id).
@pytest.mark.no_waiver  # entry #18 — PS-2 idempotent-promotion durability (test-strategy.md v0.2 §6.1 line 466)
@pytest.mark.parametrize("substrate", ["mem0", "letta"])
def test_M_T_MEM_PROMO_02_idempotent_promotion_durable(substrate: str) -> None:
    """Two `promote(hit_id, target_tier, rationale)` calls with same
    `idempotency_key`; second after adapter crash — Both return same
    `PromotedMemory.promotion_id`; exactly one promotion record;
    idempotency cache is durable (fsync'd) OR adapter re-reconciles via
    upstream read on startup. Verbatim per port-contracts.md v0.2 §3.4 PS-2."""
    if substrate == "mem0":
        fake_a = _FakeMem0Memory()
        _, adp_a = _make_mem0_adapter(fake=fake_a)
        adp_a.on_init()
        # Seed a hit to promote.
        hit_id = fake_a.seed(
            user_id=_MEM0_USER_ID_DEFAULT,
            memory="seed-content",
            metadata={_MEM0_TIER_KEY: "working"},
        )
        rat = _rationale(idempotency_key="promo-02-mem0")
        first = adp_a.promote(hit_id=hit_id, target_tier=PromotionTier.SESSION, rationale=rat)
        # Discard adapter A; construct adapter B against same upstream fake.
        del adp_a
        _, adp_b = _make_mem0_adapter(fake=fake_a)
        adp_b.on_init()  # AP-5 reconciliation rehydrates from sidecar.
        second = adp_b.promote(hit_id=hit_id, target_tier=PromotionTier.SESSION, rationale=rat)
        assert first.promotion_id == second.promotion_id
        # Exactly one promotion record (hit's metadata carries one promotion_id).
        promoted = [
            r for r in fake_a._records.values()
            if (r.get("metadata") or {}).get(_MEM0_PROMOTION_ID_KEY) == first.promotion_id
        ]
        assert len(promoted) == 1
    else:
        fake_a = _FakeLetta()
        _, adp_a = _make_letta_adapter(fake=fake_a)
        adp_a.on_init()
        # Seed a user passage to promote.
        hit_id = fake_a.seed_passage(
            agent_id=_LETTA_TEST_AGENT_ID,
            text="seed-content",
            tags=[_LETTA_KIND_USER, "verdaca.tier=working:str"],
        )
        rat = _rationale(idempotency_key="promo-02-letta")
        first = adp_a.promote(hit_id=hit_id, target_tier=PromotionTier.SESSION, rationale=rat)
        # Discard adapter A; construct adapter B against same upstream fake.
        del adp_a
        _, adp_b = _make_letta_adapter(fake=fake_a)
        adp_b.on_init()  # AP-5 + Amendment C rehydrate.
        second = adp_b.promote(hit_id=hit_id, target_tier=PromotionTier.SESSION, rationale=rat)
        assert first.promotion_id == second.promotion_id
        # Exactly one promotion-state sidecar passage for this hit.
        promo_state = [
            p for p in fake_a._store.get(_LETTA_TEST_AGENT_ID, [])
            if _LETTA_KIND_PROMOTION_STATE in (p.tags or [])
            and f"verdaca.promotion_state.promotion_id={first.promotion_id}:str"
            in (p.tags or [])
        ]
        assert len(promo_state) == 1


# ---------------------------------------------------------------------------
# 3. M-T-MEM-PROMO-03 — allow-list entry #19 (AP-6 5-attribute set-equality)
# ---------------------------------------------------------------------------
@pytest.mark.no_waiver  # entry #19 — AP-6 SpanAttributeContract (test-strategy.md v0.2 §6.1 line 467)
def test_M_T_MEM_PROMO_03_otel_span_attribute_set(
    adapter: MemoryPort,
    otel_capture: InMemorySpanExporter,
) -> None:
    """`promote()` succeeds; fake OTEL exporter captures emitted span —
    `span.attributes == {verdaca.memory.hit_id, verdaca.memory.tier_from,
    verdaca.memory.tier_to, verdaca.memory.threshold_met,
    verdaca.memory.threshold_required}` — set equality, not subset.
    Missing any attribute → `ContractViolation`. Extra attribute outside
    set → non-conformant. Assertion is `span.attributes ==
    expected_attribute_set`, NOT `span.emit.called == True`. Verbatim
    AP-6 SpanAttributeContract per requirements.md §6.2.

    Q-B3-4 LOCKED adapter-private (per 34a4eca + b14285b Amendment D):
    `verdaca.memory.confidence_synthesis` lives on a SEPARATE
    adapter-private span (`verdaca.port.memory.confidence_synthesis`)
    and DOES NOT belong to the PROMOTE span attribute set. PROMO-03
    set-equality holds verbatim."""
    stored = adapter.store(_entry("promo-03-content", idempotency_key="store-promo-03"))
    rat = _rationale(idempotency_key="promo-03-promote")
    adapter.promote(hit_id=stored.stored_id, target_tier=PromotionTier.SESSION, rationale=rat)
    spans = [
        s for s in otel_capture.get_finished_spans()
        if s.name == "verdaca.port.memory.promote"
    ]
    assert len(spans) == 1, f"expected exactly 1 promote span, got {len(spans)}"
    expected = {
        "verdaca.memory.hit_id",
        "verdaca.memory.tier_from",
        "verdaca.memory.tier_to",
        "verdaca.memory.threshold_met",
        "verdaca.memory.threshold_required",
    }
    assert set(spans[0].attributes.keys()) == expected


# ---------------------------------------------------------------------------
# 4. M-T-MEM-PROMO-04 — allow-list entry #20 (PS-4 SLO; mocked-trivial)
# ---------------------------------------------------------------------------
@pytest.mark.no_waiver  # entry #20 — PS-4 time-bounded revocation (test-strategy.md v0.2 §6.1 line 468)
def test_M_T_MEM_PROMO_04_revocation_slo(adapter: MemoryPort) -> None:
    """`promote(target_tier=SESSION)` succeeds; then `revoke_promotion()`;
    wait 30s SLO window — Post-wait `query()` asserts (a) revoked hit
    absent from result OR (b) `PromotionRevocationFailed` raised during
    the window. Tier-specific SLOs: working ≤ 1s, session ≤ 30s,
    promoted ≤ tier-specific session. Verbatim per requirements.md §6.4.

    Q-B3-6 LOCKED mocked-trivial: in-fake mode, upstream has no
    propagation delay — post-revoke query reflects the revocation
    immediately. NO time.sleep(30). Real-time SLO observation defers
    to live-server (Probe ledger entry — Stage 9.4.5 / 9.6 orchestration)."""
    stored = adapter.store(_entry("promo-04-content", idempotency_key="store-promo-04"))
    rat = _rationale(idempotency_key="promo-04-promote")
    promoted = adapter.promote(
        hit_id=stored.stored_id, target_tier=PromotionTier.SESSION, rationale=rat
    )
    revoked = adapter.revoke_promotion(promotion_id=promoted.promotion_id, reason="test-reason")
    assert isinstance(revoked, RevokedPromotion)
    assert revoked.promotion_id == promoted.promotion_id
    # Post-revoke query — assert no hit returned at SESSION tier for the
    # revoked promotion (revocation observable per PS-4).
    hits = adapter.query(_query("", k=50))
    for h in hits:
        if h.hit_id == stored.stored_id:
            assert h.tier == "working"


# ---------------------------------------------------------------------------
# 5. M-T-MEM-STORE-01 — store happy
# ---------------------------------------------------------------------------
def test_M_T_MEM_STORE_01_store_happy(adapter: MemoryPort) -> None:
    """`store(entry)` with valid `MemoryEntry` (primitive-only metadata) —
    Returns `StoredMemory`; `extra="forbid"` accepts; adapter
    idempotency_key-indexed."""
    entry = _entry("hello", idempotency_key="store-01-key")
    result = adapter.store(entry)
    assert isinstance(result, StoredMemory)
    assert result.idempotency_key == "store-01-key"
    # Idempotency_key-indexed: re-call with same entry returns same
    # stored_id (AP-5 dedup).
    again = adapter.store(entry)
    assert again.stored_id == result.stored_id


# ---------------------------------------------------------------------------
# 6. M-T-MEM-STORE-02 — DTO-boundary rejection (FM-03 nested metadata)
# ---------------------------------------------------------------------------
def test_M_T_MEM_STORE_02_dto_rejects_nested_metadata() -> None:
    """`store(entry)` with nested-object metadata (FM-03 adversarial) —
    `extra="forbid"` rejects at DTO boundary; `ContractViolation`.

    Q-B3-17 LOCKED bridge: §2.2.1 row 142's "ContractViolation" wording
    refers to the DTO-boundary contract failure semantic class. Pydantic
    v2 enforces `MemoryEntry.metadata: dict[str, str | int | float | bool]`
    typing at constructor; nested-object input raises
    `pydantic.ValidationError`, NOT `praxis.ports.common.ContractViolation`.
    Surface as test-strategy vocabulary-clarity gap in B.3 close memo
    for next ratification cycle."""
    with pytest.raises(ValidationError):
        MemoryEntry(
            schema_version=1,
            correlation_id=_TEST_CORRELATION_ID,
            idempotency_key="store-02-key",
            content="adversarial",
            metadata={"nested": {"object": "not-allowed"}},  # type: ignore[dict-item]
            confidence=0.9,
            source_span_id="span",
        )


# ---------------------------------------------------------------------------
# 7. M-T-MEM-QUERY-01 — query happy + Amendment A sidecar-filter coverage
# ---------------------------------------------------------------------------
def test_M_T_MEM_QUERY_01_top_k_confidence_range(
    adapter: MemoryPort,
    request: pytest.FixtureRequest,
) -> None:
    """`query(q)` returns top-K `MemoryHit` — Returns `Sequence[MemoryHit]`;
    all `0.0 <= hit.confidence <= 1.0` (F-011 probe on N=50 sample per
    requirements.md §6.6).

    Q-B3-11 Amendment A coverage (Letta-side): the underlying singleton
    agent contains 2 sidecar passages (`verdaca.kind=promotion_state:str`
    + `verdaca.kind=idempotency:str`) — assert filter EXCLUDES them.
    Mem0-side asymmetry: Mem0 partitions sidecars via user_id (separate
    upstream partition), so query() against the user-memory user_id
    cannot return sidecars by construction; test seeds user-partition
    only and asserts the same range invariant. Partial-closes Probe 8
    in mocked-mode."""
    # Seed corpus.
    for i in range(5):
        adapter.store(_entry(f"content-{i}", idempotency_key=f"query01-{i}"))
    # Letta-only: directly inject sidecar-tagged passages onto the
    # singleton agent to exercise Amendment A filter at query() boundary.
    if request.node.callspec.id == "letta":
        # Reach in via pytest-fixturerequest: get the live fake. We
        # constructed via _make_letta_adapter so the fake is the
        # adapter._letta attribute (the only handle).
        letta_fake = adapter._letta  # type: ignore[attr-defined]
        letta_fake.seed_passage(
            agent_id=_LETTA_TEST_AGENT_ID,
            text="sidecar-promotion-state",
            tags=[_LETTA_KIND_PROMOTION_STATE],
        )
        letta_fake.seed_passage(
            agent_id=_LETTA_TEST_AGENT_ID,
            text="sidecar-idempotency",
            tags=[_LETTA_KIND_IDEMPOTENCY],
        )
    hits = adapter.query(_query("anything", k=50))
    assert isinstance(hits, list) or hasattr(hits, "__iter__")
    contents = {h.content for h in hits}
    # Sidecar passages must NOT appear (Amendment A on Letta;
    # vacuously holds on Mem0).
    assert "sidecar-promotion-state" not in contents
    assert "sidecar-idempotency" not in contents
    for h in hits:
        assert isinstance(h, MemoryHit)
        assert 0.0 <= h.confidence <= 1.0


# ---------------------------------------------------------------------------
# 8. M-T-MEM-QUERY-02 — tier normalization (AP-3)
# ---------------------------------------------------------------------------
def test_M_T_MEM_QUERY_02_tier_normalization(
    adapter: MemoryPort,
    request: pytest.FixtureRequest,
) -> None:
    """`query(q)` against adapter whose upstream uses native tier labels
    (e.g., `short_term`, `long_term`, `core`) — All returned
    `MemoryHit.tier` values ∈ `{"working","session","promoted"}`; unmapped
    upstream tier raises `ContractViolation` at adapter boundary. AP-3
    TierNormalizer-verified."""
    if request.node.callspec.id == "mem0":
        # Inject native upstream tier label via Mem0 metadata.
        mem0_fake: _FakeMem0Memory = adapter._mem0  # type: ignore[attr-defined]
        mem0_fake.seed(
            user_id=_MEM0_USER_ID_DEFAULT,
            memory="native-tier-content",
            metadata={_MEM0_TIER_KEY: "short_term"},  # unmapped per Letta SDK survey native-tier vocab
        )
    else:
        letta_fake: _FakeLetta = adapter._letta  # type: ignore[attr-defined]
        letta_fake.seed_passage(
            agent_id=_LETTA_TEST_AGENT_ID,
            text="native-tier-content",
            tags=[_LETTA_KIND_USER, "verdaca.tier=core:str"],
        )
    with pytest.raises(ContractViolation):
        adapter.query(_query("native", k=10))


# ---------------------------------------------------------------------------
# 9. M-T-MEM-QUERY-03 — cross-adapter set-equality (NOT parametric)
# ---------------------------------------------------------------------------
def test_M_T_MEM_QUERY_03_set_equality_across_adapters() -> None:
    """Shadow-query both Mem0 + Letta adapters against same corpus —
    Conformance asserts **set equality** on top-K, NOT ordering equality.
    Documents ordering non-guarantee per FM-05.

    Cross-adapter parity assertion — does NOT parametrize over
    [mem0, letta]; consumes both adapters in a single test function."""
    _, mem0 = _make_mem0_adapter()
    _, letta = _make_letta_adapter()
    mem0.on_init()
    letta.on_init()
    try:
        corpus = ["alpha", "beta", "gamma", "delta", "epsilon"]
        for i, c in enumerate(corpus):
            mem0.store(_entry(c, idempotency_key=f"q3-mem0-{i}"))
            letta.store(_entry(c, idempotency_key=f"q3-letta-{i}"))
        mem0_hits = mem0.query(_query("any", k=10))
        letta_hits = letta.query(_query("any", k=10))
        # Set-equality on content (hit_id will differ across adapters).
        assert {h.content for h in mem0_hits} == {h.content for h in letta_hits}
    finally:
        mem0.on_shutdown()
        letta.on_shutdown()


# ---------------------------------------------------------------------------
# 10. M-T-MEM-QUERY-04 — cross-adapter cardinality drift (Tier 4 — doc-only)
# ---------------------------------------------------------------------------
# Tier 4 per test-strategy.md v0.2 §3.1 row 308 — Drift Monitor
# (weekly cron, non-blocking, alerts-only). No formal Memory-port
# Tier 4 marker minted in §3.2 / §5.3 — coverage doc-only. Q-B3-7 GAP.
def test_M_T_MEM_QUERY_04_cardinality_drift_across_adapters() -> None:
    """Shadow-query both adapters nightly; compare top-K cardinality —
    Alert if cardinality delta >10% on fixed query set. V-5 observability
    signal.

    Tier 4 (Drift Monitor) per test-strategy.md v0.2 §3.1 row 308 —
    weekly cron, non-blocking. Cross-adapter parity assertion; does NOT
    parametrize over [mem0, letta]."""
    _, mem0 = _make_mem0_adapter()
    _, letta = _make_letta_adapter()
    mem0.on_init()
    letta.on_init()
    try:
        for i in range(10):
            mem0.store(_entry(f"drift-{i}", idempotency_key=f"q4-mem0-{i}"))
            letta.store(_entry(f"drift-{i}", idempotency_key=f"q4-letta-{i}"))
        mem0_hits = list(mem0.query(_query("any", k=10)))
        letta_hits = list(letta.query(_query("any", k=10)))
        max_card = max(len(mem0_hits), len(letta_hits), 1)
        drift = abs(len(mem0_hits) - len(letta_hits)) / max_card
        assert drift <= 0.10, f"cross-adapter cardinality drift {drift:.2%} > 10%"
    finally:
        mem0.on_shutdown()
        letta.on_shutdown()


# ---------------------------------------------------------------------------
# 11. M-T-MEM-MIGRATE-01 — migrate happy
# ---------------------------------------------------------------------------
def test_M_T_MEM_MIGRATE_01_migrate_happy(request: pytest.FixtureRequest) -> None:
    """`migrate(from_version=N, to_version=N+1)` — Returns `MigrationReport`;
    no data loss; migrator_signature stable.

    Constructs adapter directly with a migrator registry per Q-MIGRATE-1
    M.1 disposition (adapter-internal registry, no Protocol-level migrator
    parameter)."""
    # Parametrize manually since the standard `adapter` fixture
    # constructs without migrators=. Two iterations.
    for substrate in ("mem0", "letta"):
        if substrate == "mem0":
            fake = _FakeMem0Memory()

            def mem0_migrator(entry: dict) -> dict:
                meta = dict(entry.get("metadata") or {})
                meta[_MEM0_SCHEMA_VERSION_KEY] = 2
                return {"memory": entry.get("memory", ""), "metadata": meta}

            adp = Mem0Adapter(
                mem0_client=fake,  # type: ignore[arg-type]
                migrators={(1, 2): mem0_migrator},
                default_correlation_id=_TEST_CORRELATION_ID,
            )
            adp.on_init()
            adp.store(_entry("migrate-mem0-content", idempotency_key="mig-01-mem0",
                             schema_version=1))
            # Adapter store stamps verdaca.schema_version=1 (entry.schema_version);
            # migrate(1, 2) finds it.
            report = adp.migrate(from_version=1, to_version=2)
            adp.on_shutdown()
        else:
            fake = _FakeLetta()

            def letta_migrator(entry: dict) -> dict:
                tags = list(entry.get("tags") or [])
                tags = [
                    t for t in tags
                    if not t.startswith(_LETTA_TAG_SCHEMA_VERSION_PREFIX)
                ]
                tags.append("verdaca.schema_version=2:int")
                return {"text": entry.get("text", ""), "tags": tags}

            adp = LettaAdapter(
                letta_client=fake,  # type: ignore[arg-type]
                system_agent_id=_LETTA_TEST_AGENT_ID,
                migrators={(1, 2): letta_migrator},
                default_correlation_id=_TEST_CORRELATION_ID,
            )
            adp.on_init()
            adp.store(_entry("migrate-letta-content", idempotency_key="mig-01-letta",
                             schema_version=1))
            report = adp.migrate(from_version=1, to_version=2)
            adp.on_shutdown()
        assert isinstance(report, MigrationReport)
        assert report.from_version == 1
        assert report.to_version == 2
        assert report.entries_migrated >= 1
        assert isinstance(report.migrator_signature, str)
        assert len(report.migrator_signature) == 64  # sha256 hex


# ---------------------------------------------------------------------------
# 12. M-T-MEM-MIGRATE-02 — AP-8 two-window cross-adapter substitute (stub-skip per §7.2)
# ---------------------------------------------------------------------------
# DO NOT add @pytest.mark.no_waiver to skip-annotated tests.
# The skip is by-design per ADR-4 §6; waiver-discipline does not apply.
@pytest.mark.skip(
    reason=(
        "documented degradation — AP-8 two-window cross-adapter migration "
        "substrate not yet authored at 9.4.3; see ADR-4 §6 substitute-readiness. "
        "This is a by-design conformance skip, NOT a waiver of a binding test."
    )
)
def test_M_T_MEM_MIGRATE_02_two_window_substitute() -> None:
    """Corpus migration across adapter substitution (AP-8 two-window) —
    Window 1 dumps + re-embeds; Window 2 smoke passes PS-1..PS-4;
    promotion state drops per Option α clause (b); per-adapter
    idempotency namespace enforced. Cites ADR-1 §3.5 clauses verbatim.

    Q-B3-8 LOCKED stub-skip per `test-strategy.md` v0.2 §7.2 template
    (substitute-readiness scope; AP-8 mechanism deferred). Skip reason
    carries verbatim substrings "documented degradation" + "ADR-4 §6
    substitute-readiness" per §7.2 grep-rule."""


# ---------------------------------------------------------------------------
# 13. M-T-MEM-REVOKE-01 — revoke happy
# ---------------------------------------------------------------------------
def test_M_T_MEM_REVOKE_01_revoke_happy(adapter: MemoryPort) -> None:
    """`revoke_promotion(promotion_id, reason)` — Returns
    `RevokedPromotion`; promotion record observable-revoked per PS-4
    SLO window."""
    stored = adapter.store(_entry("revoke-01-content", idempotency_key="revoke-01-store"))
    rat = _rationale(idempotency_key="revoke-01-promote")
    promoted = adapter.promote(
        hit_id=stored.stored_id, target_tier=PromotionTier.SESSION, rationale=rat
    )
    revoked = adapter.revoke_promotion(
        promotion_id=promoted.promotion_id, reason="test-revoke"
    )
    assert isinstance(revoked, RevokedPromotion)
    assert revoked.promotion_id == promoted.promotion_id
    assert revoked.reason == "test-revoke"


# ---------------------------------------------------------------------------
# 14. M-T-MEM-UNAVAIL-01 — UpstreamUnavailable on on_init() with sidecar down
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("substrate", ["mem0", "letta"])
def test_M_T_MEM_UNAVAIL_01_upstream_down_at_init(substrate: str) -> None:
    """`on_init()` called while [Mem0 sidecar / Letta sidecar] is down —
    Raises `UpstreamUnavailable`; `last_known_health` set. FM-02 coverage.

    NOTE per §2.2.1 row 150: trigger text references "Mem0 sidecar"
    verbatim — Letta parametrization adapts trigger to "Letta
    sidecar/process down"; assertion shape unchanged."""
    if substrate == "mem0":
        _, adp = _make_mem0_adapter(fail_health=True)
    else:
        _, adp = _make_letta_adapter(fail_health=True)
    with pytest.raises(UpstreamUnavailable) as exc_info:
        adp.on_init()
    assert exc_info.value.last_known_health is not None


# ---------------------------------------------------------------------------
# 15. M-T-MEM-IDEMPOTENT-01 — AP-5 reconcile after INTENT-without-SUCCESS
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("substrate", ["mem0", "letta"])
def test_M_T_MEM_IDEMPOTENT_01_reconcile_after_intent_only(substrate: str) -> None:
    """Adapter restarted after INTENT-without-SUCCESS state in idempotency
    log — `on_init()` reconciliation reads back prior idempotency records
    from upstream; no duplicate records on retry."""
    if substrate == "mem0":
        fake = _FakeMem0Memory()
        # Pre-seed an INTENT-without-SUCCESS sidecar record (Q-B1-Sub-2:
        # ROLLBACK over COMPLETE).
        fake._records["orphan-intent-1"] = {
            "id": "orphan-intent-1",
            "memory": "[verdaca.idempotency.intent] store orphan-key",
            "metadata": {
                _MEM0_IDEMPOTENCY_KIND_KEY: "intent",
                _MEM0_IDEMPOTENCY_OPERATION_KEY: "store",
                _MEM0_IDEMPOTENCY_KEY_KEY: "orphan-key",
                _MEM0_IDEMPOTENCY_PAYLOAD_HASH_KEY: "deadbeef" * 8,
            },
            "user_id": _MEM0_SIDECAR_USER_ID,
            "score": 0.85,
        }
        _, adp = _make_mem0_adapter(fake=fake)
        adp.on_init()
        # ROLLBACK: orphan INTENT was deleted from sidecar.
        assert "orphan-intent-1" not in fake._records
        # No duplicate records on retry — fresh store with the orphan key
        # produces a NEW SUCCESS pair (intent + success), not three records.
        before_count = len(fake._records)
        adp.store(_entry("retry-content", idempotency_key="orphan-key"))
        # +3: user-passage record + sidecar INTENT + sidecar SUCCESS.
        assert len(fake._records) == before_count + 3
        adp.on_shutdown()
    else:
        fake = _FakeLetta()
        # Pre-seed an INTENT-without-SUCCESS sidecar passage on Letta.
        intent_passage_id = fake.seed_passage(
            agent_id=_LETTA_TEST_AGENT_ID,
            text="[verdaca.idempotency.intent] store",
            tags=[
                _LETTA_KIND_IDEMPOTENCY,
                "verdaca.idempotency.kind=intent:str",
                "verdaca.idempotency.operation=store:str",
                "verdaca.idempotency.key_hash="
                + ("ab" * 32)
                + ":str",
                "verdaca.idempotency.payload_hash="
                + ("cd" * 32)
                + ":str",
            ],
        )
        _, adp = _make_letta_adapter(fake=fake)
        adp.on_init()
        # ROLLBACK: orphan INTENT was deleted from agent's passage list.
        agent_passages = fake._store.get(_LETTA_TEST_AGENT_ID, [])
        assert all(p.id != intent_passage_id for p in agent_passages)
        # No duplicate records on retry: subsequent store proceeds with
        # fresh INTENT/SUCCESS pair.
        before = len(fake._store.get(_LETTA_TEST_AGENT_ID, []))
        adp.store(_entry("retry-content", idempotency_key="retry-key-letta"))
        after = len(fake._store.get(_LETTA_TEST_AGENT_ID, []))
        # +3: 1 user passage + 1 sidecar INTENT + 1 sidecar SUCCESS.
        assert after == before + 3
        adp.on_shutdown()


# ---------------------------------------------------------------------------
# 16. M-T-MEM-SPANRELABEL-01 — F-004 / AP-10 OTEL relabel verification
# ---------------------------------------------------------------------------
def test_M_T_MEM_SPANRELABEL_01_no_upstream_namespace_leak(
    adapter: MemoryPort,
    otel_capture: InMemorySpanExporter,
) -> None:
    """Adapter emits spans; OTEL collector filter active — Only
    `verdaca.port.memory.*` span names reach collector; zero
    `letta.*`/`mem0.*` span names outside `adapters/<upstream>/`
    internals. AP-10 SpanRelabeler-verified."""
    # Exercise spans via store + query + promote + revoke.
    stored = adapter.store(_entry("spanrelabel-content", idempotency_key="spanrelabel-store"))
    adapter.query(_query("anything", k=5))
    rat = _rationale(idempotency_key="spanrelabel-promote")
    promoted = adapter.promote(
        hit_id=stored.stored_id, target_tier=PromotionTier.SESSION, rationale=rat
    )
    adapter.revoke_promotion(promotion_id=promoted.promotion_id, reason="test")
    span_names = [s.name for s in otel_capture.get_finished_spans()]
    assert span_names, "expected at least one captured span"
    for name in span_names:
        assert name.startswith("verdaca.port.memory."), (
            f"span name leaks upstream namespace: {name}"
        )
        assert not name.startswith("mem0."), f"mem0.* leak: {name}"
        assert not name.startswith("letta."), f"letta.* leak: {name}"


# ---------------------------------------------------------------------------
# 17. M-T-MEM-CORRELATION-01 — V-8 cross-port trace (Stage 9.4.5 prereq; skip per §7.2)
# ---------------------------------------------------------------------------
# DO NOT add @pytest.mark.no_waiver to skip-annotated tests.
# The skip is by-design per ADR-4 §6; waiver-discipline does not apply.
@pytest.mark.skip(
    reason=(
        "documented degradation — LLM Proxy port not yet landed at 9.4.3; "
        "Stage 9.4.5 prerequisite. See ADR-4 §6 substitute-readiness. "
        "This is a by-design conformance skip, NOT a waiver of a binding test."
    )
)
def test_M_T_MEM_CORRELATION_01_cross_port_trace() -> None:
    """Memory span + LLM Proxy span within same correlation_id trace —
    Shared trace_id present on both spans; V-8 cross-port correlation
    propagation.

    Skip-prereq per `test-strategy.md` v0.2 §7.2 template. Skip reason
    carries verbatim substrings "documented degradation" + "ADR-4 §6
    substitute-readiness" per §7.2 grep-rule. LLM Proxy port shipment
    is Stage 9.4.5 territory; this test fires once that lands."""


# ---------------------------------------------------------------------------
# 18. M-T-MEM-CONFIDENCE-01 — F-011 / AP-9 confidence-scale probe (N=50)
# ---------------------------------------------------------------------------
def test_M_T_MEM_CONFIDENCE_01_confidence_range_n50(adapter: MemoryPort) -> None:
    """Random-sample `query(q)` on N=50 — `all(0.0 <= hit.confidence <= 1.0
    for hit in query_result)`. AP-9 ConfidenceScaleNormalizer
    belt-and-braces. Verbatim per requirements.md §6.6."""
    for i in range(50):
        adapter.store(_entry(f"confidence-{i}", idempotency_key=f"conf-{i}"))
    hits = adapter.query(_query("any", k=50))
    assert len(list(hits)) >= 1
    for h in hits:
        assert 0.0 <= h.confidence <= 1.0
