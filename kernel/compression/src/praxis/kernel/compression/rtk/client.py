"""RTK subprocess wrapper — the Python boundary to the Rust RTK binary."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .errors import RTKBinaryMissingError, RTKExecutionError
from .registry import is_known_command
from .resolver import resolve_binary_path
from .telemetry import RTKSavings, parse_gain_output

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RTKResult:
    """Output from RTKClient.run_command()."""

    stdout: str
    stderr: str
    exit_code: int
    bytes_before: int
    bytes_after: int
    tokens_saved_estimate: int
    rtk_used: bool = True
    rtk_tags: dict[str, str] = field(default_factory=dict)

    @property
    def bytes_saved(self) -> int:
        return max(0, self.bytes_before - self.bytes_after)


class RTKClient:
    """Subprocess wrapper for the RTK Rust binary (architecture §3.3).

    On construction, resolves the vendored binary for the current platform.
    If the binary is not available, falls back to RTKStub automatically.
    """

    def __init__(
        self,
        *,
        binary_override: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self._timeout_s = timeout_s
        self._binary: Path | None = None
        self._stub: object | None = None
        self._disabled_for_session: bool = False

        try:
            self._binary = resolve_binary_path(binary_override)
        except RTKBinaryMissingError:
            from .stub import RTKStub
            self._stub = RTKStub()

    @property
    def is_available(self) -> bool:
        return self._binary is not None and not self._disabled_for_session

    async def run_command(
        self, argv: list[str], *, timeout_s: float | None = None
    ) -> RTKResult:
        """Run *argv* through RTK and return filtered output + savings metrics.

        Falls back to stub if binary is unavailable or if the command is not
        in RTK's registry (pass-through with zero savings).
        """
        if self._stub is not None:
            return await self._stub.run_command(argv, timeout_s=timeout_s or self._timeout_s)  # type: ignore[union-attr]

        if self._disabled_for_session:
            return await self._passthrough(argv, timeout_s=timeout_s or self._timeout_s)

        if not is_known_command(argv):
            # Unknown command — pass through without RTK (not an error)
            return await self._passthrough(argv, timeout_s=timeout_s or self._timeout_s)

        return await self._run_rtk(argv, timeout_s=timeout_s or self._timeout_s)

    async def _run_rtk(self, argv: list[str], *, timeout_s: float) -> RTKResult:
        """Invoke the RTK binary on *argv*."""
        if self._binary is None:
            raise RTKExecutionError("_run_rtk called with no binary resolved")

        rtk_argv = [str(self._binary)] + argv
        try:
            proc = await asyncio.create_subprocess_exec(
                *rtk_argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_s
                )
            except asyncio.TimeoutError:
                proc.kill()
                logger.error("rtk: subprocess timeout after %ss — disabling for session", timeout_s)
                self._disabled_for_session = True
                raise RTKExecutionError(f"RTK subprocess timed out after {timeout_s}s")

        except (OSError, RTKExecutionError) as exc:
            logger.error("rtk: subprocess error — disabling for session: %s", exc)
            self._disabled_for_session = True
            # Fall back to passthrough
            return await self._passthrough(argv, timeout_s=timeout_s)

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Read savings from RTK telemetry
        savings = await self._read_savings(timeout_s=timeout_s)

        bytes_before = savings.bytes_before if savings.bytes_before else len(stdout_bytes)
        bytes_after = savings.bytes_after if savings.bytes_after else len(stdout_bytes)

        tags: dict[str, str] = {}
        if savings.bytes_saved > 0:
            tags["compression.rtk.bytes_saved_prior"] = str(savings.bytes_saved)

        return RTKResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode or 0,
            bytes_before=bytes_before,
            bytes_after=bytes_after,
            tokens_saved_estimate=savings.tokens_saved_estimate,
            rtk_used=True,
            rtk_tags=tags,
        )

    async def _read_savings(self, *, timeout_s: float) -> RTKSavings:
        """Read the latest savings from RTK's telemetry."""
        if self._binary is None:
            raise RTKExecutionError("_read_savings called with no binary resolved")
        from .telemetry import _ZERO_SAVINGS

        try:
            proc = await asyncio.create_subprocess_exec(
                str(self._binary), "gain", "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=min(5.0, timeout_s))
            return parse_gain_output(stdout_bytes.decode("utf-8", errors="replace"))
        except Exception:
            # Best-effort — telemetry failures are non-fatal (architecture §3.3.6)
            return _ZERO_SAVINGS

    async def _passthrough(self, argv: list[str], *, timeout_s: float) -> RTKResult:
        """Run *argv* directly without RTK."""
        import shutil
        cmd = argv[0] if argv else ""
        binary = shutil.which(cmd) or cmd
        try:
            proc = await asyncio.create_subprocess_exec(
                binary, *argv[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_s
            )
            return RTKResult(
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                bytes_before=len(stdout_bytes),
                bytes_after=len(stdout_bytes),
                tokens_saved_estimate=0,
                rtk_used=False,
            )
        except Exception as exc:
            return RTKResult(
                stdout="",
                stderr=str(exc),
                exit_code=1,
                bytes_before=0,
                bytes_after=0,
                tokens_saved_estimate=0,
                rtk_used=False,
            )
