"""Session index kernel package.

Stage 10.2 exposes port Protocols and DTOs. Stage 10.3 adds SQLite-backed
implementations.
"""

from praxis.kernel.session_index.models import (
    ArtifactKind,
    ArtifactRef,
    SessionExcerpt,
    SessionFilter,
    SessionRecord,
    SessionStatus,
    SkillInvocationRecord,
    SkillOutcome,
    SkillProvenance,
    SkillState,
    SkillUsage,
    TelemetryEvent,
    TelemetryEventKind,
    TimeWindow,
)
from praxis.kernel.session_index.port import SessionIndexPort, SkillTelemetryPort
from praxis.kernel.session_index.skill_telemetry import SqliteSkillTelemetry
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex

__all__ = [
    "ArtifactKind",
    "ArtifactRef",
    "SessionExcerpt",
    "SessionFilter",
    "SessionIndexPort",
    "SessionRecord",
    "SessionStatus",
    "SkillInvocationRecord",
    "SkillOutcome",
    "SkillProvenance",
    "SkillState",
    "SkillTelemetryPort",
    "SkillUsage",
    "SqliteSessionIndex",
    "SqliteSkillTelemetry",
    "TelemetryEvent",
    "TelemetryEventKind",
    "TimeWindow",
]
