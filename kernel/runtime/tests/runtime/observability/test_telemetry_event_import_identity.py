"""Q3 option (b) — TelemetryEvent is-identity and import-source guards.

Architecture §9.1 / §10.4 / §16.2: Stage 4 does NOT define its own
TelemetryEvent.  It imports the one from praxis.kernel.memory.telemetry
and re-exports it.  The is-identity check (using Python's `is` operator)
is the strongest possible proof of single-source-of-truth.

Test-strategy §6.5.B (import identity guard) + §10.4 (R53 harness).
"""

from __future__ import annotations

import pytest


@pytest.mark.critical
@pytest.mark.r53_structural
def test_runtime_telemetry_event_is_memory_telemetry_event() -> None:
    """praxis.kernel.runtime.observability.TelemetryEvent IS
    praxis.kernel.memory.telemetry.TelemetryEvent (same object in memory).

    `is` is stricter than isinstance — it verifies no aliasing occurred
    and that there is exactly one TelemetryEvent type shared across stages.
    """
    from praxis.kernel.memory.telemetry import TelemetryEvent as MemoryTE
    from praxis.kernel.runtime.observability import TelemetryEvent as RuntimeTE

    assert RuntimeTE is MemoryTE, (
        "Q3 option (b) violated: praxis.kernel.runtime.observability.TelemetryEvent "
        "is NOT the same object as praxis.kernel.memory.telemetry.TelemetryEvent. "
        "Stage 4 must import-and-re-export, never redefine."
    )


@pytest.mark.critical
@pytest.mark.r53_structural
def test_runtime_observability_reexports_memory_telemetry_event() -> None:
    """TelemetryEvent accessible from the observability package __init__."""
    import praxis.kernel.runtime.observability as obs_pkg

    assert hasattr(obs_pkg, "TelemetryEvent"), (
        "TelemetryEvent not found in praxis.kernel.runtime.observability.__init__"
    )
    assert callable(obs_pkg.TelemetryEvent)
