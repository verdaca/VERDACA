"""SQLite-backed SkillTelemetryPort implementation."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Literal, Sequence

from praxis.kernel.session_index.models import (
    SkillInvocationRecord,
    SkillOutcome,
    SkillUsage,
    TimeWindow,
)
from praxis.kernel.session_index.port import SkillTelemetryPort
from praxis.ports.common import ContractViolation

_PORT_NAME = "skill_telemetry"
_DEFAULT_CORRELATION_ID = "skill-telemetry-sqlite"
_DEFAULT_DB_DIR = Path(tempfile.gettempdir()) / "verdaca-session-index"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "session-index-dev.sqlite3"


def default_dev_db_path() -> Path:
    """Return the shared Stage 10 dev DB path; never the main knowledge DB."""

    return _DEFAULT_DB_PATH


class SqliteSkillTelemetry(SkillTelemetryPort):
    """SQLite implementation of SkillTelemetryPort.

    The implementation shares only the SQLite substrate. It does not import or
    call SessionIndexPort implementations.
    """

    API_VERSION = SkillTelemetryPort.API_VERSION

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_dev_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def record_invocation(
        self,
        skill_id: str,
        session_id: str,
        outcome_signals: SkillOutcome,
    ) -> SkillInvocationRecord:
        self._require_aware(outcome_signals.observed_at)
        outcome_json = outcome_signals.model_dump_json()
        observation_id = self._observation_id(
            skill_id=skill_id,
            session_id=session_id,
            observed_at=outcome_signals.observed_at,
            outcome_json=outcome_json,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO skill_invocations (
                    observation_id, skill_id, session_id, observed_at, outcome_json,
                    schema_version, correlation_id, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    skill_id,
                    session_id,
                    self._encode_dt(outcome_signals.observed_at),
                    outcome_json,
                    outcome_signals.schema_version,
                    outcome_signals.correlation_id,
                    outcome_signals.idempotency_key,
                ),
            )
        return SkillInvocationRecord(
            schema_version=outcome_signals.schema_version,
            correlation_id=outcome_signals.correlation_id,
            idempotency_key=outcome_signals.idempotency_key,
            observation_id=observation_id,
            skill_id=skill_id,
            session_id=session_id,
            observed_at=outcome_signals.observed_at,
        )

    def query(self, window: TimeWindow) -> Sequence[SkillUsage]:
        self._require_aware(window.start)
        self._require_aware(window.end)
        self._require_ordered_window(window.start, window.end)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT skill_id,
                       COUNT(*) AS use_count,
                       MAX(observed_at) AS last_used_at,
                       json_group_array(session_id) AS sessions_json
                FROM skill_invocations
                WHERE observed_at >= ? AND observed_at <= ?
                GROUP BY skill_id
                ORDER BY skill_id ASC
                """,
                (self._encode_dt(window.start), self._encode_dt(window.end)),
            ).fetchall()
        return [
            SkillUsage(
                schema_version=window.schema_version,
                correlation_id=window.correlation_id,
                idempotency_key=None,
                skill_id=str(row["skill_id"]),
                use_count=int(row["use_count"]),
                last_used_at=datetime.fromisoformat(str(row["last_used_at"])),
                sessions=list(json.loads(str(row["sessions_json"]))),
                provenance="agent",
                state="active",
            )
            for row in rows
        ]

    def _initialize(self) -> None:
        schema = resources.files("praxis.kernel.session_index.schema").joinpath(
            "001_initial.sql"
        ).read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _require_aware(self, value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise self._violation("value")

    def _require_ordered_window(self, start: datetime, end: datetime) -> None:
        if start > end:
            raise self._violation("ordering")

    def _violation(self, violation_class: Literal["type", "value", "invariant", "ordering"]) -> ContractViolation:
        return ContractViolation(
            port_name=_PORT_NAME,
            correlation_id=_DEFAULT_CORRELATION_ID,
            occurred_at=datetime.now(timezone.utc),
            violation_class=violation_class,
        )

    @staticmethod
    def _encode_dt(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _observation_id(
        *,
        skill_id: str,
        session_id: str,
        observed_at: datetime,
        outcome_json: str,
    ) -> str:
        digest = hashlib.sha256(
            "|".join(
                [
                    skill_id,
                    session_id,
                    observed_at.astimezone(timezone.utc).isoformat(),
                    outcome_json,
                ]
            ).encode("utf-8")
        ).hexdigest()
        return f"skillobs-{digest[:24]}"


__all__ = [
    "SqliteSkillTelemetry",
    "default_dev_db_path",
]
