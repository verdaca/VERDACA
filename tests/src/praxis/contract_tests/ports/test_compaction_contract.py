"""Compaction port contract tests — 14 binding MAC-Ts + 3 empirical tests.

Per `test-strategy.md` §2.2.4 (re-authored at Phase 9.4.6-B.2). Each binding
test embeds its `M-T-COMP-*` ID in the function name; docstrings quote the
§2.2.4 assertion language for auditability.

Discipline (per Stage 9.4.6 Phase B.2 hand-off):
- Stay within the 14 binding + 3 empirical scope. No opportunistic coverage.
  Two `M-T-COMP-*` IDs carry two functions each (BUDGET-UNREACHABLE-01,
  ESTIMATE-03) — the ID count stays 14.
- Two-adapter model (OD-1): the suite is parametrized over both CompactionPort
  adapters — the in-tree stub and the LLMLingua adapter. Native-strategy tests
  are adapter-pinned (OD-2/OD-4); the cross-direction test asserts the generic
  downgrade-as-return invariant (OD-2).
- Mock idiom Option gamma: the stub is pure deterministic Python — runs as-is.
  The LLMLingua adapter's `PromptCompressor` is replaced by a deterministic
  `_FakeCompressor` (W3-H#3 precedent) via `patch.object` on `_get_compressor`
  — exercises marshalling / the OD-5 budget loop / strategy mapping with no
  model download.
- Empirical tier (OD-3): `M-T-COMP-EMP-*` need the real `llmlingua==0.2.2` +
  the ~700MB LLMLingua-2 model. Gated by `VERDACA_COMPACTION_EMPIRICAL=1`
  (`skipif`, the single env-var constant `_RUN_EMPIRICAL`) — PR-gate skips;
  the nightly CI job sets the var. A registered `nightly` marker is not used:
  registration would edit `tests/pyproject.toml`, outside the B.2 EDIT
  halt-class.
- No `@pytest.mark.no_waiver` — Compaction has zero allow-list entries; the 3
  error classes are deferred to the Stage 9.9 promotion cycle.

Runner invocation contract (pre-Cleo-9.6; both adapter src dirs on PYTHONPATH;
the two compaction adapters are not yet uv-workspace members):

    # PR-gate (14 binding + 2 suite-integrity tests; empirical skipped):
    PYTHONPATH='adapters/in_tree_compaction_stub/src:adapters/llmlingua/src' \\
        uv run --package praxis-contract-tests --with 'llmlingua==0.2.2' \\
        pytest tests/src/praxis/contract_tests/ports/test_compaction_contract.py -v

    # Nightly (adds the 3 empirical tests; pulls the LLMLingua-2 model):
    VERDACA_COMPACTION_EMPIRICAL=1 PYTHONPATH=... uv run ... pytest ... -v

On Windows the PYTHONPATH separator is ';'. Post-Cleo (workspace registration
at 9.6): naked `pytest` works.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from praxis.adapters.in_tree_compaction_stub import InTreeCompactionStubAdapter
from praxis.adapters.llmlingua import LLMLinguaAdapter
from praxis.ports.common import ContractViolation
from praxis.ports.compaction import (
    CompactionEstimate,
    CompactionPort,
    CompactionRequest,
    CompactionResult,
    DeterminismViolation,
    PreservedSpanEvicted,
    TokenBudgetUnreachable,
    compute_determinism_hash,
)
from praxis.ports.serialization import SerializablePayload

_CID = "test-correlation-compaction-contract"
_LL2_MODEL = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"

# Each adapter's native vs non-native lossy strategy (the inverse-downgrade
# asymmetry, OD-2). Requesting the non-native strategy triggers downgrade-as-
# return to the native one; requesting the native one yields no downgrade.
_NATIVE_LOSSY: dict[str, str] = {
    "in_tree_stub": "lossy_eviction",
    "llmlingua": "lossy_summary",
}
_NONNATIVE_LOSSY: dict[str, str] = {
    "in_tree_stub": "lossy_summary",
    "llmlingua": "lossy_eviction",
}

# Empirical tier gate (OD-3 / A8) — the single env-var constant of record.
# Cross-referenced in test-strategy.md §2.2.4.
_RUN_EMPIRICAL = os.environ.get("VERDACA_COMPACTION_EMPIRICAL") == "1"
_empirical = pytest.mark.skipif(
    not _RUN_EMPIRICAL,
    reason=(
        "empirical tier (OD-3) — requires llmlingua==0.2.2 + the LLMLingua-2 "
        "model (~700MB); set VERDACA_COMPACTION_EMPIRICAL=1 (nightly CI runs it)."
    ),
)

# DETERM-CROSSPY-01 golden literal (A11). sha256 of compute_determinism_hash
# over the exact CompactionRequest built by `_crosspy_request()` below:
#   payload.body          = {"span_a": "fixed", "span_b": "content"}
#   payload.payload_kind  = "context_window"
#   schema_version        = 1   (request + payload)
#   token_budget          = 512
#   compaction_strategy   = "lossless"
#   preserve_span_ids     = ["span_b", "span_a", "span_b"]  (duplicate + unordered)
# correlation_id / idempotency_key are excluded from the hash by construction.
# Regenerate: print(compute_determinism_hash(_crosspy_request())) under any
# CPython >= 3.11 — the literal is interpreter-independent (sha256 over
# json.dumps with sort_keys + fixed separators).
_GOLDEN_DETERMINISM_HASH = (
    "da1dce677c07650685fc3ca764c0fc4c6f8398ab85e4ce889fb7e203ecf8474c"
)


# --------------------------------------------------------------------------
# Test-only constructors + a deterministic LLMLingua substitute
# --------------------------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 5, 17, tzinfo=timezone.utc)


def _payload(
    body: dict[str, Any], *, payload_kind: str = "context_window"
) -> SerializablePayload:
    return SerializablePayload(
        schema_version=1,
        correlation_id=_CID,
        idempotency_key=None,
        body=body,
        payload_kind=payload_kind,
    )


def _request(
    *,
    body: dict[str, Any] | None = None,
    token_budget: int = 10_000,
    compaction_strategy: str = "lossless",
    preserve_span_ids: list[str] | None = None,
    idempotency_key: str | None = "test-comp-key",
    correlation_id: str = _CID,
) -> CompactionRequest:
    return CompactionRequest(
        schema_version=1,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=_payload(
            body if body is not None else {"span_a": "alpha", "span_b": "beta"}
        ),
        token_budget=token_budget,
        compaction_strategy=compaction_strategy,  # type: ignore[arg-type]
        preserve_span_ids=preserve_span_ids or [],
    )


def _crosspy_request() -> CompactionRequest:
    """The fixed request behind the DETERM-CROSSPY-01 golden literal (A11)."""
    return _request(
        body={"span_a": "fixed", "span_b": "content"},
        token_budget=512,
        compaction_strategy="lossless",
        preserve_span_ids=["span_b", "span_a", "span_b"],
        idempotency_key=None,
    )


class _FakeCompressor:
    """Deterministic stand-in for llmlingua.PromptCompressor (W3-H#3 idiom).

    Token length = whitespace-word count. `compress_prompt` truncates each
    context element to a per-element share of `target_token` — enough to
    exercise the adapter's marshalling, the OD-5 hard-budget loop, and the
    strategy mapping with no model download. The return-contract this fake
    must honour is pinned by `test_fake_compressor_return_contract` (A6).
    """

    def __init__(self, *, use_llmlingua2: bool = True, **_: Any) -> None:
        self.use_llmlingua2 = use_llmlingua2

    def get_token_length(self, text: str) -> int:
        return len(text.split())

    def compress_prompt(
        self, context: list[str], target_token: int = -1, **_: Any
    ) -> dict[str, Any]:
        n = max(1, len(context))
        per = max(1, target_token // n) if target_token > 0 else 1_000_000
        compressed = [" ".join(c.split()[:per]) for c in context]
        return {"compressed_prompt_list": compressed}


class _StubbornCompressor(_FakeCompressor):
    """A `_FakeCompressor` that refuses to compress — `compress_prompt` echoes
    the context verbatim, driving `LLMLinguaAdapter._compress`'s
    `_MAX_RECOMPRESS=3` loop to exhaustion (A4).
    """

    def compress_prompt(
        self, context: list[str], target_token: int = -1, **_: Any
    ) -> dict[str, Any]:
        return {"compressed_prompt_list": list(context)}


# --------------------------------------------------------------------------
# Fixtures — parametrized over both adapters (OD-1), plus adapter-pinned ones
# --------------------------------------------------------------------------


@pytest.fixture(params=["in_tree_stub", "llmlingua"])
def adapter_kind(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def adapter(adapter_kind: str) -> Iterator[CompactionPort]:
    if adapter_kind == "in_tree_stub":
        stub = InTreeCompactionStubAdapter()
        stub.on_init()
        yield stub
        return
    ll = LLMLinguaAdapter(default_correlation_id=_CID)
    ll.on_init()
    # Option gamma — substitute the real PromptCompressor with the fake.
    with patch.object(
        LLMLinguaAdapter, "_get_compressor", return_value=_FakeCompressor()
    ):
        yield ll


@pytest.fixture
def stub_adapter() -> InTreeCompactionStubAdapter:
    stub = InTreeCompactionStubAdapter()
    stub.on_init()
    return stub


@pytest.fixture
def llmlingua_adapter() -> Iterator[LLMLinguaAdapter]:
    ll = LLMLinguaAdapter(default_correlation_id=_CID)
    ll.on_init()
    with patch.object(
        LLMLinguaAdapter, "_get_compressor", return_value=_FakeCompressor()
    ):
        yield ll


# ==========================================================================
# §2.2.4 binding MAC-Ts — 14 IDs / 16 functions (zero @pytest.mark.no_waiver)
# ==========================================================================


def test_M_T_COMP_LOSSLESS_01_lossless_passthrough(adapter: CompactionPort) -> None:
    """`compact(strategy="lossless")` within budget — Returns CompactionResult
    with strategy_applied="lossless"; tokens_out <= token_budget; spans_evicted
    empty; every body span in spans_preserved; compacted_payload.body unchanged.
    """
    body = {"span_a": "alpha beta", "span_b": "gamma delta"}
    req = _request(body=body, compaction_strategy="lossless", token_budget=10_000)
    result = adapter.compact(req)
    assert isinstance(result, CompactionResult)
    assert result.strategy_applied == "lossless"
    assert result.tokens_out <= req.token_budget
    assert result.spans_evicted == []
    assert set(result.spans_preserved) == set(body)
    assert result.compacted_payload.body == body
    assert result.determinism_hash == compute_determinism_hash(req)


def test_M_T_COMP_LOSSY_EVICTION_01_native_eviction(
    stub_adapter: InTreeCompactionStubAdapter,
) -> None:
    """`compact(strategy="lossy_eviction", preserve_span_ids=[...])` against the
    in-tree stub (native eviction) — strategy_applied="lossy_eviction";
    tokens_out <= budget; all preserve_span_ids in spans_preserved, none evicted.
    """
    body = {"keep": "x", "drop_a": "A" * 60, "drop_b": "B" * 60}
    req = _request(
        body=body,
        compaction_strategy="lossy_eviction",
        preserve_span_ids=["keep"],
        token_budget=40,
    )
    result = stub_adapter.compact(req)
    assert result.strategy_applied == "lossy_eviction"
    assert result.tokens_out <= req.token_budget
    assert "keep" in result.spans_preserved
    assert "keep" not in result.spans_evicted


def test_M_T_COMP_LOSSY_SUMMARY_01_native_summary(
    llmlingua_adapter: LLMLinguaAdapter,
) -> None:
    """`compact(strategy="lossy_summary", preserve_span_ids=[...])` against the
    LLMLingua adapter (native compression) — strategy_applied="lossy_summary";
    tokens_out <= budget; preserved spans bypass compression and survive.
    """
    body = {
        "keep": "preserved span",
        "comp": "one two three four five six seven eight",
    }
    req = _request(
        body=body,
        compaction_strategy="lossy_summary",
        preserve_span_ids=["keep"],
        token_budget=8,
    )
    result = llmlingua_adapter.compact(req)
    assert result.strategy_applied == "lossy_summary"
    assert result.tokens_out <= req.token_budget
    assert "keep" in result.spans_preserved


def test_M_T_COMP_STRATEGY_DOWNGRADE_01_downgrade_as_return(
    adapter: CompactionPort, adapter_kind: str
) -> None:
    """`compact()` requesting each adapter's non-native lossy strategy —
    downgrade-as-return: strategy_applied is the adapter's native lossy
    strategy (A2: stub->lossy_eviction, llmlingua->lossy_summary), differs from
    compaction_strategy, no error raised; tokens_out <= budget. (ID retains the
    STRATEGY-DOWNGRADE label; the StrategyDowngrade error class was removed at
    v0.2.6 — downgrade is signalled by the returned strategy_applied.)
    """
    requested = _NONNATIVE_LOSSY[adapter_kind]
    body = {"keep": "k", "comp": "alpha beta gamma delta epsilon"}
    req = _request(
        body=body,
        compaction_strategy=requested,
        preserve_span_ids=["keep"],
        token_budget=10_000,
    )
    result = adapter.compact(req)
    assert result.strategy_applied == _NATIVE_LOSSY[adapter_kind]
    assert result.strategy_applied != requested
    assert result.strategy_applied in {"lossless", "lossy_summary", "lossy_eviction"}
    assert result.tokens_out <= req.token_budget


def test_M_T_COMP_BUDGET_UNREACHABLE_01_lossless_overflow(
    adapter: CompactionPort,
) -> None:
    """`compact(strategy="lossless")` on a payload structurally exceeding a
    minimal budget — Raises TokenBudgetUnreachable; requested_budget +
    minimum_achievable populated. (M-T-COMP-BUDGET-UNREACHABLE-01, path 1 of 2.)
    """
    body = {"span_a": "this payload structurally cannot fit a budget of one"}
    req = _request(body=body, compaction_strategy="lossless", token_budget=1)
    with pytest.raises(TokenBudgetUnreachable) as exc_info:
        adapter.compact(req)
    assert exc_info.value.requested_budget == 1
    assert exc_info.value.minimum_achievable >= 1


def test_M_T_COMP_BUDGET_UNREACHABLE_01_recompress_exhaustion() -> None:
    """`compact()` on the LLMLingua adapter when an under-compressing substrate
    cannot reach the budget within `_MAX_RECOMPRESS=3` iterations — Raises
    TokenBudgetUnreachable. Exercises the OD-5 recompress-loop exhaustion path.
    (M-T-COMP-BUDGET-UNREACHABLE-01, path 2 of 2 — A4, llmlingua-pinned.)
    """
    body = {"comp": "alpha beta gamma delta epsilon zeta eta theta iota kappa"}
    req = _request(body=body, compaction_strategy="lossy_summary", token_budget=2)
    ll = LLMLinguaAdapter(default_correlation_id=_CID)
    ll.on_init()
    with patch.object(
        LLMLinguaAdapter, "_get_compressor", return_value=_StubbornCompressor()
    ):
        with pytest.raises(TokenBudgetUnreachable) as exc_info:
            ll.compact(req)
    assert exc_info.value.requested_budget == 2
    assert exc_info.value.minimum_achievable >= 2


def test_M_T_COMP_PRESERVED_EVICTED_01_preserved_span_invariant(
    adapter: CompactionPort, adapter_kind: str
) -> None:
    """PreservedSpanEvicted is a ContractViolation with evicted_span_id;
    positive invariant — no preserved id ever appears in spans_evicted (both
    adapters preserve correct-by-construction; neither raises this class).
    A3 adversarial sub-assertion (c): when preserved-span content alone exceeds
    token_budget the adapter raises TokenBudgetUnreachable rather than evicting
    a preserved span (the raise path precludes preserved-span eviction by
    construction). Real enforcement path — no eviction-seam mock.
    """
    # (a) error-class shape.
    err = PreservedSpanEvicted(
        port_name="compaction",
        correlation_id=_CID,
        occurred_at=_now(),
        upstream_name=None,
        violation_class="invariant",
        evicted_span_id="span_x",
    )
    assert isinstance(err, ContractViolation)
    assert err.evicted_span_id == "span_x"

    # (b) positive invariant — a normal lossy compaction never evicts a
    # preserved span.
    body = {"keep": "kept", "comp": "alpha beta gamma delta epsilon zeta eta theta"}
    req = _request(
        body=body,
        compaction_strategy=_NATIVE_LOSSY[adapter_kind],
        preserve_span_ids=["keep"],
        token_budget=30,
    )
    result = adapter.compact(req)
    assert "keep" in result.spans_preserved
    assert set(result.spans_evicted).isdisjoint(set(req.preserve_span_ids))

    # (c) adversarial — preserved content alone exceeds the budget.
    adv = _request(
        body={"keep": "word " * 60, "drop": "x"},
        compaction_strategy=_NATIVE_LOSSY[adapter_kind],
        preserve_span_ids=["keep"],
        token_budget=10,
    )
    with pytest.raises(TokenBudgetUnreachable):
        adapter.compact(adv)


def test_M_T_COMP_DETERM_VIOLATION_01_caller_raised_shape() -> None:
    """DeterminismViolation is a ContractViolation with expected_hash +
    actual_hash; it is caller-raised (owned-vs-delegated table — the caller
    compares two determinism_hash values, the adapter never raises it). Two
    distinct requests yield distinct hashes, so the caller-side compare-and-
    raise has a real trigger.
    """
    err = DeterminismViolation(
        port_name="compaction",
        correlation_id=_CID,
        occurred_at=_now(),
        upstream_name=None,
        violation_class="invariant",
        expected_hash="a" * 64,
        actual_hash="b" * 64,
    )
    assert isinstance(err, ContractViolation)
    assert err.expected_hash == "a" * 64
    assert err.actual_hash == "b" * 64

    hash_one = compute_determinism_hash(_request(body={"a": "one"}))
    hash_two = compute_determinism_hash(_request(body={"a": "two"}))
    assert hash_one != hash_two


def test_M_T_COMP_DETERM_CROSSPY_01_golden_hash_stability() -> None:
    """compute_determinism_hash() of a fixed CompactionRequest (duplicate +
    unordered preserve_span_ids) — equals a frozen golden sha256 literal;
    key-sort + set-normalization make the hash binary-stable across Python
    3.11 AND 3.12. Verbatim per requirements.md §6.5.
    """
    assert compute_determinism_hash(_crosspy_request()) == _GOLDEN_DETERMINISM_HASH


def test_M_T_COMP_ESTIMATE_01_estimate_accuracy(adapter: CompactionPort) -> None:
    """`estimate()` then `compact()` on a lossless request — estimated_tokens_out
    == tokens_out (lossless is exact for both adapters); 0.0 <= confidence <= 1.0.
    """
    req = _request(
        body={"span_a": "alpha beta", "span_b": "gamma"},
        compaction_strategy="lossless",
        token_budget=10_000,
    )
    est = adapter.estimate(req)
    result = adapter.compact(req)
    assert isinstance(est, CompactionEstimate)
    assert est.estimated_tokens_out == result.tokens_out
    assert 0.0 <= est.confidence <= 1.0


def test_M_T_COMP_ESTIMATE_02_estimate_strategy(
    adapter: CompactionPort, adapter_kind: str
) -> None:
    """`estimate()` + `compact()` requesting a non-native lossy strategy —
    estimated_strategy == strategy_applied; estimate and compact resolve the
    strategy identically, including the downgrade.
    """
    req = _request(
        body={"keep": "k", "comp": "alpha beta gamma delta epsilon"},
        compaction_strategy=_NONNATIVE_LOSSY[adapter_kind],
        preserve_span_ids=["keep"],
        token_budget=10_000,
    )
    est = adapter.estimate(req)
    result = adapter.compact(req)
    assert est.estimated_strategy == result.strategy_applied


def test_M_T_COMP_ESTIMATE_03_confidence_monotonic(
    adapter: CompactionPort, adapter_kind: str
) -> None:
    """`estimate()` on a lossless vs a lossy request over the same payload —
    0.0 <= lossy.confidence <= lossless.confidence <= 1.0; a lossy forecast is
    no more confident than a lossless one. (M-T-COMP-ESTIMATE-03, path 1 of 2 —
    <=-monotonic, parametrized; the stub's confidence is a by-design constant
    1.0, so strict < is asserted only on the llmlingua-pinned path 2.)
    """
    body = {"comp": "many words to estimate a confidence over here now"}
    lossless = adapter.estimate(
        _request(body=body, compaction_strategy="lossless", token_budget=10_000)
    )
    lossy = adapter.estimate(
        _request(
            body=body,
            compaction_strategy=_NATIVE_LOSSY[adapter_kind],
            token_budget=10_000,
        )
    )
    assert 0.0 <= lossy.confidence <= lossless.confidence <= 1.0


def test_M_T_COMP_ESTIMATE_03_strict_confidence_llmlingua(
    llmlingua_adapter: LLMLinguaAdapter,
) -> None:
    """`estimate()` lossless vs lossy on the LLMLingua adapter — lossy.confidence
    is STRICTLY below lossless.confidence (0.8 vs 1.0). (M-T-COMP-ESTIMATE-03,
    path 2 of 2 — A5, llmlingua-pinned.)
    """
    body = {"comp": "many words to estimate a confidence over here now"}
    lossless = llmlingua_adapter.estimate(
        _request(body=body, compaction_strategy="lossless", token_budget=10_000)
    )
    lossy = llmlingua_adapter.estimate(
        _request(body=body, compaction_strategy="lossy_summary", token_budget=10_000)
    )
    assert lossy.confidence < lossless.confidence


def test_M_T_COMP_PRESERVE_ORDER_01_preserved_order(adapter: CompactionPort) -> None:
    """`compact()` with preserve_span_ids in non-body order — spans_preserved
    follows body insertion order, not sorted order, not preserve_span_ids
    argument order. (A13: body insertion order [s2, s3, s1] differs from both
    sorted order [s1, s2, s3] and the argument order [s1, s2].)
    """
    body = {"s2": "b", "s3": "c", "s1": "a"}
    req = _request(
        body=body,
        compaction_strategy="lossless",
        token_budget=10_000,
        preserve_span_ids=["s1", "s2"],
    )
    result = adapter.compact(req)
    assert result.spans_preserved == ["s2", "s3", "s1"]


def test_M_T_COMP_IDEMPOTENT_01_idempotent_compact(adapter: CompactionPort) -> None:
    """`compact()` twice on the same CompactionRequest — equal determinism_hash
    AND byte-equal compacted_payload (the companion assertion — a request-
    derived hash alone does not witness output determinism); both equal
    compute_determinism_hash(request).
    """
    req = _request(
        body={"span_a": "alpha", "span_b": "beta"},
        compaction_strategy="lossless",
        token_budget=10_000,
    )
    r1 = adapter.compact(req)
    r2 = adapter.compact(req)
    assert r1.determinism_hash == r2.determinism_hash
    assert r1.compacted_payload.model_dump() == r2.compacted_payload.model_dump()
    assert r1.determinism_hash == compute_determinism_hash(req)


def test_M_T_COMP_INTERNAL_TOKENS_01_no_cost_coupling() -> None:
    """grep cost_usd/price_/usd_ across the two adapter src trees — Zero
    matches; token counting is internal to the port, no Cost Meter coupling.
    (Trigger corrected at B.2 — the v0.1 target src/verdaca/adapters/forge/ is
    doubly stale: Forge retired, src/verdaca/ namespace retired.) A10: the
    denylist is a tripwire, not exhaustive proof of decoupling; the test also
    asserts a non-zero file count was actually scanned.
    """
    repo_root = Path(__file__).resolve().parents[5]
    roots = [
        repo_root / "adapters" / "in_tree_compaction_stub" / "src",
        repo_root / "adapters" / "llmlingua" / "src",
    ]
    pattern = re.compile(r"cost_usd|price_|usd_")
    offenders: list[str] = []
    scanned = 0
    for root in roots:
        assert root.is_dir(), f"adapter src root not found: {root}"
        for py in sorted(root.rglob("*.py")):
            scanned += 1
            for lineno, line in enumerate(
                py.read_text(encoding="utf-8").splitlines(), 1
            ):
                if pattern.search(line):
                    offenders.append(f"{py}:{lineno}: {line.strip()}")
    assert scanned > 0, "no .py files scanned — adapter src path drift"
    assert offenders == [], f"cost-coupling tokens found: {offenders}"


# ==========================================================================
# Suite-integrity tests — non-binding, no MAC-T ID (A6, A7)
# ==========================================================================


def test_fake_compressor_return_contract() -> None:
    """A6 (non-binding): the `_FakeCompressor` must match the surface
    `LLMLinguaAdapter._compress` depends on — `compress_prompt` returns
    {"compressed_prompt_list": list} with len == len(context) (the adapter's
    `zip(..., strict=True)` + length guard), and `get_token_length` returns
    int. Closes the PR-gate-invisible fake-fidelity hole — the real
    PromptCompressor surface runs only in the empirical tier.
    """
    fake = _FakeCompressor()
    context = ["alpha beta", "gamma delta epsilon"]
    out = fake.compress_prompt(context=context, target_token=4)
    assert isinstance(out, dict)
    compressed = out["compressed_prompt_list"]
    assert isinstance(compressed, list)
    assert len(compressed) == len(context)
    assert isinstance(fake.get_token_length("one two three"), int)
    assert fake.get_token_length("one two three") == 3


def test_empirical_tier_membership_guard() -> None:
    """A7 (non-binding): exactly 3 M-T-COMP-EMP-* tests exist and every one
    carries a skipif mark — the empirical tier never leaks into the PR gate.
    """
    import sys

    module = sys.modules[__name__]
    emp_names = sorted(n for n in dir(module) if n.startswith("test_M_T_COMP_EMP_"))
    assert len(emp_names) == 3, emp_names
    for name in emp_names:
        marks = list(getattr(getattr(module, name), "pytestmark", []))
        assert any(m.name == "skipif" for m in marks), f"{name} missing skipif"


# ==========================================================================
# Empirical substrate-fidelity tests — 3 (env-gated, OD-3)
# ==========================================================================


@_empirical
def test_M_T_COMP_EMP_DETERM_01_empirical_twice_run() -> None:
    """LLMLingua adapter compact() twice (two fresh instances) on a fixed
    request against the real substrate — identical determinism_hash AND
    byte-equal compacted_payload. Confirms the W1-H#1 static determinism PASS
    empirically. Tests through the CompactionPort surface.
    """
    body = {
        "keep": "a preserved verbatim span",
        "comp": (
            "a longer paragraph of natural-language text supplied so the "
            "LLMLingua-2 perplexity compressor has real content to compress "
            "and the determinism of the compression path can be observed"
        ),
    }
    req = _request(
        body=body,
        compaction_strategy="lossy_summary",
        preserve_span_ids=["keep"],
        token_budget=256,
    )
    a1 = LLMLinguaAdapter(default_correlation_id=_CID)
    a1.on_init()
    a2 = LLMLinguaAdapter(default_correlation_id=_CID)
    a2.on_init()
    r1 = a1.compact(req)
    r2 = a2.compact(req)
    assert r1.determinism_hash == r2.determinism_hash
    assert r1.compacted_payload.model_dump() == r2.compacted_payload.model_dump()


# --- substrate-fidelity tier (A14 / F-9.4.6-B.2-EMP-PLACEMENT-01) ---
# EMP-LL2MODE-01 and EMP-ALIGN-01 characterize the llmlingua library surface
# directly — they are not CompactionPort contract assertions. Kept in-file for
# B.2 (relocating needs a 2nd CREATE file, outside the B.2 halt-class; no
# adapter substrate-test-dir convention exists yet). Relocation deferred to 9.6
# (Cleo workspace registration). EMP-DETERM-01 above tests through the port
# and stays.


@_empirical
def test_M_T_COMP_EMP_LL2MODE_01_llmlingua2_dispatch() -> None:
    """W3 assumption (a): compress_prompt dispatches to llmlingua2 mode for a
    use_llmlingua2=True compressor; returns the compressed_prompt_list dict.
    Substrate-fidelity tier (A14).
    """
    from llmlingua import PromptCompressor

    pc = PromptCompressor(model_name=_LL2_MODEL, device_map="cpu", use_llmlingua2=True)
    assert pc.use_llmlingua2 is True
    out = pc.compress_prompt(
        context=["some natural-language text to compress in llmlingua2 mode"],
        target_token=5,
    )
    assert isinstance(out, dict)
    assert "compressed_prompt_list" in out


@_empirical
def test_M_T_COMP_EMP_ALIGN_01_positional_alignment() -> None:
    """W3 assumption (b): compressed_prompt_list is a list positionally aligned
    to the input context (equal len). Substrate-fidelity tier (A14).
    """
    from llmlingua import PromptCompressor

    pc = PromptCompressor(model_name=_LL2_MODEL, device_map="cpu", use_llmlingua2=True)
    context = [
        "first span alpha alpha alpha",
        "second span beta beta beta",
        "third span gamma gamma gamma",
    ]
    out = pc.compress_prompt(context=context, target_token=12)
    compressed = out["compressed_prompt_list"]
    assert isinstance(compressed, list)
    assert len(compressed) == len(context)
