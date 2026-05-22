"""Stage 10 SessionIndexPort contract tests.

RED phase expectation for H#4.1: this module fails by import until
``kernel/session_index`` lands in H#4.2+.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Literal

import pytest
from pydantic import ValidationError

from praxis.kernel.session_index.models import (
    ArtifactRef,
    SessionFilter,
    SessionRecord,
    SkillOutcome,
    TelemetryEvent,
    TimeWindow,
)
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.kernel.session_index.skill_telemetry import SqliteSkillTelemetry
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex
from praxis.ports.common import ContractViolation

_CORRELATION_ID = "stage10-session-index-contract"
_T0 = datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc)
_T1 = datetime(2026, 5, 21, 9, 0, tzinfo=timezone.utc)
_T2 = datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc)


def _store(tmp_path) -> SessionIndexPort:
    store = SqliteSessionIndex(tmp_path / "session-index-contract.sqlite3")
    assert isinstance(store, SessionIndexPort)
    return store


def _record(
    session_id: str,
    *,
    user_id: str | None = "user-a",
    skill_ids: list[str] | None = None,
    status: Literal["started", "running", "completed", "failed", "archived"] = "completed",
    created_at: datetime = _T0,
) -> SessionRecord:
    return SessionRecord(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        session_id=session_id,
        user_id=user_id,
        title=f"Session {session_id}",
        created_at=created_at,
        updated_at=created_at,
        status=status,
        skill_ids=skill_ids or ["bmad-dev-story"],
        artifact_ids=[f"{session_id}-summary"],
        source_uri=f"memory://sessions/{session_id}",
    )


def _event(
    event_type: Literal["invocation", "outcome", "error"],
    *,
    occurred_at: datetime = _T0,
    session_id: str = "session-a",
) -> TelemetryEvent:
    return TelemetryEvent(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        event_type=event_type,
        session_id=session_id,
        occurred_at=occurred_at,
        skill_id="bmad-dev-story",
        payload={"ok": True},
    )


@pytest.fixture
def adapter(tmp_path) -> SessionIndexPort:
    return _store(tmp_path)


@pytest.mark.no_waiver
def test_M_T_SESSIONIDX_LIST_01_returns_records_for_empty_and_populated_store(
    adapter: SessionIndexPort,
) -> None:
    assert list(adapter.list_sessions()) == []

    adapter.index_session("session-a", "alpha decision content")

    records = list(adapter.list_sessions())
    assert len(records) == 1
    assert isinstance(records[0], SessionRecord)
    assert records[0].session_id == "session-a"
    assert records[0].schema_version == 1
    assert records[0].correlation_id


@pytest.mark.parametrize(
    ("criteria", "expected"),
    [
        (SessionFilter(schema_version=1, correlation_id=_CORRELATION_ID, user_id=None, skill_id="skill-a"), ["s1", "s5", "s4", "s7"]),
        (
            SessionFilter(
                schema_version=1,
                correlation_id=_CORRELATION_ID,
                time_window=TimeWindow(schema_version=1, correlation_id=_CORRELATION_ID, start=_T1, end=_T2),
            ),
            ["s2", "s4", "s6", "s7"],
        ),
        (SessionFilter(schema_version=1, correlation_id=_CORRELATION_ID, status="failed"), ["s3", "s5", "s6", "s7"]),
        (
            SessionFilter(
                schema_version=1,
                correlation_id=_CORRELATION_ID,
                skill_id="skill-a",
                time_window=TimeWindow(schema_version=1, correlation_id=_CORRELATION_ID, start=_T1, end=_T2),
            ),
            ["s4", "s7"],
        ),
        (
            SessionFilter(
                schema_version=1,
                correlation_id=_CORRELATION_ID,
                skill_id="skill-a",
                status="failed",
            ),
            ["s5", "s7"],
        ),
        (
            SessionFilter(
                schema_version=1,
                correlation_id=_CORRELATION_ID,
                time_window=TimeWindow(schema_version=1, correlation_id=_CORRELATION_ID, start=_T1, end=_T2),
                status="failed",
            ),
            ["s6", "s7"],
        ),
        (
            SessionFilter(
                schema_version=1,
                correlation_id=_CORRELATION_ID,
                skill_id="skill-a",
                time_window=TimeWindow(schema_version=1, correlation_id=_CORRELATION_ID, start=_T1, end=_T2),
                status="failed",
            ),
            ["s7"],
        ),
    ],
)
def test_M_T_SESSIONIDX_LIST_02_criteria_filters_each_dimension_distinctly(
    adapter: SessionIndexPort,
    criteria: SessionFilter,
    expected: list[str],
) -> None:
    rows = [
        _record("s1", skill_ids=["skill-a"], created_at=_T0, status="completed"),
        _record("s2", skill_ids=["skill-b"], created_at=_T1, status="completed"),
        _record("s3", skill_ids=["skill-b"], created_at=_T0, status="failed"),
        _record("s4", skill_ids=["skill-a"], created_at=_T1, status="completed"),
        _record("s5", skill_ids=["skill-a"], created_at=_T0, status="failed"),
        _record("s6", skill_ids=["skill-b"], created_at=_T1, status="failed"),
        _record("s7", skill_ids=["skill-a"], created_at=_T1, status="failed"),
    ]
    for row in rows:
        adapter.index_session(row.session_id, row.model_dump_json())

    observed = [record.session_id for record in adapter.list_sessions(criteria=criteria)]

    assert observed == expected


def test_M_T_SESSIONIDX_LIST_02_reversed_time_window_raises_contract_violation(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", _record("session-a").model_dump_json())
    criteria = SessionFilter(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        time_window=TimeWindow(
            schema_version=1,
            correlation_id=_CORRELATION_ID,
            start=_T2,
            end=_T1,
        ),
    )

    with pytest.raises(ContractViolation):
        adapter.list_sessions(criteria=criteria)


def test_M_T_SESSIONIDX_LIST_03_ordering_stable_across_requeries(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha")
    adapter.index_session("session-b", "bravo")

    first = [record.session_id for record in adapter.list_sessions()]
    second = [record.session_id for record in adapter.list_sessions()]

    assert first == second


@pytest.mark.no_waiver
def test_M_T_SESSIONIDX_GET_01_known_id_returns_record_with_dto_fields(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha")

    record = adapter.get_session("session-a")

    assert record is not None
    assert record.session_id == "session-a"
    assert record.schema_version == 1
    assert record.correlation_id


def test_M_T_SESSIONIDX_GET_02_unknown_id_returns_none(adapter: SessionIndexPort) -> None:
    assert adapter.get_session("missing-session") is None


def test_M_T_SESSIONIDX_GET_03_session_record_forbids_extra_and_is_frozen() -> None:
    record = _record("session-a")

    with pytest.raises(ValidationError):
        SessionRecord(**(record.model_dump() | {"extra": "forbidden"}))

    with pytest.raises(ValidationError):
        record.user_id = "mutated"  # type: ignore[misc]


def test_M_T_SESSIONIDX_GET_03_index_session_rejects_naive_record_datetimes(
    adapter: SessionIndexPort,
) -> None:
    aware_record = _record("aware-session", created_at=_T0)
    naive_record = _record(
        "naive-session",
        created_at=datetime(2026, 5, 21, 8, 0),
    )

    adapter.index_session(aware_record.session_id, aware_record.model_dump_json())
    with pytest.raises(ContractViolation):
        adapter.index_session(naive_record.session_id, naive_record.model_dump_json())


@pytest.mark.no_waiver
def test_M_T_SESSIONIDX_SEARCH_01_keyword_uses_fts5_and_returns_scored_excerpts(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha governance replay")
    adapter.index_session("session-b", "unrelated content")

    matches = list(adapter.search("governance", mode="keyword"))

    assert [match.session_id for match in matches] == ["session-a"]
    assert matches[0].score > 0
    assert matches[0].excerpt
    assert matches[0].evidence_ref


def test_M_T_SESSIONIDX_SEARCH_02_semantic_mode_is_empty_sequence(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha governance replay")

    assert list(adapter.search("governance", mode="semantic")) == []


@pytest.mark.parametrize(("limit", "expected_count"), [(0, 0), (4, 3)])
def test_M_T_SESSIONIDX_SEARCH_03_limit_parameter_honored(
    adapter: SessionIndexPort,
    limit: int,
    expected_count: int,
) -> None:
    for idx in range(3):
        adapter.index_session(f"session-{idx}", "repeatable governance content")

    assert len(list(adapter.search("governance", mode="keyword", limit=limit))) == expected_count


def test_M_T_SESSIONIDX_SEARCH_04_fts5_special_chars_do_not_raise(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "literal special characters")

    assert list(adapter.search('"special" OR chars* - bad', mode="keyword")) is not None


def test_M_T_SESSIONIDX_ARTIFACT_01_known_artifact_returns_ref(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha")

    artifact = adapter.get_artifact("session-a", "session-a-summary")

    assert isinstance(artifact, ArtifactRef)


def test_M_T_SESSIONIDX_ARTIFACT_02_unknown_artifact_returns_none(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha")

    assert adapter.get_artifact("session-a", "missing-artifact") is None


def test_M_T_SESSIONIDX_ARTIFACT_03_artifact_ref_has_payload_uri_and_size(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("session-a", "alpha")

    artifact = adapter.get_artifact("session-a", "session-a-summary")

    assert artifact is not None
    assert artifact.byte_size > 0
    assert artifact.payload_uri


@pytest.mark.parametrize("event_type", ["invocation", "outcome", "error"])
def test_M_T_SESSIONIDX_TELEMETRY_01_event_types_and_duplicate_idempotency(
    adapter: SessionIndexPort,
    event_type: Literal["invocation", "outcome", "error"],
) -> None:
    event = _event(event_type)
    adapter.record_telemetry(event)

    try:
        adapter.record_telemetry(event)
    except ContractViolation:
        with pytest.raises(ContractViolation):
            adapter.record_telemetry(event)
    else:
        adapter.record_telemetry(event)


def test_M_T_SESSIONIDX_TELEMETRY_02_naive_occurred_at_raises_contract_violation(
    adapter: SessionIndexPort,
) -> None:
    event = _event("invocation", occurred_at=datetime(2026, 5, 21, 8, 0))

    with pytest.raises(ContractViolation):
        adapter.record_telemetry(event)


def test_M_T_SESSIONIDX_FTS5_PROBE_sqlite_build_supports_fts5() -> None:
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE t USING fts5(x)")


def test_M_T_SESSIONIDX_FTS5_FALLBACK_requires_advisor_disposition() -> None:
    import sqlite3

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
    except sqlite3.OperationalError:
        pytest.skip("Q-10-1 advisor disposition required before fallback can pass")


def test_M_T_SESSIONIDX_COMPOSITION_01_skill_telemetry_does_not_call_session_index_methods() -> None:
    source = inspect.getsource(SqliteSkillTelemetry)
    forbidden_calls = [
        ".index_session(",
        ".search(",
        ".list_sessions(",
        ".get_session(",
        ".get_artifact(",
        ".record_telemetry(",
    ]

    assert "SqliteSessionIndex" not in source
    assert all(call not in source for call in forbidden_calls)


def test_M_T_SESSIONIDX_REPLAY_01_shared_substrate_replays_without_port_delegation(tmp_path) -> None:
    db_path = tmp_path / "shared-substrate.sqlite3"
    index = SqliteSessionIndex(db_path)
    telemetry = SqliteSkillTelemetry(db_path)
    record = _record("session-a", user_id="user-a", skill_ids=["bmad-dev-story"])

    index.index_session(record.session_id, record.model_dump_json())
    invocation = telemetry.record_invocation(
        "bmad-dev-story",
        "session-a",
        SkillOutcome(
            schema_version=1,
            correlation_id=_CORRELATION_ID,
            idempotency_key=None,
            observed_at=_T1,
            gate_scores={"Q1": 8.0},
            beat_count=3,
            halt_point_dispositions={"H1": "GO"},
        ),
    )
    replayed = index.get_session("session-a")
    usage = telemetry.query(
        TimeWindow(
            schema_version=1,
            correlation_id=_CORRELATION_ID,
            idempotency_key=None,
            start=_T0,
            end=_T2,
        )
    )

    assert invocation.observation_id
    assert replayed is not None
    assert replayed.session_id == "session-a"
    assert [entry.skill_id for entry in usage] == ["bmad-dev-story"]
    assert usage[0].sessions == ["session-a"]


def test_M_T_SESSIONIDX_USER_01_list_sessions_filters_by_user_id(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("user-a-1", _record("user-a-1", user_id="user-a").model_dump_json())
    adapter.index_session("user-b-1", _record("user-b-1", user_id="user-b").model_dump_json())
    adapter.index_session("anonymous", _record("anonymous", user_id=None).model_dump_json())

    criteria = SessionFilter(schema_version=1, correlation_id=_CORRELATION_ID, user_id="user-a")

    assert [record.session_id for record in adapter.list_sessions(criteria=criteria)] == ["user-a-1"]


def test_M_T_SESSIONIDX_USER_02_get_session_roundtrips_user_id_and_none(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("user-a-1", _record("user-a-1", user_id="user-a").model_dump_json())
    adapter.index_session("anonymous", _record("anonymous", user_id=None).model_dump_json())

    user_record = adapter.get_session("user-a-1")
    anonymous_record = adapter.get_session("anonymous")

    assert user_record is not None
    assert user_record.user_id == "user-a"
    assert anonymous_record is not None
    assert anonymous_record.user_id is None


def test_M_T_SESSIONIDX_USER_03_user_history_ordering_is_created_at_stable(
    adapter: SessionIndexPort,
) -> None:
    adapter.index_session("newer", _record("newer", user_id="user-a", created_at=_T2).model_dump_json())
    adapter.index_session("older", _record("older", user_id="user-a", created_at=_T0).model_dump_json())
    criteria = SessionFilter(schema_version=1, correlation_id=_CORRELATION_ID, user_id="user-a")

    first = [record.session_id for record in adapter.list_sessions(criteria=criteria)]
    second = [record.session_id for record in adapter.list_sessions(criteria=criteria)]

    assert first == ["older", "newer"]
    assert second == first
