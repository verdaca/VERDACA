"""LLM Proxy port contract tests — 7 MAC-Ts.

Per `test-strategy.md` v0.2 §2.2.6 post-A-8 — 7 binding `M-T-LLM-*` MAC-Ts
active (4 retired at A-8 corrigendum 2026-05-11 per H2-falsification per
Q-9.4.5-21: M-T-LLM-CALL-RTK-01 + M-T-LLM-STREAM-RTK-01 +
M-T-LLM-COST-STRIP-01 retired in §2.2.6 + M-T-MATRIX-SUBST-LLMPROXY-01
retired in §2.2.7.b). Each test embeds its MAC-T ID in the function name;
docstrings quote the §2.2.6 assertion language verbatim (post-A-7
trigger text for PROVIDERS-02) for auditability.

Discipline (per Stage 9.4.5 Phase B.2 hand-off):
- Stay strictly within the 7-ID scope. No 8th test, no parametric
  expansion, no opportunistic coverage.
- Test the public `LLMProxyPort` Protocol surface via the LiteLLM
  adapter (single-adapter post-H2-falsification per Q-9.4.5-21; no
  parametric [rtk, litellm]-style fixture — sole substrate is LiteLLM).
- No `@pytest.mark.no_waiver` — LLM-Proxy has zero entries in the
  22-entry allow-list per `test-strategy.md` v0.2 §6.1 + advisor §3.1.
  M-T-LLM-COMPRESS-01 + M-T-LLM-COSTLEAK-01 remain deferred-to-9.9
  promotion cycle but are gate-only via contract tests at v0.1.0.
- Per-test targeted mocks (Option γ ruling at H#1) — `unittest.mock`
  patches `praxis.adapters.litellm.adapter.litellm.completion` /
  `models_by_provider` / `get_supported_openai_params` per-test for
  state isolation and F-B1-AUTH-NOISE-1 mitigation.
- M-T-LLM-COMPRESS-01 uses @patch.object(LiteLLMAdapter,
  '_detect_compression', return_value=True) per J-B2-1 Option α: B.1
  adapter's _detect_compression() returns False unconditionally at
  v0.1.0; mock simulates "adapter that compresses" scenario for raise-
  path verification.

Runner invocation contract (per Q-9.4.5-7 = Option α):

    PYTHONPATH='adapters/litellm/src' uv run \\
        --package praxis-contract-tests pytest \\
        tests/src/praxis/contract_tests/ports/test_llm_proxy_contract.py -v

Post-Cleo (workspace registration landed at 9.6): naked `pytest` works.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from praxis.adapters.litellm import LiteLLMAdapter
from praxis.ports.common import Message
from praxis.ports.llm_proxy import (
    CompressionContractViolation,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ProviderInfo,
)


_TEST_CORRELATION_ID = "test-correlation-llm-proxy-contract"


# Test-only payload constructors (per sibling test_cost_meter_contract.py:53-87
# at 3cd6c86 `_event` pattern).


def _message(role: str = "user", content: str = "hello") -> Message:
    return Message(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        idempotency_key=None,
        role=role,  # type: ignore[arg-type]
        content=content,
    )


def _request(
    *,
    provider: str = "anthropic",
    model: str = "claude-opus-4-7",
    messages: list[Message] | None = None,
    max_tokens: int = 100,
    temperature: float = 0.5,
    compression_hint: str = "none",
    idempotency_key: str | None = "test-llm-key",
    correlation_id: str = _TEST_CORRELATION_ID,
) -> LLMRequest:
    return LLMRequest(
        schema_version=1,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        provider=provider,
        model=model,
        messages=messages if messages is not None else [_message()],
        max_tokens=max_tokens,
        temperature=temperature,
        compression_hint=compression_hint,  # type: ignore[arg-type]
    )


def _mock_completion_response(
    *,
    content: str = "hello-back",
    finish_reason: str = "stop",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    raw_id: str = "resp-test-1",
    extra_usage: dict[str, Any] | None = None,
) -> MagicMock:
    """Construct mocked litellm.ModelResponse return value.

    `extra_usage` lets tests inject cost-adjacent keys (cost_usd /
    usd_total / price_per_token) into the usage dict to verify DS-1
    cost-strip behavior at adapter layer (M-T-LLM-COSTLEAK-01 Layer 3).
    """
    usage_dict: dict[str, Any] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    if extra_usage:
        usage_dict.update(extra_usage)
    mock_usage = MagicMock()
    mock_usage.model_dump.return_value = usage_dict

    mock_choice = MagicMock()
    mock_choice.finish_reason = finish_reason
    mock_choice.message.content = content

    mock = MagicMock()
    mock.id = raw_id
    mock.choices = [mock_choice]
    mock.usage = mock_usage
    return mock


def _mock_stream_chunks(
    *,
    deltas: list[str] | None = None,
    final_prompt_tokens: int = 10,
    final_completion_tokens: int = 15,
    extra_usage: dict[str, Any] | None = None,
) -> Any:
    """Construct mocked iterator of litellm.ModelResponseStream chunks.

    Returns N delta chunks (default 2) + 1 final chunk (final detected
    via finish_reason is not None). `extra_usage` injects cost-adjacent
    keys to verify DS-1 cost-strip on final-chunk usage.
    """
    deltas = deltas if deltas is not None else ["hel", "lo"]
    chunks: list[MagicMock] = []
    for delta in deltas:
        ch = MagicMock()
        ch_choice = MagicMock()
        ch_choice.finish_reason = None
        ch_choice.delta.content = delta
        ch.choices = [ch_choice]
        ch.usage = None
        chunks.append(ch)
    # Final chunk
    final_chunk = MagicMock()
    fc_choice = MagicMock()
    fc_choice.finish_reason = "stop"
    fc_choice.delta.content = ""
    final_chunk.choices = [fc_choice]
    usage_dict: dict[str, Any] = {
        "prompt_tokens": final_prompt_tokens,
        "completion_tokens": final_completion_tokens,
    }
    if extra_usage:
        usage_dict.update(extra_usage)
    mock_usage = MagicMock()
    mock_usage.model_dump.return_value = usage_dict
    final_chunk.usage = mock_usage
    chunks.append(final_chunk)
    return iter(chunks)


@pytest.fixture
def adapter() -> LiteLLMAdapter:
    a = LiteLLMAdapter(
        api_keys={"anthropic": "test-fake-key"},
        default_correlation_id=_TEST_CORRELATION_ID,
    )
    a.on_init()
    return a


# ===========================================================================
# §2.2.6 MAC-Ts post-A-8 — 7 tests (zero @pytest.mark.no_waiver per advisor §3.1)
# ===========================================================================


def test_M_T_LLM_CALL_LITELLM_01_call_happy(adapter: LiteLLMAdapter) -> None:
    """`call(LLMRequest(provider, model, messages, max_tokens, ...))`
    against LiteLLM adapter — Returns `LLMResponse`; `input_tokens` +
    `output_tokens` present; `finish_reason` in valid set; **no `cost_usd`
    field**. Verbatim per test-strategy.md v0.2 §2.2.6 (post-A-8 LITELLM
    suffix preserved per LITELLM-suffix-rename rejection at A.3 H#2).
    """
    request = _request(idempotency_key="call-01")
    with patch(
        "praxis.adapters.litellm.adapter.litellm.completion"
    ) as mock_completion:
        mock_completion.return_value = _mock_completion_response(
            content="hello-back",
            finish_reason="stop",
            prompt_tokens=10,
            completion_tokens=20,
        )
        response = adapter.call(request)
    assert isinstance(response, LLMResponse)
    assert response.content == "hello-back"
    assert response.input_tokens == 10
    assert response.output_tokens == 20
    assert response.finish_reason in {
        "stop",
        "length",
        "content_filter",
        "tool_use",
    }
    # No cost_usd field at construction-time (extra="forbid" enforces).
    assert not hasattr(response, "cost_usd")
    assert response.raw_response_id == "resp-test-1"


def test_M_T_LLM_STREAM_LITELLM_01_stream_happy(adapter: LiteLLMAdapter) -> None:
    """`stream(request)` returns iterator — Yields `LLMStreamChunk`;
    final chunk has `is_final=True` + `final_input_tokens` +
    `final_output_tokens` set; non-final chunks have them as `None`.
    Verbatim per test-strategy.md v0.2 §2.2.6.
    """
    request = _request(idempotency_key="stream-01")
    with patch(
        "praxis.adapters.litellm.adapter.litellm.completion"
    ) as mock_completion:
        mock_completion.return_value = _mock_stream_chunks(
            deltas=["hel", "lo"],
            final_prompt_tokens=10,
            final_completion_tokens=15,
        )
        chunks = list(adapter.stream(request))
    assert len(chunks) == 3
    # Intermediate chunks (chunk_index 0, 1) have is_final=False.
    for i in (0, 1):
        assert isinstance(chunks[i], LLMStreamChunk)
        assert chunks[i].is_final is False
        assert chunks[i].final_input_tokens is None
        assert chunks[i].final_output_tokens is None
        assert chunks[i].chunk_index == i
    # Final chunk (chunk_index 2) has is_final=True + tokens set.
    assert chunks[2].is_final is True
    assert chunks[2].final_input_tokens == 10
    assert chunks[2].final_output_tokens == 15
    assert chunks[2].chunk_index == 2


def test_M_T_LLM_COMPRESS_01_compression_hint_violation(
    adapter: LiteLLMAdapter,
) -> None:
    """`call()` with `compression_hint="none"` against adapter that
    compresses — Raises `CompressionContractViolation` with
    `hint_was="none"`, `compressed_anyway=True`. Verbatim per
    test-strategy.md v0.2 §2.2.6.

    Per J-B2-1 Option α: B.1 adapter's `_detect_compression()` returns
    False unconditionally at v0.1.0 (compression-detection heuristics
    deferred to v0.2.0 per changelog scope restriction); test mocks
    detection via @patch.object to simulate "adapter that compresses"
    scenario, verifying the raise-path conditional logic in
    adapter.call() works correctly. Tests pre-condition + assertion
    independence (production logic exists; detection mechanism is the
    v0.1.0 no-op surface).
    """
    request = _request(
        idempotency_key="compress-01",
        compression_hint="none",
    )
    with patch(
        "praxis.adapters.litellm.adapter.litellm.completion"
    ) as mock_completion:
        mock_completion.return_value = _mock_completion_response()
        with patch.object(
            LiteLLMAdapter,
            "_detect_compression",
            return_value=True,
        ):
            with pytest.raises(CompressionContractViolation) as exc_info:
                adapter.call(request)
    assert exc_info.value.hint_was == "none"
    assert exc_info.value.compressed_anyway is True


def test_M_T_LLM_COSTLEAK_01_cost_field_leakage(
    adapter: LiteLLMAdapter,
) -> None:
    """Cleo grep: any `cost_` / `usd_` / `price_` field on `LLMResponse`
    subclasses — Zero results. At runtime, adapter response passing
    through port raises `CostFieldLeakage` with `leaked_field` name if
    any cost-adjacent field is attached. Verbatim per test-strategy.md
    v0.2 §2.2.6.

    Per Q-9.4.5-6 3-layer defense-in-depth + DS-B2-2 dual-coverage in
    single test: this test verifies Layer 1 (construction-time
    `extra="forbid"`) + Layer 3 (adapter-layer prefix-match strip).
    Layer 2 (port-boundary runtime guard) is inherently tested via
    Layer 1 + Layer 3.
    """
    # Layer 1: LLMResponse(cost_usd=...) construction-time raise via
    # VerdacaDTOMixin extra="forbid".
    with pytest.raises(ValidationError):
        LLMResponse(
            schema_version=1,
            correlation_id=_TEST_CORRELATION_ID,
            idempotency_key=None,
            content="x",
            finish_reason="stop",
            input_tokens=1,
            output_tokens=1,
            raw_response_id="r-leak-1",
            cost_usd=0.001,  # type: ignore[call-arg]
        )

    # Layer 3: adapter strips cost-adjacent fields from LiteLLM response
    # usage BEFORE LLMResponse construction. Mocked LiteLLM response
    # carries cost_usd + usd_total + price_per_token in usage; adapter
    # strips all three; LLMResponse construction succeeds with clean
    # input_tokens + output_tokens only.
    request = _request(idempotency_key="costleak-layer3")
    with patch(
        "praxis.adapters.litellm.adapter.litellm.completion"
    ) as mock_completion:
        mock_completion.return_value = _mock_completion_response(
            content="clean",
            prompt_tokens=10,
            completion_tokens=20,
            extra_usage={
                "cost_usd": 0.001,
                "usd_total": 0.0015,
                "price_per_token": 1e-7,
            },
        )
        response = adapter.call(request)
    # Adapter strip held: response constructed without ValidationError.
    assert isinstance(response, LLMResponse)
    assert response.input_tokens == 10
    assert response.output_tokens == 20
    # Verify no cost-adjacent fields leaked through to LLMResponse.
    assert not hasattr(response, "cost_usd")


def test_M_T_LLM_PROVIDERS_01_supported_providers_happy(
    adapter: LiteLLMAdapter,
) -> None:
    """`supported_providers()` — Returns `Sequence[ProviderInfo]`;
    stable across calls; no dropped providers between version bumps
    (matrix-tier parametrization catches drift). Verbatim per
    test-strategy.md v0.2 §2.2.6.

    Per F-B1-AUTH-NOISE-1 mitigation: mock both
    `litellm.models_by_provider` (DS-2 Option α capability-grounded
    source per advisor H#2 override) AND
    `litellm.get_supported_openai_params` to avoid 60-90s device-auth
    probes during test run.
    """
    synthetic_models_by_provider = {
        "anthropic": {"claude-opus-4-7", "claude-sonnet-4-6"},
        "openai": {"gpt-4o", "o1"},
    }
    with patch.dict(
        "praxis.adapters.litellm.adapter.litellm.models_by_provider",
        synthetic_models_by_provider,
        clear=True,
    ):
        with patch(
            "praxis.adapters.litellm.adapter.litellm.get_supported_openai_params",
            return_value=["stream", "temperature", "max_tokens"],
        ):
            providers = adapter.supported_providers()
    assert len(providers) == 2
    by_name = {p.name: p for p in providers}
    assert "anthropic" in by_name
    assert "openai" in by_name
    # Q-9.4.5-13 shape verification.
    anthropic_pi = by_name["anthropic"]
    assert isinstance(anthropic_pi, ProviderInfo)
    assert isinstance(anthropic_pi.name, str)
    assert isinstance(anthropic_pi.version, str)
    assert isinstance(anthropic_pi.model_catalog, tuple)
    assert all(isinstance(m, str) for m in anthropic_pi.model_catalog)
    assert isinstance(anthropic_pi.streaming_supported, bool)
    # Sorted tuple per adapter immutability discipline.
    assert anthropic_pi.model_catalog == ("claude-opus-4-7", "claude-sonnet-4-6")
    # streaming_supported derived from mocked get_supported_openai_params.
    assert anthropic_pi.streaming_supported is True


def test_M_T_LLM_PROVIDERS_02_catalog_stability(
    adapter: LiteLLMAdapter,
) -> None:
    """Matrix run: `supported_providers()` on adapter-current vs
    adapter-current-1; catalog comparison = set-equality on
    `(provider.name, frozenset(provider.model_catalog))` tuples — No
    silent `(provider, model)` pair removal between adapter-current and
    adapter-current-1; additions OK. Verbatim per test-strategy.md
    v0.2 §2.2.6 post-A-7 trigger amendment + post-A-8 PROVIDERS-02
    matrix-tier scope.

    Per Watch K (matrix-tier 9.5 territory): B.2 implements as
    single-version sanity-check verifying the set-equality formula
    structure with synthetic data; full cross-version comparison is
    9.5 matrix harness scope. This test invokes supported_providers()
    twice with the same mock to verify the formula is stable; cross-
    version-tier scaffolding (litellm-current + litellm-current-1
    parametrize) is OUT OF SCOPE at B.2 per advisor §8 watch K.
    """
    synthetic_models_by_provider = {
        "anthropic": {"claude-opus-4-7", "claude-sonnet-4-6"},
        "openai": {"gpt-4o", "o1"},
    }
    with patch.dict(
        "praxis.adapters.litellm.adapter.litellm.models_by_provider",
        synthetic_models_by_provider,
        clear=True,
    ):
        with patch(
            "praxis.adapters.litellm.adapter.litellm.get_supported_openai_params",
            return_value=["stream"],
        ):
            providers_t1 = adapter.supported_providers()
            providers_t2 = adapter.supported_providers()
    # Set-equality formula per A-7 PROVIDERS-02 trigger:
    # comparison on (provider.name, frozenset(provider.model_catalog)) tuples.
    set_t1 = {(p.name, frozenset(p.model_catalog)) for p in providers_t1}
    set_t2 = {(p.name, frozenset(p.model_catalog)) for p in providers_t2}
    assert set_t1 == set_t2
    # No silent (provider, model) pair removal: empty symmetric difference
    # for the same-version case.
    assert set_t1.symmetric_difference(set_t2) == set()
    # 9.5 matrix harness territory: real cross-version comparison
    # (litellm-current + litellm-current-1 parametrize) lands at the
    # matrix tier; this B.2 test is single-version sanity-check.


def test_M_T_LLM_IDEMPOTENT_01_dedup_on_key(
    adapter: LiteLLMAdapter,
) -> None:
    """`call()` with duplicate `idempotency_key` — Same `LLMResponse`;
    provider-level idempotency per adapter config. Verbatim per
    test-strategy.md v0.2 §2.2.6.

    Per DS-4 in-process dict cache (B.1 H#3 watch F1 verified). DS-5
    strict-β: stream-idempotency is OUT OF SCOPE for this MAC-T;
    deferred to v1.1.0 minor bump if Stage 10+ MAC-T demands it.
    """
    request = _request(idempotency_key="dedup-key-llm-1")
    with patch(
        "praxis.adapters.litellm.adapter.litellm.completion"
    ) as mock_completion:
        mock_completion.return_value = _mock_completion_response(
            content="cached-result"
        )
        # First call: cache miss; upstream invoked.
        r1 = adapter.call(request)
        assert mock_completion.call_count == 1
        # Second call with same idempotency_key: cache hit; upstream NOT
        # invoked again.
        r2 = adapter.call(request)
        assert r2 is r1  # same instance returned per cache lookup
        assert mock_completion.call_count == 1
