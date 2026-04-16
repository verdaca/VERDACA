"""Shared fixtures for Pi-Mono tests."""
from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio

from praxis.kernel.cost import (
    CacheRetention,
    CostTracker,
    Currency,
    LLMRequest,
    LLMResponse,
    ModelPricing,
    ProviderName,
)

SNAPSHOT_DIR = (
    Path(__file__).resolve().parents[1]
    / "praxis"
    / "kernel"
    / "cost"
    / "pricing"
    / "snapshots"
)


@pytest.fixture
def snapshot_dir() -> Path:
    return SNAPSHOT_DIR


@pytest.fixture
def frozen_clock() -> callable:
    fixed = datetime(2026, 4, 12, 14, 0, 0, tzinfo=UTC)
    return lambda: fixed


@pytest.fixture
def sample_pricing() -> ModelPricing:
    return ModelPricing(
        provider=ProviderName.FAKE,
        model_id="fake-model-1",
        cache_retention_key=CacheRetention.NONE,
        currency=Currency.USD,
        input_rate=Decimal("1.0000000000"),
        output_rate=Decimal("2.0000000000"),
        cache_read_rate=Decimal("0.1000000000"),
        cache_write_rate=Decimal("1.2500000000"),
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def sample_request() -> LLMRequest:
    return LLMRequest(
        request_id="01JTRKSES00000000000000001",
        provider=ProviderName.FAKE,
        model_id="fake-model-1",
        session_id="sess_test",
        workflow_id="wf_test",
        agent="winston",
        cache_retention=CacheRetention.NONE,
        tags={"cycle": "1"},
        started_at=datetime(2026, 4, 12, 14, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_response() -> LLMResponse:
    return LLMResponse(
        request_id="01JTRKSES00000000000000001",
        input_tokens=1000,
        output_tokens=500,
        cache_read_tokens=200,
        cache_write_tokens=100,
        finished_at=datetime(2026, 4, 12, 14, 0, 1, tzinfo=UTC),
        stop_reason="stop",
    )


@pytest_asyncio.fixture
async def sqlite_tracker(snapshot_dir: Path) -> AsyncIterator[CostTracker]:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        tracker = CostTracker(
            storage_url=f"sqlite+aiosqlite:///{db_path}",
            pricing_snapshot_dir=snapshot_dir,
        )
        await tracker.initialize()
        try:
            yield tracker
        finally:
            await tracker.close()
