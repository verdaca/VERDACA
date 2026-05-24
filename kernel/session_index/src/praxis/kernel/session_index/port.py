"""Stage 10 SessionIndexPort and SkillTelemetryPort Protocols."""

from __future__ import annotations

from typing import ClassVar, Literal, Protocol, Sequence, runtime_checkable

from praxis.kernel.session_index.models import (
    ArtifactRef,
    SessionExcerpt,
    SessionFilter,
    SessionRecord,
    SkillInvocationRecord,
    SkillOutcome,
    SkillUsage,
    TelemetryEvent,
    TimeWindow,
)


@runtime_checkable
class SessionIndexPort(Protocol):
    """Persistence boundary for session discovery and replay metadata."""

    API_VERSION: ClassVar[str] = "1.0.0"

    def index_session(self, session_id: str, content: str) -> None: ...

    def search(
        self,
        query: str,
        mode: Literal["keyword", "semantic"],
        limit: int = 10,
    ) -> Sequence[SessionExcerpt]: ...

    def list_sessions(
        self,
        criteria: SessionFilter | None = None,
    ) -> Sequence[SessionRecord]: ...

    def get_session(self, session_id: str) -> SessionRecord | None: ...

    def get_artifact(
        self,
        session_id: str,
        artifact_id: str,
    ) -> ArtifactRef | None: ...

    def record_telemetry(self, event: TelemetryEvent) -> None: ...


@runtime_checkable
class SkillTelemetryPort(Protocol):
    """Observation-only facade for skill invocation telemetry."""

    API_VERSION: ClassVar[str] = "1.0.0"

    def record_invocation(
        self,
        skill_id: str,
        session_id: str,
        outcome_signals: SkillOutcome,
    ) -> SkillInvocationRecord: ...

    def query(self, window: TimeWindow) -> Sequence[SkillUsage]: ...


__all__ = [
    "SessionIndexPort",
    "SkillTelemetryPort",
]
