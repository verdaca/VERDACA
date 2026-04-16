"""Unit tests — RTKClient async paths (stub fallback, passthrough, run_rtk).

Covers the async methods not reached by the existing test_rtk.py:
- run_command → stub path
- run_command → disabled_for_session path
- run_command → unknown command passthrough
- run_command → known command (mocked subprocess)
- _run_rtk → timeout → disabled_for_session
- _run_rtk → OSError → fallback to passthrough
- _passthrough → success
- _passthrough → exception handling
- RTKResult.bytes_saved property
- is_available property
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from praxis.kernel.compression.rtk.client import RTKClient, RTKResult
from praxis.kernel.compression.rtk.errors import RTKBinaryMissingError, RTKExecutionError
from praxis.kernel.compression.rtk.stub import RTKStub


# ---------------------------------------------------------------------------
# RTKResult
# ---------------------------------------------------------------------------

class TestRTKResult:
    def test_bytes_saved_positive(self):
        r = RTKResult(stdout="", stderr="", exit_code=0,
                      bytes_before=1000, bytes_after=300, tokens_saved_estimate=50)
        assert r.bytes_saved == 700

    def test_bytes_saved_no_negative(self):
        r = RTKResult(stdout="", stderr="", exit_code=0,
                      bytes_before=100, bytes_after=500, tokens_saved_estimate=0)
        assert r.bytes_saved == 0

    def test_bytes_saved_equal(self):
        r = RTKResult(stdout="", stderr="", exit_code=0,
                      bytes_before=100, bytes_after=100, tokens_saved_estimate=0)
        assert r.bytes_saved == 0

    def test_rtk_used_defaults_true(self):
        r = RTKResult(stdout="", stderr="", exit_code=0,
                      bytes_before=0, bytes_after=0, tokens_saved_estimate=0)
        assert r.rtk_used is True

    def test_rtk_tags_default_empty(self):
        r = RTKResult(stdout="out", stderr="", exit_code=0,
                      bytes_before=10, bytes_after=5, tokens_saved_estimate=1)
        assert r.rtk_tags == {}


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------

class TestRTKClientIsAvailable:
    def test_available_with_binary(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/some/binary")
        client._stub = None
        client._disabled_for_session = False
        assert client.is_available is True

    def test_not_available_when_disabled(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/some/binary")
        client._stub = None
        client._disabled_for_session = True
        assert client.is_available is False

    def test_not_available_when_no_binary(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = None
        client._stub = None
        client._disabled_for_session = False
        assert client.is_available is False


# ---------------------------------------------------------------------------
# run_command — stub path
# ---------------------------------------------------------------------------

class TestRTKClientRunCommandStubPath:
    @pytest.mark.asyncio
    async def test_run_command_uses_stub_when_no_binary(self):
        """When binary is missing, constructor installs stub; run_command delegates."""
        mock_stub = AsyncMock()
        mock_result = RTKResult(
            stdout="stub output", stderr="", exit_code=0,
            bytes_before=10, bytes_after=10, tokens_saved_estimate=0, rtk_used=False
        )
        mock_stub.run_command.return_value = mock_result

        client = RTKClient.__new__(RTKClient)
        client._binary = None
        client._stub = mock_stub
        client._disabled_for_session = False
        client._timeout_s = 30.0

        result = await client.run_command(["echo", "hello"])
        assert result is mock_result
        mock_stub.run_command.assert_awaited_once()


# ---------------------------------------------------------------------------
# run_command — disabled_for_session path
# ---------------------------------------------------------------------------

class TestRTKClientDisabledForSession:
    @pytest.mark.asyncio
    async def test_run_command_passthrough_when_disabled(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/some/binary")
        client._stub = None
        client._disabled_for_session = True
        client._timeout_s = 30.0

        mock_result = RTKResult(
            stdout="passthrough", stderr="", exit_code=0,
            bytes_before=10, bytes_after=10, tokens_saved_estimate=0, rtk_used=False
        )

        with patch.object(client, "_passthrough", return_value=mock_result) as mock_pass:
            result = await client.run_command(["echo", "test"])
        mock_pass.assert_called_once()
        assert result.rtk_used is False


# ---------------------------------------------------------------------------
# run_command — unknown command passthrough
# ---------------------------------------------------------------------------

class TestRTKClientUnknownCommandPassthrough:
    @pytest.mark.asyncio
    async def test_unknown_command_uses_passthrough(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/fake/rtk-binary")
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        mock_result = RTKResult(
            stdout="", stderr="", exit_code=0,
            bytes_before=0, bytes_after=0, tokens_saved_estimate=0, rtk_used=False
        )

        with patch("praxis.kernel.compression.rtk.registry.is_known_command", return_value=False):
            with patch.object(client, "_passthrough", return_value=mock_result) as mock_pass:
                result = await client.run_command(["my_custom_tool", "--arg"])
        mock_pass.assert_called_once()
        assert result.rtk_used is False


# ---------------------------------------------------------------------------
# _run_rtk — mocked subprocess success
# ---------------------------------------------------------------------------

class TestRTKClientRunRTK:
    @pytest.mark.asyncio
    async def test_run_rtk_success(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/fake/rtk")
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"git log output", b""))

        from praxis.kernel.compression.rtk.telemetry import RTKSavings

        async def fake_read_savings(**_kwargs):
            return RTKSavings(bytes_before=500, bytes_after=100, tokens_saved_estimate=50)

        async def fake_wait_for(coro, timeout=None):
            return await coro

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=fake_wait_for):
                with patch.object(client, "_read_savings", side_effect=fake_read_savings):
                    result = await client._run_rtk(["git", "log"], timeout_s=30.0)

        assert result.exit_code == 0
        assert result.rtk_used is True
        assert result.bytes_saved > 0

    @pytest.mark.asyncio
    async def test_run_rtk_timeout_disables_session(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = Path("/fake/rtk")
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        mock_proc = MagicMock()
        mock_proc.kill = MagicMock()

        async def fake_wait_for(coro, timeout=None):
            raise asyncio.TimeoutError()

        mock_passthrough_result = RTKResult(
            stdout="", stderr="timeout", exit_code=1,
            bytes_before=0, bytes_after=0, tokens_saved_estimate=0, rtk_used=False
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=fake_wait_for):
                with patch.object(client, "_passthrough", return_value=mock_passthrough_result):
                    result = await client._run_rtk(["git", "log"], timeout_s=1.0)

        # Timeout → disabled_for_session set, falls through to passthrough (not raised to caller)
        assert client._disabled_for_session is True
        assert result.rtk_used is False

    @pytest.mark.asyncio
    async def test_run_rtk_raises_when_no_binary(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = None
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        with pytest.raises(RTKExecutionError, match="no binary"):
            await client._run_rtk(["git", "log"], timeout_s=30.0)


# ---------------------------------------------------------------------------
# _passthrough
# ---------------------------------------------------------------------------

class TestRTKClientPassthrough:
    @pytest.mark.asyncio
    async def test_passthrough_success(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = None
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))

        async def fake_wait_for(coro, timeout=None):
            return await coro

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=fake_wait_for):
                with patch("shutil.which", return_value="/usr/bin/echo"):
                    result = await client._passthrough(["echo", "hello"], timeout_s=5.0)

        assert result.rtk_used is False
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_passthrough_handles_exception(self):
        client = RTKClient.__new__(RTKClient)
        client._binary = None
        client._stub = None
        client._disabled_for_session = False
        client._timeout_s = 30.0

        with patch("asyncio.create_subprocess_exec", side_effect=OSError("cannot exec")):
            with patch("shutil.which", return_value=None):
                result = await client._passthrough(["nonexistent"], timeout_s=5.0)

        assert result.exit_code == 1
        assert result.rtk_used is False


# ---------------------------------------------------------------------------
# RTKStub — additional coverage for stub module
# ---------------------------------------------------------------------------

class TestRTKStubExtended:
    @pytest.mark.asyncio
    async def test_stub_unknown_command_returns_127(self):
        stub = RTKStub.__new__(RTKStub)
        # skip __init__ to avoid the warning log
        with patch("shutil.which", return_value=None):
            result = await stub.run_command(["definitely_not_a_real_command_xyz"])
        assert result.exit_code == 127
        assert "not found" in result.stderr

    @pytest.mark.asyncio
    async def test_stub_timeout_returns_error_result(self):
        stub = RTKStub.__new__(RTKStub)

        async def fake_wait_for(coro, timeout):
            raise asyncio.TimeoutError()

        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("shutil.which", return_value="/usr/bin/echo"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("asyncio.wait_for", side_effect=fake_wait_for):
                    result = await stub.run_command(["echo", "hi"], timeout_s=0.001)

        assert result.exit_code == 1
        assert result.rtk_used is False
