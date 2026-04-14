"""Unit tests — TONL tokenizer adapters and factory.

Covers: base Protocol, GenericTokenizer, AnthropicTokenizer, OpenAITokenizer,
        and the get_tokenizer() factory.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from praxis.kernel.compression.tonl.tokenizers.base import Tokenizer
from praxis.kernel.compression.tonl.tokenizers.generic import GenericTokenizer
from praxis.kernel.compression.tonl.tokenizers.anthropic import AnthropicTokenizer
from praxis.kernel.compression.tonl.tokenizers.openai import OpenAITokenizer
from praxis.kernel.compression.tonl.tokenizers import get_tokenizer


# ---------------------------------------------------------------------------
# GenericTokenizer
# ---------------------------------------------------------------------------

class TestGenericTokenizer:
    def setup_method(self):
        self.tok = GenericTokenizer()

    def test_count_basic(self):
        # "Hello" = 5 chars → round(5/4) = 1
        assert self.tok.count("Hello") == 1

    def test_count_minimum_one(self):
        assert self.tok.count("") == 1
        assert self.tok.count("x") == 1

    def test_count_longer_text(self):
        text = "a" * 40  # 40 chars → round(40/4) = 10
        assert self.tok.count(text) == 10

    def test_count_approximation(self):
        text = "The quick brown fox jumps over the lazy dog"
        count = self.tok.count(text)
        assert count > 0
        assert count <= len(text)

    def test_encode_bytes_returns_utf8(self):
        result = self.tok.encode_bytes("hello")
        assert result == b"hello"

    def test_encode_bytes_unicode(self):
        result = self.tok.encode_bytes("caf\u00e9")
        assert result == "caf\u00e9".encode("utf-8")

    def test_byte_boundary_positions_empty(self):
        positions = self.tok.byte_boundary_positions("")
        assert positions == []

    def test_byte_boundary_positions_short(self):
        positions = self.tok.byte_boundary_positions("abcdefghijklmnop")
        assert isinstance(positions, list)
        assert all(isinstance(p, int) for p in positions)
        assert positions[0] == 0

    def test_byte_boundary_positions_spacing(self):
        text = "a" * 16
        positions = self.tok.byte_boundary_positions(text)
        assert len(positions) == 4  # 16 bytes / 4-byte step = 4 boundaries

    def test_implements_protocol(self):
        assert isinstance(self.tok, Tokenizer)

    def test_name_and_version_class_vars(self):
        assert GenericTokenizer.name == "generic"
        assert "heuristic" in GenericTokenizer.version


# ---------------------------------------------------------------------------
# AnthropicTokenizer
# ---------------------------------------------------------------------------

class TestAnthropicTokenizer:
    def test_name_and_version(self):
        assert AnthropicTokenizer.name == "anthropic"
        assert AnthropicTokenizer.version != ""

    def test_falls_back_to_generic_when_sdk_absent(self):
        tok = AnthropicTokenizer()
        # Force SDK unavailable by making import fail
        with patch.dict("sys.modules", {"anthropic": None}):
            tok._sdk_available = False
            tok._client = None
            result = tok.count("hello world this is a test sentence")
        assert result >= 1

    def test_count_uses_fallback_when_sdk_unavailable(self):
        tok = AnthropicTokenizer()
        tok._sdk_available = False
        tok._client = None
        text = "a" * 20
        fallback = GenericTokenizer()
        assert tok.count(text) == fallback.count(text)

    def test_count_uses_sdk_when_available(self):
        tok = AnthropicTokenizer()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.input_tokens = 7
        mock_client.messages.count_tokens.return_value = mock_response
        tok._client = mock_client
        tok._sdk_available = True

        mock_anthropic = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = tok.count("hello world test")
        assert result == 7
        mock_client.messages.count_tokens.assert_called_once()

    def test_count_falls_back_on_api_error(self):
        tok = AnthropicTokenizer()
        mock_client = MagicMock()
        mock_client.messages.count_tokens.side_effect = RuntimeError("network error")
        tok._client = mock_client
        tok._sdk_available = True

        # Should not raise; falls back to heuristic
        result = tok.count("hello")
        assert result >= 1

    def test_encode_bytes(self):
        tok = AnthropicTokenizer()
        assert tok.encode_bytes("test") == b"test"

    def test_byte_boundary_positions_delegates_to_fallback(self):
        tok = AnthropicTokenizer()
        fallback = GenericTokenizer()
        text = "abcdefghijklmnop"
        assert tok.byte_boundary_positions(text) == fallback.byte_boundary_positions(text)

    def test_get_client_caches_result(self):
        tok = AnthropicTokenizer()
        mock_module = MagicMock()
        mock_module.Anthropic.return_value = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_module}):
            tok._sdk_available = None
            tok._client = None
            client1 = tok._get_client()
            client2 = tok._get_client()
        assert client1 is client2

    def test_get_client_handles_import_error(self):
        tok = AnthropicTokenizer()
        tok._sdk_available = None
        tok._client = None
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            result = tok._get_client()
        assert result is None
        assert tok._sdk_available is False


# ---------------------------------------------------------------------------
# OpenAITokenizer
# ---------------------------------------------------------------------------

class TestOpenAITokenizer:
    def test_name_and_version(self):
        assert OpenAITokenizer.name == "openai"
        assert OpenAITokenizer.version != ""

    def test_falls_back_when_tiktoken_absent(self):
        tok = OpenAITokenizer()
        tok._sdk_available = False
        tok._enc = None
        text = "a" * 20
        fallback = GenericTokenizer()
        assert tok.count(text) == fallback.count(text)

    def test_count_uses_tiktoken_when_available(self):
        tok = OpenAITokenizer()
        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1, 2, 3, 4, 5]
        tok._enc = mock_enc
        tok._sdk_available = True

        assert tok.count("hello world") == 5

    def test_count_falls_back_on_encode_error(self):
        tok = OpenAITokenizer()
        mock_enc = MagicMock()
        mock_enc.encode.side_effect = RuntimeError("encode failed")
        tok._enc = mock_enc
        tok._sdk_available = True

        result = tok.count("hello")
        assert result >= 1

    def test_encode_bytes_uses_tiktoken(self):
        tok = OpenAITokenizer()
        mock_enc = MagicMock()
        mock_enc.encode.return_value = [104, 101, 108]
        tok._enc = mock_enc
        tok._sdk_available = True

        result = tok.encode_bytes("hel")
        assert isinstance(result, bytes)

    def test_encode_bytes_fallback(self):
        tok = OpenAITokenizer()
        tok._sdk_available = False
        tok._enc = None
        assert tok.encode_bytes("test") == b"test"

    def test_byte_boundary_positions_with_tiktoken(self):
        tok = OpenAITokenizer()
        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1, 2, 3, 4]  # 4 tokens
        tok._enc = mock_enc
        tok._sdk_available = True

        text = "a" * 16
        positions = tok.byte_boundary_positions(text)
        assert len(positions) == 4
        assert positions[0] == 0

    def test_byte_boundary_positions_empty_tokens(self):
        tok = OpenAITokenizer()
        mock_enc = MagicMock()
        mock_enc.encode.return_value = []
        tok._enc = mock_enc
        tok._sdk_available = True

        positions = tok.byte_boundary_positions("hello")
        assert positions == []

    def test_byte_boundary_positions_fallback(self):
        tok = OpenAITokenizer()
        tok._sdk_available = False
        tok._enc = None
        fallback = GenericTokenizer()
        text = "abcdefghijklmnop"
        assert tok.byte_boundary_positions(text) == fallback.byte_boundary_positions(text)

    def test_get_enc_caches_result(self):
        tok = OpenAITokenizer()
        mock_module = MagicMock()
        mock_enc = MagicMock()
        mock_module.encoding_for_model.return_value = mock_enc
        with patch.dict("sys.modules", {"tiktoken": mock_module}):
            tok._sdk_available = None
            tok._enc = None
            enc1 = tok._get_enc()
            enc2 = tok._get_enc()
        assert enc1 is enc2

    def test_get_enc_handles_import_error(self):
        tok = OpenAITokenizer()
        tok._sdk_available = None
        tok._enc = None
        with patch.dict("sys.modules", {"tiktoken": None}):
            result = tok._get_enc()
        assert result is None
        assert tok._sdk_available is False


# ---------------------------------------------------------------------------
# get_tokenizer factory
# ---------------------------------------------------------------------------

class TestGetTokenizerFactory:
    def test_none_returns_generic(self):
        tok = get_tokenizer(None)
        assert isinstance(tok, GenericTokenizer)

    def test_generic_name(self):
        tok = get_tokenizer("generic")
        assert isinstance(tok, GenericTokenizer)

    def test_anthropic_name(self):
        tok = get_tokenizer("anthropic")
        assert isinstance(tok, AnthropicTokenizer)

    def test_claude_alias(self):
        tok = get_tokenizer("claude")
        assert isinstance(tok, AnthropicTokenizer)

    def test_openai_name(self):
        tok = get_tokenizer("openai")
        assert isinstance(tok, OpenAITokenizer)

    def test_gpt_alias(self):
        tok = get_tokenizer("gpt")
        assert isinstance(tok, OpenAITokenizer)

    def test_unknown_returns_generic_with_warning(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            tok = get_tokenizer("unknownmodel")
        assert isinstance(tok, GenericTokenizer)
        assert "Unknown tokenizer" in caplog.text
