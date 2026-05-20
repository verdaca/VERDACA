"""RuntimeTelemetryEnvelope — Stage 4 wrapper over Memory's TelemetryEvent.

Q3 option (b) structural decision (ratified 2026-04-13):
  - Stage 4 does NOT define its own TelemetryEvent.
  - Stage 4 imports TelemetryEvent from praxis.kernel.memory.telemetry.
  - RuntimeTelemetryEnvelope composes a TelemetryEvent via to_telemetry_event().
  - No inheritance.  No parallel RuntimeTelemetryEvent type.

Architecture §9.1 / §10.4 / §16.2 binding.
"""

from __future__ import annotations

from datetime import datetime, timezone

from praxis.kernel.memory.telemetry import TelemetryEvent

_PRAXIS_VERSION = "0.1.0"


class RuntimeTelemetryEnvelope:
    """Construction helper for runtime-namespace telemetry events.

    Enforces ``runtime.*`` metric_name prefix.  Delegates R53 field
    enforcement to the wrapped ``TelemetryEvent`` model — any forbidden
    field in ``to_telemetry_event()`` raises ``ValidationError`` from
    Pydantic before the event reaches any sink.

    Usage
    -----
    ::

        env = RuntimeTelemetryEnvelope.for_spawn(
            tenant_hash="abc",
            agent_name="bmad-agent-architect",
            role="producer",
            mode="subagent",
            duration_ms=123.4,
        )
        event = env.to_telemetry_event()
    """

    __slots__ = (
        "_metric_name",
        "_metric_type",
        "_value",
        "_labels",
        "_tenant_hash",
    )

    def __init__(
        self,
        *,
        metric_name: str,
        metric_type: str,
        value: float,
        labels: dict[str, str],
        tenant_hash: str,
    ) -> None:
        if not metric_name.startswith("runtime."):
            raise ValueError(
                f"RuntimeTelemetryEnvelope metric_name must start with 'runtime.', "
                f"got: {metric_name!r}"
            )
        self._metric_name = metric_name
        self._metric_type = metric_type
        self._value = float(value)
        self._labels = dict(labels)
        self._tenant_hash = tenant_hash

    def to_telemetry_event(self) -> TelemetryEvent:
        """Build and return a frozen TelemetryEvent from the Memory package.

        R53 enforcement is structural — TelemetryEvent(extra='forbid') will
        raise ValidationError on any forbidden-field attempt before this
        method can return.
        """
        return TelemetryEvent(
            metric_name=self._metric_name,
            metric_type=self._metric_type,  # type: ignore[arg-type]
            value=self._value,
            labels=self._labels,
            timestamp=datetime.now(tz=timezone.utc),
            praxis_version=_PRAXIS_VERSION,
            tenant_hash=self._tenant_hash,
        )

    # ------------------------------------------------------------------
    # Typed construction helpers for canonical Stage 4 metric families
    # ------------------------------------------------------------------

    @classmethod
    def for_spawn(
        cls,
        *,
        tenant_hash: str,
        agent_name: str,
        role: str,
        mode: str,
        duration_ms: float,
    ) -> "RuntimeTelemetryEnvelope":
        """Agent spawn histogram event."""
        return cls(
            metric_name="runtime.agent.spawn.duration_ms",
            metric_type="histogram",
            value=duration_ms,
            labels={
                "tenant_hash": tenant_hash,
                "agent_name": agent_name,
                "role": role,
                "mode": mode,
            },
            tenant_hash=tenant_hash,
        )

    @classmethod
    def for_tool_call(
        cls,
        *,
        tenant_hash: str,
        tool_name: str,
        blast_class: str,
        count: float = 1.0,
    ) -> "RuntimeTelemetryEnvelope":
        """Tool call counter event."""
        return cls(
            metric_name=f"runtime.tool_call.{blast_class}",
            metric_type="counter",
            value=count,
            labels={"tenant_hash": tenant_hash, "tool_name": tool_name},
            tenant_hash=tenant_hash,
        )

    @classmethod
    def for_asymmetry_hit(
        cls,
        *,
        tenant_hash: str,
        reviewer_agent_name: str,
        filtered_event_type: str,
        producer_sender_name: str,
    ) -> "RuntimeTelemetryEnvelope":
        """Bus asymmetry filter hit counter event."""
        return cls(
            metric_name="runtime.asymmetry.bus_filter.hit.count",
            metric_type="counter",
            value=1.0,
            labels={
                "tenant_hash": tenant_hash,
                "reviewer_agent_name": reviewer_agent_name,
                "filtered_event_type": filtered_event_type,
                "producer_sender_name": producer_sender_name,
            },
            tenant_hash=tenant_hash,
        )

    @classmethod
    def for_manifest_heartbeat(
        cls,
        *,
        tenant_hash: str,
        success_rate: float,
    ) -> "RuntimeTelemetryEnvelope":
        """Manifest heartbeat success-rate gauge event."""
        return cls(
            metric_name="runtime.manifest.heartbeat.success_rate",
            metric_type="gauge",
            value=success_rate,
            labels={"tenant_hash": tenant_hash},
            tenant_hash=tenant_hash,
        )


__all__ = ["RuntimeTelemetryEnvelope"]
