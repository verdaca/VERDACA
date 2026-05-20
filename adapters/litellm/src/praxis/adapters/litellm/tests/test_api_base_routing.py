"""Adapter-internal test — LiteLLMAdapter DIAL override routing.

Verifies the ADR-9.2-V5 v0.8 corrigendum capability: a per-provider
`api_base` override (caller-DI, mirroring `api_keys`) is threaded into
`litellm.completion()`. The local EPAM DIAL route also requires Azure
`api_version`; the adapter exposes that as an additive per-provider
override rather than relying on process-global `AZURE_API_VERSION`.
NOT part of the shared 7-ID-frozen contract suite
(`tests/src/praxis/contract_tests/ports/test_llm_proxy_contract.py`) —
adapter-internal per `ports-architecture.md` §2.1.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from praxis.adapters.litellm import LiteLLMAdapter
from praxis.ports.common import Message
from praxis.ports.llm_proxy import LLMRequest

_CID = "test-api-base-routing"
_DIAL_ENDPOINT = "https://ai-proxy.lab.epam.com"
_DIAL_API_VERSION = "2024-02-01"


def _request(*, provider: str = "openai", model: str = "gpt-4o") -> LLMRequest:
    return LLMRequest(
        schema_version=1,
        correlation_id=_CID,
        idempotency_key=None,
        provider=provider,
        model=model,
        messages=[
            Message(
                schema_version=1,
                correlation_id=_CID,
                idempotency_key=None,
                role="user",  # type: ignore[arg-type]
                content="hello",
            )
        ],
        max_tokens=100,
        temperature=0.0,
        compression_hint="none",  # type: ignore[arg-type]
    )


def _completion_response() -> MagicMock:
    usage = MagicMock()
    usage.model_dump.return_value = {"prompt_tokens": 5, "completion_tokens": 7}
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = "hi-back"
    resp = MagicMock()
    resp.id = "resp-api-base-1"
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _final_stream_chunk() -> MagicMock:
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.delta.content = ""
    usage = MagicMock()
    usage.model_dump.return_value = {"prompt_tokens": 3, "completion_tokens": 4}
    chunk = MagicMock()
    chunk.choices = [choice]
    chunk.usage = usage
    return chunk


def test_call_threads_api_base_override_into_litellm_completion() -> None:
    """call() threads the per-provider api_base override into litellm.completion()."""
    adapter = LiteLLMAdapter(
        api_keys={"openai": "test-key"},
        api_base_overrides={"openai": _DIAL_ENDPOINT},
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = _completion_response()
        adapter.call(_request(provider="openai"))
    assert mock_completion.call_args.kwargs["api_base"] == _DIAL_ENDPOINT


def test_call_threads_api_version_override_into_litellm_completion() -> None:
    """call() threads per-provider api_version for Azure-shaped DIAL calls."""
    adapter = LiteLLMAdapter(
        api_keys={"azure": "test-key"},
        api_base_overrides={"azure": _DIAL_ENDPOINT},
        api_version_overrides={"azure": _DIAL_API_VERSION},
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = _completion_response()
        adapter.call(_request(provider="azure"))
    assert mock_completion.call_args.kwargs["api_base"] == _DIAL_ENDPOINT
    assert mock_completion.call_args.kwargs["api_version"] == _DIAL_API_VERSION


def test_call_api_base_is_none_when_provider_not_overridden() -> None:
    """An absent override yields api_base=None — the LiteLLM provider default
    (backward-compatible)."""
    adapter = LiteLLMAdapter(api_keys={"anthropic": "test-key"})
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = _completion_response()
        adapter.call(_request(provider="anthropic", model="claude-haiku-4-5"))
    assert mock_completion.call_args.kwargs["api_base"] is None
    assert mock_completion.call_args.kwargs["api_version"] is None


def test_stream_threads_api_base_override_into_litellm_completion() -> None:
    """stream() threads the per-provider api_base override into litellm.completion()."""
    adapter = LiteLLMAdapter(api_base_overrides={"openai": _DIAL_ENDPOINT})
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = iter([_final_stream_chunk()])
        list(adapter.stream(_request(provider="openai")))
    assert mock_completion.call_args.kwargs["api_base"] == _DIAL_ENDPOINT


def test_stream_threads_api_version_override_into_litellm_completion() -> None:
    """stream() threads per-provider api_version for Azure-shaped DIAL calls."""
    adapter = LiteLLMAdapter(
        api_base_overrides={"azure": _DIAL_ENDPOINT},
        api_version_overrides={"azure": _DIAL_API_VERSION},
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = iter([_final_stream_chunk()])
        list(adapter.stream(_request(provider="azure")))
    assert mock_completion.call_args.kwargs["api_base"] == _DIAL_ENDPOINT
    assert mock_completion.call_args.kwargs["api_version"] == _DIAL_API_VERSION
