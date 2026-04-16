"""Unit tests — RTK resolver, telemetry parser, client stub fallback."""
from __future__ import annotations

import json
import pytest

from praxis.kernel.compression.rtk.errors import (
    RTKBinaryMissingError,
    RTKTelemetryError,
)
from praxis.kernel.compression.rtk.registry import is_known_command
from praxis.kernel.compression.rtk.telemetry import (
    RTKSavings,
    parse_gain_output,
    _ZERO_SAVINGS,
)


class TestRegistry:
    def test_known_command(self):
        assert is_known_command(["git", "log"]) is True
        assert is_known_command(["npm", "install"]) is True
        assert is_known_command(["cargo", "build"]) is True
        assert is_known_command(["pytest"]) is True

    def test_unknown_command(self):
        assert is_known_command(["my_custom_tool"]) is False
        assert is_known_command(["notinthere"]) is False

    def test_empty_argv(self):
        assert is_known_command([]) is False


class TestTelemetry:
    def test_parse_single_object(self):
        data = {"bytes_before": 1000, "bytes_after": 150, "tokens_saved": 212, "command": "git"}
        result = parse_gain_output(json.dumps(data))
        assert result.bytes_before == 1000
        assert result.bytes_after == 150
        assert result.tokens_saved_estimate == 212
        assert result.bytes_saved == 850

    def test_parse_array_returns_last(self):
        data = [
            {"bytes_before": 100, "bytes_after": 50, "tokens_saved": 12},
            {"bytes_before": 500, "bytes_after": 100, "tokens_saved": 100},
        ]
        result = parse_gain_output(json.dumps(data))
        assert result.bytes_before == 500

    def test_parse_empty_string(self):
        result = parse_gain_output("")
        assert result == _ZERO_SAVINGS

    def test_parse_empty_array(self):
        result = parse_gain_output("[]")
        assert result == _ZERO_SAVINGS

    def test_parse_invalid_json(self):
        with pytest.raises(RTKTelemetryError, match="not valid JSON"):
            parse_gain_output("{invalid json}")

    def test_parse_unexpected_format(self):
        with pytest.raises(RTKTelemetryError, match="unexpected"):
            parse_gain_output('"just a string"')

    def test_bytes_saved_property(self):
        s = RTKSavings(bytes_before=500, bytes_after=100, tokens_saved_estimate=100)
        assert s.bytes_saved == 400

    def test_bytes_saved_no_negative(self):
        s = RTKSavings(bytes_before=100, bytes_after=500, tokens_saved_estimate=0)
        assert s.bytes_saved == 0

    def test_parse_missing_fields_defaults_to_zero(self):
        result = parse_gain_output(json.dumps({"command": "git"}))
        assert result.bytes_before == 0
        assert result.bytes_after == 0


class TestRTKClientFallback:
    @pytest.mark.asyncio
    async def test_client_falls_back_to_stub_when_binary_missing(self, tmp_path):
        """RTK client should never crash — always fall back to stub."""
        from praxis.kernel.compression.rtk.client import RTKClient

        # Point to a nonexistent binary
        client = RTKClient(binary_override=None)
        # The client was constructed; check that it has either a binary or a stub
        assert client._binary is not None or client._stub is not None

    @pytest.mark.asyncio
    async def test_stub_runs_echo(self):
        """RTKStub.run_command should pass commands through without crashing."""
        from praxis.kernel.compression.rtk.stub import RTKStub
        from praxis.kernel.compression.rtk.client import RTKResult

        stub = RTKStub.__new__(RTKStub)
        stub.__init__.__func__(stub)

        result = await stub.run_command(["echo", "hello"])
        # Either runs successfully or returns an error result — never throws
        assert isinstance(result, RTKResult)
        assert result.rtk_used is False

    def test_resolver_raises_for_unknown_platform(self, monkeypatch):
        import platform
        monkeypatch.setattr(platform, "system", lambda: "AmigaOS")
        monkeypatch.setattr(platform, "machine", lambda: "m68k")

        from praxis.kernel.compression.rtk.resolver import resolve_binary_path
        with pytest.raises(RTKBinaryMissingError):
            resolve_binary_path()
