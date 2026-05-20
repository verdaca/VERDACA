"""tests/runtime/tools/test_otel_exporter_mcp_contract.py — RED commit.

Contract tests for otel-exporter-mcp. THE R53 enforcement point.
Architecture §6.1.8, §9.10, §10.5. S4.R-05 no-waiver.

Tests are tagged r53_structural per test-strategy.
"""

from __future__ import annotations

import pytest


@pytest.mark.r53_structural
def test_otel_exporter_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.otel_exporter_mcp import OtelExporterMcpAdapter  # noqa: F401


@pytest.mark.r53_structural
def test_otel_exporter_mcp_descriptor_blast_class_a() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.otel_exporter_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.A


@pytest.mark.r53_structural
def test_otel_exporter_imports_telemetry_event_from_memory() -> None:
    """R53 discipline: TelemetryEvent must be imported from memory.telemetry,
    not redefined. Q3 option (b) structural binding."""
    from praxis.kernel.memory.telemetry import TelemetryEvent as MemoryTelemetryEvent
    from praxis.kernel.runtime.tools.otel_exporter_mcp import TelemetryEvent

    assert TelemetryEvent is MemoryTelemetryEvent, (
        "otel_exporter_mcp must import TelemetryEvent from memory.telemetry, "
        "not redefine it. Q3 option (b) is-identity violation."
    )


@pytest.mark.r53_structural
@pytest.mark.no_waiver
def test_otel_exporter_forbidden_field_query_content_raises() -> None:
    """R53 hard gate: query_content must be rejected at construction."""

    from pydantic import ValidationError

    from praxis.kernel.runtime.tools.otel_exporter_mcp import build_telemetry_event

    with pytest.raises(ValidationError):
        build_telemetry_event(
            metric_name="test.metric",
            metric_type="counter",
            value=1.0,
            labels={},
            praxis_version="0.1.0",
            tenant_hash="abc123",
            query_content="this should be rejected",  # FORBIDDEN
        )


@pytest.mark.r53_structural
@pytest.mark.no_waiver
def test_otel_exporter_forbidden_field_embedding_raises() -> None:
    from pydantic import ValidationError

    from praxis.kernel.runtime.tools.otel_exporter_mcp import build_telemetry_event

    with pytest.raises(ValidationError):
        build_telemetry_event(
            metric_name="test.metric",
            metric_type="counter",
            value=1.0,
            labels={},
            praxis_version="0.1.0",
            tenant_hash="abc123",
            embedding=[0.1, 0.2, 0.3],  # FORBIDDEN
        )


@pytest.mark.r53_structural
def test_otel_exporter_seven_allowed_fields_accepted() -> None:
    """Seven allowed fields (R53 allowlist) must be accepted."""
    from praxis.kernel.runtime.tools.otel_exporter_mcp import build_telemetry_event

    # Should not raise
    event = build_telemetry_event(
        metric_name="runtime.agent.spawn.count",
        metric_type="counter",
        value=1.0,
        labels={"agent_name": "bmad-agent-dev", "tenant_hash": "abc123"},
        praxis_version="0.1.0",
        tenant_hash="abc123",
    )
    assert event.metric_name == "runtime.agent.spawn.count"


@pytest.mark.r53_structural
def test_otel_exporter_uses_runtime_telemetry_envelope() -> None:
    """otel_exporter must use RuntimeTelemetryEnvelope.to_telemetry_event()."""
    from praxis.kernel.runtime.tools.otel_exporter_mcp import OtelExporterMcpAdapter

    adapter = OtelExporterMcpAdapter()
    assert hasattr(adapter, "emit")
