"""Unit tests — HaikuProvider (LLMProxyPort-backed compression provider).

No real API calls are made. The LLMProxyPort is mocked.

Covers:
- compress() happy path — LLMRequest shape + response mapping
- compress() proxy exception → CavemanProviderError
- compress() port-scoped error (VerdacaPortError subclass) → CavemanProviderError
- compress() pins the model; honours a custom model
- compress_with_fix() delegates to compress() with the fix-prompt structure
- compress_with_fix() → CavemanProviderError propagates
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from praxis.ports.common import TransientError

from praxis.kernel.compression.caveman.errors import CavemanProviderError
from praxis.kernel.compression.caveman.provider import HAIKU_MODEL, HaikuProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text="compressed text", input_tokens=100, output_tokens=30):
    response = MagicMock()
    response.content = text
    response.input_tokens = input_tokens
    response.output_tokens = output_tokens
    return response


def _proxy_returning(response):
    proxy = MagicMock()
    proxy.call.return_value = response
    return proxy


# ---------------------------------------------------------------------------
# compress()
# ---------------------------------------------------------------------------

class TestHaikuProviderCompress:
    @pytest.mark.asyncio
    async def test_compress_happy_path(self):
        proxy = _proxy_returning(_mock_response("short terse version", 100, 25))
        provider = HaikuProvider(proxy)

        text, in_tok, out_tok = await provider.compress("long text here", "system prompt")

        assert (text, in_tok, out_tok) == ("short terse version", 100, 25)
        req = proxy.call.call_args.args[0]
        assert req.model == HAIKU_MODEL
        assert req.provider == "anthropic"
        assert req.max_tokens == 8096
        assert req.temperature == 0.0
        assert req.compression_hint == "none"
        assert [(m.role, m.content) for m in req.messages] == [
            ("system", "system prompt"),
            ("user", "long text here"),
        ]

    @pytest.mark.asyncio
    async def test_compress_proxy_exception_raises_provider_error(self):
        proxy = MagicMock()
        proxy.call.side_effect = RuntimeError("API timeout")

        with pytest.raises(CavemanProviderError, match="Haiku LLMProxy call failed"):
            await HaikuProvider(proxy).compress("text", "prompt")

    @pytest.mark.asyncio
    async def test_compress_port_error_raises_provider_error(self):
        proxy = MagicMock()
        proxy.call.side_effect = TransientError(
            port_name="llm_proxy",
            correlation_id="c",
            occurred_at=datetime.now(UTC),
        )

        with pytest.raises(CavemanProviderError):
            await HaikuProvider(proxy).compress("text", "prompt")

    @pytest.mark.asyncio
    async def test_compress_uses_pinned_model(self):
        proxy = _proxy_returning(_mock_response())

        await HaikuProvider(proxy).compress("text", "prompt")

        assert proxy.call.call_args.args[0].model == HAIKU_MODEL

    @pytest.mark.asyncio
    async def test_compress_custom_model(self):
        proxy = _proxy_returning(_mock_response())

        await HaikuProvider(proxy, model="claude-test-model").compress("text", "prompt")

        assert proxy.call.call_args.args[0].model == "claude-test-model"


# ---------------------------------------------------------------------------
# compress_with_fix()
# ---------------------------------------------------------------------------

class TestHaikuProviderCompressWithFix:
    @pytest.mark.asyncio
    async def test_compress_with_fix_calls_compress(self):
        proxy = _proxy_returning(_mock_response("fixed version", 150, 40))

        text, in_tok, out_tok = await HaikuProvider(proxy).compress_with_fix(
            original="original text",
            compressed="bad compressed text",
            errors=["polarity_flip", "number_drop"],
            system_prompt="be terse",
        )

        assert text == "fixed version"
        assert in_tok == 150
        # The fix-prompt user message must carry the original text and the errors.
        user_content = proxy.call.call_args.args[0].messages[1].content
        assert "original text" in user_content
        assert "polarity_flip" in user_content
        assert "number_drop" in user_content

    @pytest.mark.asyncio
    async def test_compress_with_fix_propagates_provider_error(self):
        proxy = MagicMock()
        proxy.call.side_effect = RuntimeError("network error")

        with pytest.raises(CavemanProviderError):
            await HaikuProvider(proxy).compress_with_fix(
                original="original",
                compressed="compressed",
                errors=["some_error"],
                system_prompt="prompt",
            )
