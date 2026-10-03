"""Stage 10 SkillTelemetryPort contract tests.

RED phase expectation for H#4.1: this module fails by import until
``kernel/session_index`` lands in H#4.2+.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.session_index.models import SkillOutcome, SkillUsage, TimeWindow
from praxis.kernel.session_index.port import SkillTelemetryPort
from praxis.kernel.session_index.skill_telemetry import SqliteSkillTelemetry
from praxis.ports.common import ContractViolation

_CORRELATION_ID = "stage10-skill-telemetry-contract"
_T0 = datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc)
_T1 = datetime(2026, 5, 21, 9, 0, tzinfo=timezone.utc)
_T2 = datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc)


def _outcome(observed_at: datetime = _T0) -> SkillOutcome:
    return SkillOutcome(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        observed_at=observed_at,
        gate_scores={"Q1": 8.0},
        beat_count=3,
        halt_point_dispositions={"H1": "GO"},
    )


@pytest.fixture
def adapter(tmp_path) -> SkillTelemetryPort:
    telemetry = SqliteSkillTelemetry(tmp_path / "skill-telemetry-contract.sqlite3")
    assert isinstance(telemetry, SkillTelemetryPort)
    return telemetry


@pytest.mark.no_waiver
def test_M_T_SKILLTEL_EMIT_01_record_invocation_returns_stable_observation_id(
    adapter: SkillTelemetryPort,
) -> None:
    first = adapter.record_invocation("bmad-dev-story", "session-a", _outcome(_T0))
    second = adapter.record_invocation("bmad-dev-story", "session-a", _outcome(_T0))

    assert first.observation_id
    assert second.observation_id == first.observation_id
    assert second.skill_id == "bmad-dev-story"
    assert second.session_id == "session-a"


def test_M_T_SKILLTEL_EMIT_02_naive_observed_at_raises_contract_violation(
    adapter: SkillTelemetryPort,
) -> None:
    with pytest.raises(ContractViolation):
        adapter.record_invocation(
            "bmad-dev-story",
            "session-a",
            _outcome(datetime(2026, 5, 21, 8, 0)),
        )


def test_M_T_SKILLTEL_QUERY_01_window_returns_consistent_usage_counts(
    adapter: SkillTelemetryPort,
) -> None:
    adapter.record_invocation("bmad-dev-story", "session-a", _outcome(_T0))
    adapter.record_invocation("bmad-dev-story", "session-b", _outcome(_T1))
    window = TimeWindow(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        start=_T0,
        end=_T2,
    )

    usage = list(adapter.query(window))

    assert len(usage) == 1
    assert isinstance(usage[0], SkillUsage)
    assert usage[0].skill_id == "bmad-dev-story"
    assert usage[0].use_count == 2
    assert usage[0].sessions == ["session-a", "session-b"]


def test_M_T_SKILLTEL_QUERY_02_empty_window_returns_empty_sequence(
    adapter: SkillTelemetryPort,
) -> None:
    adapter.record_invocation("bmad-dev-story", "session-a", _outcome(_T0))
    window = TimeWindow(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        start=_T1,
        end=_T2,
    )

    assert list(adapter.query(window)) == []


def test_M_T_SKILLTEL_QUERY_02_reversed_time_window_raises_contract_violation(
    adapter: SkillTelemetryPort,
) -> None:
    window = TimeWindow(
        schema_version=1,
        correlation_id=_CORRELATION_ID,
        idempotency_key=None,
        start=_T2,
        end=_T1,
    )

    with pytest.raises(ContractViolation):
        adapter.query(window)
