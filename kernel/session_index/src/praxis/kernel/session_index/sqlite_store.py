"""SQLite-backed SessionIndexPort implementation."""

from __future__ import annotations

import json
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Literal, Sequence

from pydantic import ValidationError

from praxis.kernel.session_index.models import (
    ArtifactKind,
    ArtifactRef,
    SessionExcerpt,
    SessionFilter,
    SessionRecord,
    SessionStatus,
    TelemetryEvent,
)
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.common import ContractViolation

_PORT_NAME = "session_index"
_DEFAULT_CORRELATION_ID = "session-index-sqlite"
_DEFAULT_DB_DIR = Path(tempfile.gettempdir()) / "verdaca-session-index"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "session-index-dev.sqlite3"


def default_dev_db_path() -> Path:
    """Return the package-owned dev DB path; never the main knowledge DB."""

    return _DEFAULT_DB_PATH


class SqliteSessionIndex(SessionIndexPort):
    """SQLite + FTS5 implementation of SessionIndexPort."""

    API_VERSION = SessionIndexPort.API_VERSION

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_dev_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def index_session(self, session_id: str, content: str) -> None:
        record = self._record_from_content(session_id, content)
        self._require_aware(record.created_at)
        self._require_aware(record.updated_at)
        artifact_ids_json = json.dumps(record.artifact_ids)
        skill_ids_json = json.dumps(record.skill_ids)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, user_id, title, content, created_at, updated_at, status,
                    skill_ids_json, artifact_ids_json, source_uri, schema_version,
                    correlation_id, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    title = excluded.title,
                    content = excluded.content,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    status = excluded.status,
                    skill_ids_json = excluded.skill_ids_json,
                    artifact_ids_json = excluded.artifact_ids_json,
                    source_uri = excluded.source_uri,
                    schema_version = excluded.schema_version,
                    correlation_id = excluded.correlation_id,
                    idempotency_key = excluded.idempotency_key
                """,
                (
                    record.session_id,
                    record.user_id,
                    record.title,
                    content,
                    self._encode_dt(record.created_at),
                    self._encode_dt(record.updated_at),
                    record.status,
                    skill_ids_json,
                    artifact_ids_json,
                    record.source_uri,
                    record.schema_version,
                    record.correlation_id,
                    record.idempotency_key,
                ),
            )
            conn.execute("DELETE FROM session_fts WHERE session_id = ?", (session_id,))
            conn.execute(
                """
                INSERT INTO session_fts(session_id, content, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.session_id,
                    content,
                    self._encode_dt(record.created_at),
                    self._encode_dt(record.updated_at),
                    record.status,
                ),
            )
            for artifact_id in record.artifact_ids:
                payload_uri = f"session://{record.session_id}/artifacts/{artifact_id}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO artifact_refs (
                        session_id, artifact_id, kind, payload_uri, byte_size,
                        schema_version, correlation_id, idempotency_key
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.session_id,
                        artifact_id,
                        self._artifact_kind(artifact_id),
                        payload_uri,
                        max(1, len(content.encode("utf-8"))),
                        record.schema_version,
                        record.correlation_id,
                        record.idempotency_key,
                    ),
                )

    def search(
        self,
        query: str,
        mode: Literal["keyword", "semantic"],
        limit: int = 10,
    ) -> Sequence[SessionExcerpt]:
        if mode == "semantic" or limit <= 0:
            return []
        if mode != "keyword":
            raise self._violation("value")

        match_query = self._fts_query(query)
        if not match_query:
            return []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, snippet(session_fts, 1, '', '', '...', 12) AS excerpt,
                       bm25(session_fts) AS rank
                FROM session_fts
                WHERE session_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, limit),
            ).fetchall()

        return [
            SessionExcerpt(
                schema_version=1,
                correlation_id=_DEFAULT_CORRELATION_ID,
                idempotency_key=None,
                session_id=str(row["session_id"]),
                excerpt=str(row["excerpt"]),
                score=max(0.000001, abs(float(row["rank"]))),
                evidence_ref=f"{row['session_id']}:fts5",
            )
            for row in rows
        ]

    def list_sessions(
        self,
        criteria: SessionFilter | None = None,
    ) -> Sequence[SessionRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if criteria is not None:
            if criteria.user_id is not None:
                clauses.append("user_id = ?")
                params.append(criteria.user_id)
            if criteria.skill_id is not None:
                clauses.append("EXISTS (SELECT 1 FROM json_each(skill_ids_json) WHERE value = ?)")
                params.append(criteria.skill_id)
            if criteria.status is not None:
                clauses.append("status = ?")
                params.append(criteria.status)
            if criteria.time_window is not None:
                self._require_aware(criteria.time_window.start)
                self._require_aware(criteria.time_window.end)
                self._require_ordered_window(
                    criteria.time_window.start,
                    criteria.time_window.end,
                )
                clauses.append("created_at >= ? AND created_at <= ?")
                params.extend(
                    [
                        self._encode_dt(criteria.time_window.start),
                        self._encode_dt(criteria.time_window.end),
                    ]
                )
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM sessions {where} ORDER BY created_at ASC, session_id ASC",
                params,
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_session(self, session_id: str) -> SessionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return None if row is None else self._row_to_record(row)

    def get_artifact(
        self,
        session_id: str,
        artifact_id: str,
    ) -> ArtifactRef | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM artifact_refs
                WHERE session_id = ? AND artifact_id = ?
                """,
                (session_id, artifact_id),
            ).fetchone()
        if row is None:
            return None
        return ArtifactRef(
            schema_version=int(row["schema_version"]),
            correlation_id=str(row["correlation_id"]),
            idempotency_key=row["idempotency_key"],
            id=str(row["artifact_id"]),
            kind=row["kind"],
            payload_uri=str(row["payload_uri"]),
            byte_size=int(row["byte_size"]),
        )

    def record_telemetry(self, event: TelemetryEvent) -> None:
        self._require_aware(event.occurred_at)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO telemetry_events (
                    session_id, occurred_at, event_type, skill_id, payload_json,
                    schema_version, correlation_id, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.session_id,
                    self._encode_dt(event.occurred_at),
                    event.event_type,
                    event.skill_id,
                    json.dumps(event.payload, sort_keys=True),
                    event.schema_version,
                    event.correlation_id,
                    event.idempotency_key,
                ),
            )

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

    def _record_from_content(self, session_id: str, content: str) -> SessionRecord:
        try:
            return SessionRecord.model_validate_json(content)
        except ValidationError:
            now = datetime.now(timezone.utc)
            return SessionRecord(
                schema_version=1,
                correlation_id=_DEFAULT_CORRELATION_ID,
                idempotency_key=None,
                session_id=session_id,
                user_id=None,
                title=None,
                created_at=now,
                updated_at=now,
                status="completed",
                skill_ids=[],
                artifact_ids=[f"{session_id}-summary"],
                source_uri=None,
            )

    def _row_to_record(self, row: sqlite3.Row) -> SessionRecord:
        return SessionRecord(
            schema_version=int(row["schema_version"]),
            correlation_id=str(row["correlation_id"]),
            idempotency_key=row["idempotency_key"],
            session_id=str(row["session_id"]),
            user_id=row["user_id"],
            title=row["title"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            status=row["status"],
            skill_ids=list(json.loads(str(row["skill_ids_json"]))),
            artifact_ids=list(json.loads(str(row["artifact_ids_json"]))),
            source_uri=row["source_uri"],
        )

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
    def _artifact_kind(artifact_id: str) -> ArtifactKind:
        if artifact_id.endswith("-summary"):
            return "summary"
        if artifact_id.endswith("-transcript"):
            return "transcript"
        return "other"

    @staticmethod
    def _fts_query(query: str) -> str:
        terms = re.findall(r"[\w]+", query, flags=re.UNICODE)
        return " OR ".join(f'"{term}"' for term in terms)


__all__ = [
    "SqliteSessionIndex",
    "default_dev_db_path",
]
