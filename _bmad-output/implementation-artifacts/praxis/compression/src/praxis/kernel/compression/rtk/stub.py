"""RTK stub — used when the RTK binary is unavailable.

The stub passes commands through unchanged and reports zero savings.
This ensures agent workflows never crash due to a missing binary.
"""
from __future__ import annotations

import asyncio
import logging
import shutil

logger = logging.getLogger(__name__)


class RTKStub:
    """Pass-through stub for RTK when binary is not available."""

    def __init__(self) -> None:
        logger.warning(
            "RTK binary not available on this platform — "
            "command output will not be compressed (stub mode)."
        )

    async def run_command(
        self, argv: list[str], *, timeout_s: float = 30.0
    ) -> "RTKResult":  # noqa: F821
        """Run *argv* directly (without RTK compression) and return an RTKResult."""
        from .client import RTKResult  # avoid circular import

        cmd = argv[0] if argv else ""
        binary = shutil.which(cmd)
        if not binary:
            return RTKResult(
                stdout="",
                stderr=f"command not found: {cmd}",
                exit_code=127,
                bytes_before=0,
                bytes_after=0,
                tokens_saved_estimate=0,
                rtk_used=False,
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_s
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            return RTKResult(
                stdout=stdout,
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                bytes_before=len(stdout_bytes),
                bytes_after=len(stdout_bytes),
                tokens_saved_estimate=0,
                rtk_used=False,
            )
        except asyncio.TimeoutError:
            return RTKResult(
                stdout="",
                stderr="timeout",
                exit_code=1,
                bytes_before=0,
                bytes_after=0,
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
