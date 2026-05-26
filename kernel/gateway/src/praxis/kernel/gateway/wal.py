"""Gateway-owned WAL and async SessionIndex helpers."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, Sequence

from praxis.kernel.session_index.models import ArtifactRef as SessionIndexArtifactRef
from praxis.kernel.session_index.models import SessionExcerpt, SessionFilter, SessionRecord
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef, SessionHandle

_RESULT_VERSION = 1


WAL_PRAGMAS: tuple[str, ...] = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GatewayWalConfig:
    """SQLite WAL configuration for gateway-owned idempotency state."""

    database_path: Path


class GatewayWalStore:
    """SQLite WAL store for gateway-owned idempotency authority."""

    def __init__(self, config: GatewayWalConfig) -> None:
        self._config = config
        self._config.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def database_path(self) -> Path:
        return self._config.database_path

    def begin_attempt(self, idempotency_key: str) -> None:
        """Record that the gateway accepted an idempotent attempt."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO gateway_idempotency (
                    idempotency_key, status, result_json
                )
                VALUES (?, 'in_progress', NULL)
                """,
                (idempotency_key,),
            )

    def get_result(self, idempotency_key: str) -> AnalysisResult | None:
        """Return a completed cached result, if one exists."""
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                """
                SELECT result_json
                FROM gateway_idempotency
                WHERE idempotency_key = ? AND status = 'completed'
                """,
                (idempotency_key,),
            ).fetchone()
        if row is None or row["result_json"] is None:
            return None
        return _analysis_result_from_json(str(row["result_json"]))

    def complete_attempt(self, idempotency_key: str, result: AnalysisResult) -> None:
        """Persist the canonical result for future idempotent replays."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO gateway_idempotency (
                    idempotency_key, status, result_json
                )
                VALUES (?, 'completed', ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    status = 'completed',
                    result_json = excluded.result_json
                """,
                (idempotency_key, _analysis_result_to_json(result)),
            )

    def _initialize(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gateway_idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed')),
                    result_json TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._config.database_path)
        conn.row_factory = sqlite3.Row
        for pragma in WAL_PRAGMAS:
            conn.execute(pragma)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn


class AsyncSessionIndex:
    """Async facade over the sync Stage 10 SessionIndexPort."""

    def __init__(self, session_index: SessionIndexPort) -> None:
        self._session_index = session_index

    async def index_session(self, session_id: str, content: str) -> None:
        await asyncio.to_thread(self._session_index.index_session, session_id, content)

    async def search(
        self,
        query: str,
        mode: Literal["keyword", "semantic"],
        limit: int = 10,
    ) -> Sequence[SessionExcerpt]:
        return await asyncio.to_thread(self._session_index.search, query, mode, limit)

    async def list_sessions(
        self,
        criteria: SessionFilter | None = None,
    ) -> Sequence[SessionRecord]:
        return await asyncio.to_thread(self._session_index.list_sessions, criteria)

    async def get_session(self, session_id: str) -> SessionRecord | None:
        return await asyncio.to_thread(self._session_index.get_session, session_id)

    async def get_artifact(
        self,
        session_id: str,
        artifact_id: str,
    ) -> SessionIndexArtifactRef | None:
        return await asyncio.to_thread(self._session_index.get_artifact, session_id, artifact_id)


def _analysis_result_to_json(result: AnalysisResult) -> str:
    payload = {
        "version": _RESULT_VERSION,
        "session": {
            "session_id": result.session.session_id,
            "status": result.session.status,
            "source_uri": result.session.source_uri,
        },
        "recommendation": result.recommendation,
        "cited_tradeoffs": list(result.cited_tradeoffs),
        "dissent_frames": list(result.dissent_frames),
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "session_id": artifact.session_id,
                "kind": artifact.kind,
                "uri": artifact.uri,
                "title": artifact.title,
            }
            for artifact in result.artifacts
        ],
        "cost_usd": None if result.cost_usd is None else str(result.cost_usd),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _analysis_result_from_json(value: str) -> AnalysisResult:
    payload = json.loads(value)
    if payload["version"] != _RESULT_VERSION:
        raise ValueError("Unsupported gateway WAL result version")

    session_payload = payload["session"]
    return AnalysisResult(
        session=SessionHandle(
            session_id=session_payload["session_id"],
            status=session_payload["status"],
            source_uri=session_payload["source_uri"],
        ),
        recommendation=payload["recommendation"],
        cited_tradeoffs=tuple(payload["cited_tradeoffs"]),
        dissent_frames=tuple(payload["dissent_frames"]),
        artifacts=tuple(
            ArtifactRef(
                artifact_id=artifact["artifact_id"],
                session_id=artifact["session_id"],
                kind=artifact["kind"],
                uri=artifact["uri"],
                title=artifact["title"],
            )
            for artifact in payload["artifacts"]
        ),
        cost_usd=None if payload["cost_usd"] is None else Decimal(payload["cost_usd"]),
    )


__all__ = [
    "AsyncSessionIndex",
    "GatewayWalConfig",
    "GatewayWalStore",
    "WAL_PRAGMAS",
]
