"""Stage 10 additive SessionIndex source URI filter contract tests."""

from __future__ import annotations

import types
from datetime import datetime, timezone

from praxis.kernel.session_index.models import SessionFilter, SessionRecord
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex

_CORRELATION_ID = "stage11-session-index-workspace-filter"
_NOW = datetime(2026, 5, 26, 8, 0, tzinfo=timezone.utc)


def test_M_T_SESSIONIDX_WORKSPACE_FILTER_01_applies_sql_source_uri_prefix(tmp_path) -> None:
    store = SqliteSessionIndex(tmp_path / "session-index-workspace-filter.sqlite3")
    for index in range(1000):
        record = _record(f"workspace-b-{index}", workspace_id="workspace-b")
        store.index_session(record.session_id, record.model_dump_json())
    expected_records = [
        _record("workspace-a-1", workspace_id="workspace-a"),
        _record("workspace-a-2", workspace_id="workspace-a"),
    ]
    for record in expected_records:
        store.index_session(record.session_id, record.model_dump_json())

    materialized_session_ids: list[str] = []
    original_row_to_record = store._row_to_record

    def recording_row_to_record(self, row) -> SessionRecord:
        materialized_session_ids.append(str(row["session_id"]))
        return original_row_to_record(row)

    store._row_to_record = types.MethodType(recording_row_to_record, store)  # type: ignore[method-assign]
    criteria = SessionFilter(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        source_uri_prefix="gateway://workspaces/workspace-a/",
    )

    observed = list(store.list_sessions(criteria=criteria))

    assert [record.session_id for record in observed] == ["workspace-a-1", "workspace-a-2"]
    assert materialized_session_ids == ["workspace-a-1", "workspace-a-2"]


def _record(session_id: str, *, workspace_id: str) -> SessionRecord:
    return SessionRecord(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        session_id=session_id,
        user_id="user-a",
        title=f"Session {session_id}",
        created_at=_NOW,
        updated_at=_NOW,
        status="completed",
        skill_ids=["stage11-gateway"],
        artifact_ids=[f"{session_id}-summary"],
        source_uri=f"gateway://workspaces/{workspace_id}/channels/cli/sessions/{session_id}",
    )
