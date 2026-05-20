"""Public dashboard endpoint — arch §8.

GET /api/public/stats — "Built With Praxis" dashboard data.

Privacy safeguards:
- No customer names, workspace names, or question content
- Only aggregate metrics (counts, averages, totals)
- Minimum 10 sessions before any metric is shown
- No per-customer breakdown

Binding anchors:
  - shell/architecture.md §8 "Built With Praxis" Public Dashboard (ADR-10)
  - shell/architecture.md §8.3 Privacy Safeguards
"""

from __future__ import annotations

from typing import Any

from api.models import PublicStatsResponse


class PublicDashboardService:
    """Produces aggregate-only public dashboard data (arch §8.1)."""

    def __init__(self, *, min_sessions: int = 10) -> None:
        self._min_sessions = min_sessions

    def compute_stats(self, sessions: list[dict[str, Any]]) -> PublicStatsResponse:
        """Compute aggregate stats from session records.

        Privacy: no question content, no workspace names, no user IDs.
        Only counts and averages from completed sessions.
        """
        completed = [
            s for s in sessions if s.get("status") == "completed"
        ]

        total = len(completed)

        if total < self._min_sessions:
            return PublicStatsResponse(
                total_sessions=total,
                avg_cost_usd=0.0,
                avg_duration_seconds=0.0,
                sessions_today=0,
                insufficient_data=True,
            )

        costs = [float(s.get("cost_usd", 0) or 0) for s in completed]
        durations = [float(s.get("duration_seconds", 0) or 0) for s in completed]

        from datetime import date, timezone
        today = date.today()
        today_count = sum(
            1 for s in completed
            if s.get("started_at") and _is_today(s["started_at"], today)
        )

        avg_cost = sum(costs) / total if total > 0 else 0.0
        avg_duration = sum(durations) / total if total > 0 else 0.0

        return PublicStatsResponse(
            total_sessions=total,
            avg_cost_usd=round(avg_cost, 2),
            avg_duration_seconds=round(avg_duration, 1),
            sessions_today=today_count,
            insufficient_data=False,
        )


def _is_today(dt: Any, today: Any) -> bool:
    """Check if datetime falls on today. Handles both datetime and str."""
    from datetime import datetime
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return False
    if hasattr(dt, "date"):
        return dt.date() == today
    return False
