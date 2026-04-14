"""Unit tests — HaikuProvider (Anthropic SDK wrapper).

No real API calls are made. All SDK interactions are mocked.

Covers:
- _get_client when SDK not installed → CavemanProviderError on compress()
- _get_client caches client
- compress() happy path with mock client
- compress() API exception → CavemanProviderError
- compress_with_fix() delegates to compress() with correct prompt structure
- compress_with_fix() → CavemanProviderError propagates
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from praxis.kernel.compression.caveman.provider import HaikuProvider, HAIKU_MODEL
from praxis.kernel.compression.caveman.errors import CavemanProviderError


# ---------------------------------------------------------------------------
# _get_client
# ---------------------------------------------------------------------------

class TestHaikuProviderGetClient:
    def test_raises_when_sdk_not_installed(self):
        provider = HaikuProvider()
        with patch.dict("sys.modules", {"anthropic": None}):
            provider._client = None
            with pytest.raises(CavemanProviderError, match="SDK not installed"):
                provider._get_client()

    def test_caches_client(self):
        provider = HaikuProvider()
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_module.Anthropic.return_value = mock_client
        with patch.dict("sys.modules", {"anthropic": mock_module}):
            provider._client = None
            c1 = provider._get_client()
            c2 = provider._get_client()
        assert c1 is c2
        assert mock_module.Anthropic.call_count == 1


# ---------------------------------------------------------------------------
# compress()
# ---------------------------------------------------------------------------

class TestHaikuProviderCompress:
    def _make_mock_response(self, text="compressed text", input_tokens=100, output_tokens=30):
        response = MagicMock()
        response.content = [MagicMock(text=text)]
        response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
        return response

    @pytest.mark.asyncio
    async def test_compress_happy_path(self):
        provider = HaikuProvider()
        mock_client = MagicMock()
        mock_response = self._make_mock_response("short terse version", 100, 25)
        mock_client.messages.create.return_value = mock_response
        provider._client = mock_client

        text, in_tok, out_tok = await provider.compress("long text here", "system prompt")

        assert text == "short terse version"
        assert in_tok == 100
        assert out_tok == 25
        mock_client.messages.create.assert_called_once_with(
            model=HAIKU_MODEL,
            max_tokens=8096,
            system="system prompt",
            messages=[{"role": "user", "content": "long text here"}],
        )

    @pytest.mark.asyncio
    async def test_compress_api_exception_raises_provider_error(self):
        provider = HaikuProvider()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API timeout")
        provider._client = mock_client

        with pytest.raises(CavemanProviderError, match="Haiku API call failed"):
            await provider.compress("text", "prompt")

    @pytest.mark.asyncio
    async def test_compress_uses_pinned_model(self):
        provider = HaikuProvider()
        mock_client = MagicMock()
        mock_response = self._make_mock_response()
        mock_client.messages.create.return_value = mock_response
        provider._client = mock_client

        await provider.compress("text", "prompt")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == HAIKU_MODEL

    @pytest.mark.asyncio
    async def test_compress_custom_model(self):
        provider = HaikuProvider(model="claude-test-model")
        mock_client = MagicMock()
        mock_response = self._make_mock_response()
        mock_client.messages.create.return_value = mock_response
        provider._client = mock_client

        await provider.compress("text", "prompt")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-test-model"


# ---------------------------------------------------------------------------
# compress_with_fix()
# ---------------------------------------------------------------------------

class TestHaikuProviderCompressWithFix:
    @pytest.mark.asyncio
    async def test_compress_with_fix_calls_compress(self):
        provider = HaikuProvider()
        mock_client = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text="fixed version")]
        response.usage = MagicMock(input_tokens=150, output_tokens=40)
        mock_client.messages.create.return_value = response
        provider._client = mock_client

        text, in_tok, out_tok = await provider.compress_with_fix(
            original="original text",
            compressed="bad compressed text",
            errors=["polarity_flip", "number_drop"],
            system_prompt="be terse",
        )

        assert text == "fixed version"
        assert in_tok == 150
        # The prompt passed to messages.create should contain both original and errors
        call_args = mock_client.messages.create.call_args
        user_content = call_args.kwargs["messages"][0]["content"]
        assert "original text" in user_content
        assert "polarity_flip" in user_content
        assert "number_drop" in user_content

    @pytest.mark.asyncio
    async def test_compress_with_fix_propagates_provider_error(self):
        provider = HaikuProvider()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("network error")
        provider._client = mock_client

        with pytest.raises(CavemanProviderError):
            await provider.compress_with_fix(
                original="original",
                compressed="compressed",
                errors=["some_error"],
                system_prompt="prompt",
            )
