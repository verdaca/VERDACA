"""Public dashboard tests — test-strategy §4.8.

SHELL-T-DASH-UNIT-01: GET /api/public/stats → aggregate metrics only
SHELL-T-DASH-UNIT-02: <10 sessions → insufficient_data flag
SHELL-T-DASH-UNIT-03: No question content, workspace names, or user IDs
SHELL-T-TENANT-INT-03: Public dashboard → no workspace_id, no question text
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from api.routes.public import PublicDashboardService


@pytest.fixture
def dashboard_service() -> PublicDashboardService:
    return PublicDashboardService(min_sessions=10)


def _make_session(
    *,
    workspace_id: str = "ws-1",
    question: str = "Should we expand to Europe?",
    status: str = "completed",
    cost_usd: float = 2.50,
    duration_seconds: float = 120.0,
) -> dict:
    return {
        "workspace_id": workspace_id,
        "question": question,
        "status": status,
        "cost_usd": cost_usd,
        "duration_seconds": duration_seconds,
        "started_at": datetime.now(timezone.utc),
    }


class TestPublicDashboard:
    """Public dashboard tests per test-strategy §4.8."""

    @pytest.mark.shell_dash
    @pytest.mark.critical
    def test_dash_unit_01_aggregate_metrics(self, dashboard_service: PublicDashboardService):
        """SHELL-T-DASH-UNIT-01: Returns aggregate metrics only."""
        sessions = [_make_session(cost_usd=2.0 + i * 0.1) for i in range(15)]
        result = dashboard_service.compute_stats(sessions)

        assert result.total_sessions == 15
        assert result.avg_cost_usd > 0
        assert result.avg_duration_seconds > 0
        assert result.insufficient_data is False

    @pytest.mark.shell_dash
    @pytest.mark.critical
    def test_dash_unit_02_insufficient_data(self, dashboard_service: PublicDashboardService):
        """SHELL-T-DASH-UNIT-02: <10 sessions → insufficient_data flag."""
        sessions = [_make_session() for _ in range(5)]
        result = dashboard_service.compute_stats(sessions)

        assert result.insufficient_data is True
        assert result.total_sessions == 5

    @pytest.mark.shell_dash
    @pytest.mark.critical
    def test_dash_unit_03_no_pii_in_response(self, dashboard_service: PublicDashboardService):
        """SHELL-T-DASH-UNIT-03: No question content, workspace names, or user IDs."""
        sessions = [
            _make_session(
                workspace_id="ws-secret-corp",
                question="Should we acquire competitor for $50M?",
            )
            for _ in range(15)
        ]
        result = dashboard_service.compute_stats(sessions)

        # Serialize to dict and check no PII fields
        result_dict = result.model_dump()
        result_str = str(result_dict)

        assert "ws-secret-corp" not in result_str
        assert "acquire competitor" not in result_str
        assert "$50M" not in result_str
        assert "workspace_id" not in result_dict
        assert "question" not in result_dict
        assert "user_id" not in result_dict

    @pytest.mark.shell_tenant
    @pytest.mark.critical
    def test_tenant_int_03_no_workspace_in_public(
        self, dashboard_service: PublicDashboardService
    ):
        """SHELL-T-TENANT-INT-03: Public dashboard has no workspace data."""
        sessions = [
            _make_session(workspace_id=f"ws-{i}") for i in range(15)
        ]
        result = dashboard_service.compute_stats(sessions)

        result_dict = result.model_dump()
        # PublicStatsResponse should not contain workspace_id
        assert "workspace_id" not in result_dict
        # Should not contain any ws- prefixed strings
        assert "ws-" not in str(result_dict)

    @pytest.mark.shell_dash
    def test_only_completed_counted(self, dashboard_service: PublicDashboardService):
        """Only completed sessions contribute to metrics."""
        sessions = (
            [_make_session(status="completed") for _ in range(12)]
            + [_make_session(status="pending") for _ in range(5)]
            + [_make_session(status="failed") for _ in range(3)]
        )
        result = dashboard_service.compute_stats(sessions)

        assert result.total_sessions == 12
        assert result.insufficient_data is False

    @pytest.mark.shell_dash
    def test_zero_sessions(self, dashboard_service: PublicDashboardService):
        """Zero sessions → insufficient_data."""
        result = dashboard_service.compute_stats([])
        assert result.total_sessions == 0
        assert result.insufficient_data is True

    @pytest.mark.shell_dash
    def test_exactly_10_sessions(self, dashboard_service: PublicDashboardService):
        """Exactly 10 sessions → data shown (threshold is >=10)."""
        sessions = [_make_session() for _ in range(10)]
        result = dashboard_service.compute_stats(sessions)

        assert result.total_sessions == 10
        assert result.insufficient_data is False
