"""RTK wrapper error hierarchy."""
from __future__ import annotations


class RTKError(Exception):
    """Base for all RTK errors."""


class RTKBinaryMissingError(RTKError):
    """Vendored binary not found for this platform."""


class RTKExecutionError(RTKError):
    """Subprocess invocation failed or timed out."""


class RTKTelemetryError(RTKError):
    """Could not parse RTK telemetry JSON output."""
