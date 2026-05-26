"""Stage 10 SessionIndexPort and SkillTelemetryPort DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from praxis.ports.common import VerdacaDTOMixin

SessionStatus = Literal["started", "running", "completed", "failed", "archived"]
ArtifactKind = Literal["summary", "transcript", "cost", "trace", "export", "other"]
TelemetryEventKind = Literal["invocation", "outcome", "error"]
SkillProvenance = Literal["user", "agent"]
SkillState = Literal["active", "stale", "archived"]


class TimeWindow(VerdacaDTOMixin):
    """Closed query window for telemetry and session filtering."""

    start: datetime
    end: datetime


class SessionExcerpt(VerdacaDTOMixin):
    """A bounded piece of prior-session evidence returned by search()."""

    session_id: str
    excerpt: str
    score: float
    evidence_ref: str


class SessionRecord(VerdacaDTOMixin):
    """Session metadata sufficient for list/get/replay navigation."""

    session_id: str
    user_id: str | None
    title: str | None
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    skill_ids: list[str]
    artifact_ids: list[str]
    source_uri: str | None


class SessionFilter(VerdacaDTOMixin):
    """Optional list_sessions filter."""

    user_id: str | None = None
    skill_id: str | None = None
    time_window: TimeWindow | None = None
    status: SessionStatus | None = None
    source_uri_prefix: str | None = None


class ArtifactRef(VerdacaDTOMixin):
    """Reference to a stored session artifact without inlining payload bytes."""

    id: str
    kind: ArtifactKind
    payload_uri: str
    byte_size: int


class TelemetryEvent(VerdacaDTOMixin):
    """Discriminated telemetry event for session-index writes."""

    event_type: TelemetryEventKind
    session_id: str
    occurred_at: datetime
    skill_id: str | None = None
    payload: dict[str, str | int | float | bool | None]


class SkillOutcome(VerdacaDTOMixin):
    """Structured outcome signal captured when a skill is used."""

    observed_at: datetime
    gate_scores: dict[str, float]
    beat_count: int
    halt_point_dispositions: dict[str, str]


class SkillUsage(VerdacaDTOMixin):
    """Usage aggregate exposed through SkillTelemetryPort.query()."""

    skill_id: str
    use_count: int
    last_used_at: datetime | None
    sessions: list[str]
    provenance: SkillProvenance
    state: SkillState


class SkillInvocationRecord(VerdacaDTOMixin):
    """Recorded observation returned after an invocation is captured."""

    observation_id: str
    skill_id: str
    session_id: str
    observed_at: datetime
