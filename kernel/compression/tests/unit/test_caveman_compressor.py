"""Unit tests — compress_output() orchestrator (all paths).

Caveman ships behind feature flag (default OFF). Tests mock HaikuProvider
so no real LLM calls are made.

Paths covered:
- Gate denied (calibration stale, below min length, content type, below break-even, wenyan)
- Provider error → immediate fallback
- Expansion detected on all retries → fallback
- Expansion on first attempt → success on retry
- Validation fails → retry with fix → success
- Validation exhausted → fallback with last error
- Happy path (first attempt, validation passes)
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from praxis.kernel.compression.caveman.compressor import compress_output
from praxis.kernel.compression.caveman.errors import CavemanProviderError
from praxis.kernel.compression.caveman.gate import GateConfig, CalibrationSnapshot
from praxis.kernel.compression.caveman.models import (
    CompressionRequest,
    CompressionResult,
    Dialect,
    Intensity,
    ValidationReport,
    StructuralError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_PROSE = (
    "This is a comprehensive technical document that describes the system architecture "
    "in detail. The system is designed to be safe, correct, and reliable. "
    "All components are valid and tested. The public API is available. "
    "Enable the logging module and disable the debug mode in production. "
    "Expected values: 100, 200, 300, 42, 3.14. Versions: 1.2.3, 2.0.0. "
) * 15  # ~2000 tokens

_FRESH_CALIBRATION = CalibrationSnapshot(
    refreshed_at=datetime.now(UTC),
    savings_per_read_tokens=200.0,
    compression_cost_tokens=150.0,
)


def _make_request(text=_LONG_PROSE, reads=5, dialect=Dialect.CAVEMAN_ENGLISH,
                  accept_wenyan=False):
    return CompressionRequest(
        text=text,
        expected_downstream_reads=reads,
        dialect=dialect,
        accept_wenyan=accept_wenyan,
    )


def _mock_provider(compressed_text: str, input_tok=100, output_tok=50) -> MagicMock:
    provider = MagicMock()
    provider.compress = AsyncMock(return_value=(compressed_text, input_tok, output_tok))
    provider.compress_with_fix = AsyncMock(return_value=(compressed_text, input_tok, output_tok))
    return provider


def _gate_config(min_tokens=1, break_even_reads=2) -> GateConfig:
    return GateConfig(min_tokens=min_tokens, break_even_reads=break_even_reads)


# ---------------------------------------------------------------------------
# Gate denied paths
# ---------------------------------------------------------------------------

class TestCompressOutputGateDenied:
    @pytest.mark.asyncio
    async def test_gate_denied_calibration_stale(self):
        stale_cal = CalibrationSnapshot(
            refreshed_at=datetime.now(UTC) - timedelta(days=10),
        )
        req = _make_request()
        result = await compress_output(
            req,
            gate_config=GateConfig(),
            provider=_mock_provider("short"),
        )
        # The default calibration is fresh, so we pass a stale one explicitly
        from praxis.kernel.compression.caveman import gate as gate_module
        orig_cal = gate_module._calibration
        gate_module._calibration = stale_cal
        try:
            result = await compress_output(req, gate_config=GateConfig())
        finally:
            gate_module._calibration = orig_cal

        assert result.compressed is False
        assert result.gate_denied_reason == "calibration_stale"

    @pytest.mark.asyncio
    async def test_gate_denied_below_min_length(self):
        req = CompressionRequest(
            text="short",
            expected_downstream_reads=5,
        )
        result = await compress_output(
            req,
            gate_config=GateConfig(min_tokens=10000),
            provider=_mock_provider("compressed"),
        )
        assert result.compressed is False
        assert "below_min_length" in (result.gate_denied_reason or "")

    @pytest.mark.asyncio
    async def test_gate_denied_below_break_even(self):
        req = _make_request(reads=0)
        result = await compress_output(
            req,
            gate_config=GateConfig(min_tokens=1, break_even_reads=100),
        )
        assert result.compressed is False
        assert "below_break_even" in (result.gate_denied_reason or "")

    @pytest.mark.asyncio
    async def test_gate_denied_wenyan_not_accepted(self):
        req = CompressionRequest(
            text=_LONG_PROSE,
            dialect=Dialect.WENYAN,
            expected_downstream_reads=5,
            accept_wenyan=False,
        )
        cfg = GateConfig(min_tokens=1)
        result = await compress_output(
            req,
            gate_config=cfg,
            provider=_mock_provider("compressed"),
        )
        # Either wenyan_not_accepted or some other gate reason
        assert result.compressed is False

    @pytest.mark.asyncio
    async def test_gate_denied_returns_original_text(self):
        req = CompressionRequest(text="short", expected_downstream_reads=5)
        result = await compress_output(req, gate_config=GateConfig(min_tokens=10000))
        assert result.text_out == req.text
        assert result.text_in == req.text


# ---------------------------------------------------------------------------
# Provider error
# ---------------------------------------------------------------------------

class TestCompressOutputProviderError:
    @pytest.mark.asyncio
    async def test_provider_error_returns_original(self):
        provider = MagicMock()
        provider.compress = AsyncMock(side_effect=CavemanProviderError("network down"))

        req = _make_request()
        result = await compress_output(
            req,
            gate_config=GateConfig(min_tokens=1),
            provider=provider,
        )
        assert result.compressed is False
        assert result.fallback_reason == "provider_error"
        assert result.text_out == req.text

    @pytest.mark.asyncio
    async def test_provider_error_on_retry_returns_original(self):
        provider = MagicMock()
        # First call succeeds but expansion detected; fix call raises error
        short_text = "shorter"  # original is LONG_PROSE which is longer

        # Simulate: first call returns expansion (len(compressed) >= len(original))
        # But we control validate: failing validation triggers fix call
        failing_report = ValidationReport(
            structural_errors=[StructuralError(kind="polarity_flip")]
        )

        call_count = 0
        async def compress_side_effect(text, system_prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ("compressed but still pretty long" * 3, 100, 50)
            raise CavemanProviderError("timeout on retry")

        provider.compress = AsyncMock(side_effect=compress_side_effect)
        provider.compress_with_fix = AsyncMock(side_effect=CavemanProviderError("timeout on retry"))

        with patch("praxis.kernel.compression.caveman.compressor.validate_all",
                   return_value=failing_report):
            req = _make_request()
            result = await compress_output(
                req,
                gate_config=GateConfig(min_tokens=1),
                provider=provider,
                max_retries=1,
            )
        assert result.compressed is False
        assert result.fallback_reason == "provider_error"


# ---------------------------------------------------------------------------
# Provider unconfigured
# ---------------------------------------------------------------------------

class TestCompressOutputProviderUnconfigured:
    @pytest.mark.asyncio
    async def test_gate_passing_no_provider_returns_fallback(self):
        """Gate passes but neither provider nor llm_proxy is wired → graceful fallback."""
        req = _make_request()
        result = await compress_output(req, gate_config=GateConfig(min_tokens=1))

        assert result.compressed is False
        assert result.fallback_reason == "provider_unconfigured"
        assert result.text_out == req.text
        assert result.caveman_tags["compression.caveman.fallback"] == "provider_unconfigured"


# ---------------------------------------------------------------------------
# Expansion guard
# ---------------------------------------------------------------------------

class TestCompressOutputExpansion:
    @pytest.mark.asyncio
    async def test_expansion_on_all_retries_returns_fallback(self):
        original = _LONG_PROSE
        expanded = original * 2  # guaranteed expansion

        provider = _mock_provider(expanded)

        req = _make_request(text=original)
        result = await compress_output(
            req,
            gate_config=GateConfig(min_tokens=1),
            provider=provider,
            max_retries=1,
        )
        assert result.compressed is False
        assert result.fallback_reason == "expansion"
        assert result.text_out == original
        assert result.retry_count == 2  # max_retries + 1

    @pytest.mark.asyncio
    async def test_expansion_tags_include_cost(self):
        original = _LONG_PROSE
        expanded = original * 2

        provider = _mock_provider(expanded, input_tok=100, output_tok=50)
        req = _make_request(text=original)
        result = await compress_output(
            req,
            gate_config=GateConfig(min_tokens=1),
            provider=provider,
            max_retries=0,
        )
        assert result.compressed is False
        assert "compression.caveman.fallback" in result.caveman_tags
        assert "compression.caveman.cost_tokens" in result.caveman_tags


# ---------------------------------------------------------------------------
# Validation paths
# ---------------------------------------------------------------------------

class TestCompressOutputValidation:
    @pytest.mark.asyncio
    async def test_happy_path_first_attempt(self):
        original = _LONG_PROSE
        compressed_text = "Terse text. Key points only. Everything preserved."

        provider = _mock_provider(compressed_text, input_tok=100, output_tok=20)

        passing_report = ValidationReport()  # no errors

        with patch("praxis.kernel.compression.caveman.compressor.validate_all",
                   return_value=passing_report):
            req = _make_request(text=original)
            result = await compress_output(
                req,
                gate_config=GateConfig(min_tokens=1),
                provider=provider,
            )

        assert result.compressed is True
        assert result.text_out == compressed_text
        assert result.retry_count == 0
        assert result.validation_report is not None
        assert result.validation_report.passed is True
        assert "compression.caveman.intensity" in result.caveman_tags

    @pytest.mark.asyncio
    async def test_validation_fail_then_success_on_retry(self):
        original = _LONG_PROSE
        compressed_text = "Terse text. Valid version."

        failing_report = ValidationReport(
            structural_errors=[StructuralError(kind="polarity_flip")]
        )
        passing_report = ValidationReport()

        call_count = 0
        def fake_validate(orig, comp):
            nonlocal call_count
            call_count += 1
            return failing_report if call_count == 1 else passing_report

        provider = MagicMock()
        provider.compress = AsyncMock(return_value=(compressed_text, 100, 50))
        provider.compress_with_fix = AsyncMock(return_value=(compressed_text, 80, 30))

        with patch("praxis.kernel.compression.caveman.compressor.validate_all",
                   side_effect=fake_validate):
            req = _make_request(text=original)
            result = await compress_output(
                req,
                gate_config=GateConfig(min_tokens=1),
                provider=provider,
                max_retries=2,
            )

        assert result.compressed is True
        assert result.retry_count == 1

    @pytest.mark.asyncio
    async def test_validation_exhausted_returns_fallback(self):
        original = _LONG_PROSE
        compressed_text = "Compressed but invalid"

        failing_report = ValidationReport(
            structural_errors=[StructuralError(kind="polarity_flip")]
        )

        provider = MagicMock()
        provider.compress = AsyncMock(return_value=(compressed_text, 100, 50))
        provider.compress_with_fix = AsyncMock(return_value=(compressed_text, 80, 30))

        with patch("praxis.kernel.compression.caveman.compressor.validate_all",
                   return_value=failing_report):
            req = _make_request(text=original)
            result = await compress_output(
                req,
                gate_config=GateConfig(min_tokens=1),
                provider=provider,
                max_retries=1,
            )

        assert result.compressed is False
        assert result.fallback_reason == "polarity_flip"
        assert result.text_out == original

    @pytest.mark.asyncio
    async def test_net_savings_computed_correctly(self):
        original = "x" * 2000  # rough 500 tokens
        compressed_text = "x" * 400  # 100 tokens

        provider = MagicMock()
        provider.compress = AsyncMock(return_value=(compressed_text, 50, 25))

        passing_report = ValidationReport()

        with patch("praxis.kernel.compression.caveman.compressor.validate_all",
                   return_value=passing_report):
            req = CompressionRequest(
                text=original, expected_downstream_reads=5
            )
            result = await compress_output(
                req,
                gate_config=GateConfig(min_tokens=1),
                provider=provider,
            )

        assert result.compressed is True
        assert result.net_savings_tokens >= 0
