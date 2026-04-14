"""Integration tests for CostTracker against SQLite."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from praxis.kernel.cost import (
    CacheRetention,
    CostTracker,
    Filter,
    Invoice,
    InvoiceLine,
    LLMRequest,
    LLMResponse,
    ProviderName,
    TimeRange,
    UnknownModelError,
)


REQ_IDS = [f"01JTRK{str(i).zfill(20)}" for i in range(100)]


def _req(idx: int, session_id: str = "sess_a", agent: str = "winston") -> LLMRequest:
    return LLMRequest(
        request_id=REQ_IDS[idx],
        provider=ProviderName.ANTHROPIC,
        model_id="claude-opus-4-6",
        session_id=session_id,
        workflow_id="wf_a",
        agent=agent,
        cache_retention=CacheRetention.NONE,
        tags={"cycle": "1"},
        started_at=datetime(2026, 4, 12, 14, 0, idx, tzinfo=UTC),
    )


def _resp(idx: int, input_tokens: int = 1000, output_tokens: int = 500) -> LLMResponse:
    return LLMResponse(
        request_id=REQ_IDS[idx],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=0,
        cache_write_tokens=0,
        finished_at=datetime(2026, 4, 12, 14, 0, idx, 500000, tzinfo=UTC),
        stop_reason="stop",
    )


@pytest.mark.asyncio
class TestTrackerLifecycle:
    async def test_initialize_and_close(self, sqlite_tracker: CostTracker) -> None:
        health = await sqlite_tracker.health()
        assert health["status"] == "healthy"
        assert health["pricing_catalog_loaded"] is True


@pytest.mark.asyncio
class TestTrackCost:
    async def test_happy_path(self, sqlite_tracker: CostTracker) -> None:
        record = await sqlite_tracker.track_cost(_req(0), _resp(0))
        # 1000*15/1e6 + 500*75/1e6 = 0.015 + 0.0375 = 0.0525
        assert record.cost.total == Decimal("0.0525000000")
        assert record.agent == "winston"
        assert record.session_id == "sess_a"

    async def test_idempotent_double_tracking(
        self, sqlite_tracker: CostTracker
    ) -> None:
        r1 = await sqlite_tracker.track_cost(_req(0), _resp(0))
        r2 = await sqlite_tracker.track_cost(_req(0), _resp(0))
        assert r1.record_id == r2.record_id

    async def test_unknown_model_raises(self, sqlite_tracker: CostTracker) -> None:
        req = LLMRequest(
            request_id=REQ_IDS[1],
            provider=ProviderName.ANTHROPIC,
            model_id="claude-nonexistent",
            started_at=datetime(2026, 4, 12, tzinfo=UTC),
        )
        resp = LLMResponse(
            request_id=REQ_IDS[1],
            input_tokens=10,
            output_tokens=5,
            finished_at=datetime(2026, 4, 12, 14, 1, tzinfo=UTC),
            stop_reason="stop",
        )
        with pytest.raises(UnknownModelError):
            await sqlite_tracker.track_cost(req, resp)

    async def test_mismatched_request_id_raises(
        self, sqlite_tracker: CostTracker
    ) -> None:
        req = _req(0)
        resp = _resp(1)  # different request_id
        with pytest.raises(ValueError, match="request_id mismatch"):
            await sqlite_tracker.track_cost(req, resp)


@pytest.mark.asyncio
class TestAggregation:
    async def test_session_summary(self, sqlite_tracker: CostTracker) -> None:
        for i in range(3):
            await sqlite_tracker.track_cost(_req(i), _resp(i))
        summary = await sqlite_tracker.get_session_cost("sess_a")
        assert summary.request_count == 3
        # 3 records × 0.0525 each = 0.1575
        assert summary.cost.total == Decimal("0.1575000000")

    async def test_empty_session_returns_zero_summary(
        self, sqlite_tracker: CostTracker
    ) -> None:
        summary = await sqlite_tracker.get_session_cost("sess_nonexistent")
        assert summary.request_count == 0
        assert summary.cost.total == Decimal("0")
        assert summary.first_request_at is None

    async def test_workflow_summary(self, sqlite_tracker: CostTracker) -> None:
        for i in range(2):
            await sqlite_tracker.track_cost(_req(i), _resp(i))
        summary = await sqlite_tracker.get_workflow_cost("wf_a")
        assert summary.request_count == 2

    async def test_agent_summary_time_range(
        self, sqlite_tracker: CostTracker
    ) -> None:
        for i in range(3):
            await sqlite_tracker.track_cost(_req(i), _resp(i))
        tr = TimeRange(
            start=datetime(2026, 4, 12, tzinfo=UTC),
            end=datetime(2026, 4, 13, tzinfo=UTC),
        )
        summary = await sqlite_tracker.get_agent_cost("winston", tr)
        assert summary.request_count == 3

    async def test_lifetime_cost_aggregates_all(
        self, sqlite_tracker: CostTracker
    ) -> None:
        for i in range(5):
            await sqlite_tracker.track_cost(
                _req(i, session_id=f"sess_{i}"), _resp(i)
            )
        lifetime = await sqlite_tracker.get_lifetime_cost()
        assert lifetime.request_count == 5


@pytest.mark.asyncio
class TestReconciliation:
    async def test_reconciliation_clean_on_synthetic(
        self, sqlite_tracker: CostTracker
    ) -> None:
        for i in range(3):
            await sqlite_tracker.track_cost(_req(i), _resp(i))

        # Build an invoice that exactly matches what we wrote
        invoice = Invoice(
            invoice_id="inv-test-001",
            provider=ProviderName.ANTHROPIC,
            period_start=datetime(2026, 4, 12, tzinfo=UTC),
            period_end=datetime(2026, 4, 13, tzinfo=UTC),
            lines=[
                InvoiceLine(
                    provider=ProviderName.ANTHROPIC,
                    model_id="claude-opus-4-6",
                    period_start=datetime(2026, 4, 12, tzinfo=UTC),
                    period_end=datetime(2026, 4, 13, tzinfo=UTC),
                    input_tokens=3000,
                    output_tokens=1500,
                    cache_read_tokens=0,
                    cache_write_tokens=0,
                    amount=Decimal("0.1575000000"),
                )
            ],
            total=Decimal("0.1575000000"),
        )
        report = await sqlite_tracker.reconcile(invoice)
        assert report.status == "clean"
        assert report.total_delta == Decimal("0")
