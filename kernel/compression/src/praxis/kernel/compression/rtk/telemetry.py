"""RTK telemetry parser — reads ``rtk gain --format json`` output."""
from __future__ import annotations

import json
from dataclasses import dataclass

from .errors import RTKTelemetryError


@dataclass(frozen=True)
class RTKSavings:
    bytes_before: int
    bytes_after: int
    tokens_saved_estimate: int
    command: str = ""

    @property
    def bytes_saved(self) -> int:
        return max(0, self.bytes_before - self.bytes_after)


_ZERO_SAVINGS = RTKSavings(bytes_before=0, bytes_after=0, tokens_saved_estimate=0)


def parse_gain_output(json_text: str) -> RTKSavings:
    """Parse the JSON output from ``rtk gain --format json``.

    RTK emits a JSON object (or array of objects) with fields:
    ``bytes_before``, ``bytes_after``, ``tokens_saved``, ``command``.

    Returns RTKSavings. On parse failure, raises RTKTelemetryError.
    """
    if not json_text.strip():
        return _ZERO_SAVINGS

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise RTKTelemetryError(f"rtk gain output is not valid JSON: {exc}") from exc

    # RTK may return a list (history) or a single object (latest)
    if isinstance(data, list):
        if not data:
            return _ZERO_SAVINGS
        data = data[-1]  # Use the most recent entry

    if not isinstance(data, dict):
        raise RTKTelemetryError(f"unexpected rtk gain format: {type(data).__name__}")

    try:
        return RTKSavings(
            bytes_before=int(data.get("bytes_before", 0)),
            bytes_after=int(data.get("bytes_after", 0)),
            tokens_saved_estimate=int(data.get("tokens_saved", 0)),
            command=str(data.get("command", "")),
        )
    except (TypeError, ValueError) as exc:
        raise RTKTelemetryError(f"rtk gain field parse error: {exc}") from exc
