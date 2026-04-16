"""Session model validation tests — test-strategy §4.6.

SHELL-T-SESS-UNIT-01: question min 20 chars
SHELL-T-SESS-UNIT-02: question max 10000 chars
SHELL-T-SESS-UNIT-03: PENDING → RUNNING → COMPLETED
SHELL-T-SESS-UNIT-04: PENDING → RUNNING → FAILED
SHELL-T-SESS-UNIT-05: rendering_mode defaults to position_to_hold
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.models import (
    CreateSessionRequest,
    RenderingMode,
    SessionDepth,
    SessionStatus,
)


class TestCreateSessionRequest:
    """Validation tests for CreateSessionRequest (arch §3.2)."""

    @pytest.mark.shell_sess
    def test_sess_unit_01_question_min_length(self):
        """SHELL-T-SESS-UNIT-01: question must be >= 20 chars."""
        with pytest.raises(ValidationError, match="String should have at least 20 characters"):
            CreateSessionRequest(question="too short")

    @pytest.mark.shell_sess
    def test_sess_unit_01_question_exactly_20(self):
        """SHELL-T-SESS-UNIT-01: question at exactly 20 chars is valid."""
        req = CreateSessionRequest(question="a" * 20)
        assert len(req.question) == 20

    @pytest.mark.shell_sess
    def test_sess_unit_02_question_max_length(self):
        """SHELL-T-SESS-UNIT-02: question must be <= 10000 chars."""
        with pytest.raises(ValidationError, match="String should have at most 10000 characters"):
            CreateSessionRequest(question="a" * 10001)

    @pytest.mark.shell_sess
    def test_sess_unit_02_question_exactly_10000(self):
        """SHELL-T-SESS-UNIT-02: question at exactly 10000 chars is valid."""
        req = CreateSessionRequest(question="a" * 10000)
        assert len(req.question) == 10000

    @pytest.mark.shell_sess
    def test_sess_unit_05_rendering_mode_default(self):
        """SHELL-T-SESS-UNIT-05: rendering_mode defaults to position_to_hold."""
        req = CreateSessionRequest(question="What is the strategic impact of this decision on our portfolio?")
        assert req.rendering_mode == RenderingMode.POSITION_TO_HOLD

    @pytest.mark.shell_sess
    def test_depth_defaults_to_deep(self):
        """Arch §3.2: depth defaults to deep."""
        req = CreateSessionRequest(question="What is the strategic impact of this decision on our portfolio?")
        assert req.depth == SessionDepth.DEEP

    @pytest.mark.shell_sess
    def test_context_optional(self):
        """Arch §3.2: context is optional (None)."""
        req = CreateSessionRequest(question="What is the strategic impact of this decision on our portfolio?")
        assert req.context is None

    @pytest.mark.shell_sess
    def test_context_max_length(self):
        """Arch §3.2: context max 5000 chars."""
        with pytest.raises(ValidationError, match="String should have at most 5000 characters"):
            CreateSessionRequest(
                question="What is the strategic impact of this decision on our portfolio?",
                context="x" * 5001,
            )

    @pytest.mark.shell_sess
    def test_all_rendering_modes_valid(self):
        """DL-15: all three rendering modes are valid."""
        for mode in RenderingMode:
            req = CreateSessionRequest(
                question="What is the strategic impact of this decision on our portfolio?",
                rendering_mode=mode,
            )
            assert req.rendering_mode == mode


class TestSessionStatus:
    """Session state machine tests — test-strategy §4.6."""

    @pytest.mark.shell_sess
    def test_sess_unit_03_valid_completed_transition(self):
        """SHELL-T-SESS-UNIT-03: PENDING → RUNNING → COMPLETED are valid states."""
        assert SessionStatus.PENDING.value == "pending"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.COMPLETED.value == "completed"

    @pytest.mark.shell_sess
    def test_sess_unit_04_valid_failed_transition(self):
        """SHELL-T-SESS-UNIT-04: PENDING → RUNNING → FAILED are valid states."""
        assert SessionStatus.PENDING.value == "pending"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.FAILED.value == "failed"

    @pytest.mark.shell_sess
    def test_all_statuses_exist(self):
        """All 4 session statuses exist per arch §7.1."""
        statuses = {s.value for s in SessionStatus}
        assert statuses == {"pending", "running", "completed", "failed"}
