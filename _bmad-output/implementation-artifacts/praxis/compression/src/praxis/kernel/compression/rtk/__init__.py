"""RTK — CLI output compression via vendored Rust binary (architecture §3.3).

Public API:
    RTKClient() — auto-resolves vendored binary, falls back to stub
    RTKResult  — output of run_command()

Exceptions:
    RTKError, RTKBinaryMissingError, RTKExecutionError, RTKTelemetryError
"""
from .client import RTKClient, RTKResult
from .errors import RTKBinaryMissingError, RTKError, RTKExecutionError, RTKTelemetryError

__all__ = [
    "RTKClient",
    "RTKResult",
    "RTKError",
    "RTKBinaryMissingError",
    "RTKExecutionError",
    "RTKTelemetryError",
]
