"""CostTracker — the single public entry point for Pi-Mono."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ulid import ULID

from .aggregator import Aggregator
from .errors import CostTrackerError, StorageError
from .events import EventStream
from .math import compute_cost
from .models import (
    AggregationScope,
    CostEvent,
    CostRecord,
    CostSummary,
    Filter,
    Invoice,
    LLMRequest,
    LLMResponse,
    ProviderName,
    TimeRange,
)
from .pricing import PricingCatalog, load_snapshot_dir
from .providers import get_provider
from .reconciliation import Reconciler
from .storage import CostRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_ulid() -> str:
    return str(ULID())


class CostTracker:
    """The single public entry point."""

    def __init__(
        self,
        storage_url: str,
        pricing_snapshot_dir: Path,
        clock: Callable[[], datetime] = _utcnow,
        engine_options: dict | None = None,
    ) -> None:
        self._storage_url = storage_url
        self._pricing_snapshot_dir = pricing_snapshot_dir
        self._clock = clock
        self._engine_options = engine_options or {}
        self._repo = CostRepository(storage_url, engine_options)
        self._catalog: PricingCatalog | None = None
        self._aggregator: Aggregator | None = None
        self._event_stream: EventStream | None = None
        self._reconciler: Reconciler | None = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        await self._repo.initialize()
        rows = load_snapshot_dir(self._pricing_snapshot_dir)
        self._catalog = PricingCatalog(rows)
        self._aggregator = Aggregator(self._repo, self._clock)
        self._event_stream = EventStream(self._repo)
        self._reconciler = Reconciler(self._repo, self._clock)
        self._initialized = True

    async def close(self) -> None:
        await self._repo.close()
        self._initialized = False

    async def __aenter__(self) -> "CostTracker":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    def _require_initialized(self) -> None:
        if not self._initialized or self._catalog is None:
            raise CostTrackerError("CostTracker not initialized; call initialize() first")

    async def track_cost(
        self,
        request: LLMRequest,
        response: LLMResponse,
    ) -> CostRecord:
        self._require_initialized()
        assert self._catalog is not None
        if request.request_id != response.request_id:
            raise ValueError(
                f"request_id mismatch: {request.request_id} vs {response.request_id}"
            )
        if response.finished_at < request.started_at:
            raise ValueError("response.finished_at < request.started_at")

        existing = await self._repo.get_record_by_request_id(request.request_id)
        if existing is not None:
            return existing

        pricing = self._catalog.lookup(
            provider=request.provider,
            model_id=request.model_id,
            cache_retention=request.cache_retention,
            started_at=request.started_at,
        )
        cost = compute_cost(response, pricing)
        now = self._clock()

        latency_ms = int(
            (response.finished_at - request.started_at).total_seconds() * 1000
        )

        record = CostRecord(
            record_id=_new_ulid(),
            request_id=request.request_id,
            provider=request.provider,
            model_id=request.model_id,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cache_read_tokens=response.cache_read_tokens,
            cache_write_tokens=response.cache_write_tokens,
            total_tokens=(
                response.input_tokens
                + response.output_tokens
                + response.cache_read_tokens
                + response.cache_write_tokens
            ),
            cost=cost,
            pricing_effective_from=pricing.effective_from,
            pricing_snapshot_sha256=pricing.snapshot_sha256 or "",
            session_id=request.session_id,
            workflow_id=request.workflow_id,
            agent=request.agent,
            parent_request_id=request.parent_request_id,
            tags=dict(request.tags),
            started_at=request.started_at,
            finished_at=response.finished_at,
            latency_ms=max(latency_ms, 0),
            stop_reason=response.stop_reason,
            error_message=response.error_message,
            cache_retention=request.cache_retention,
            created_at=now,
        )

        event = CostEvent(
            event_id=_new_ulid(),
            event_type="record_created",
            emitted_at=now,
            record=record,
        )

        persisted = await self._repo.insert_record_with_event(record, event)
        return persisted

    async def track_raw_response(
        self,
        request: LLMRequest,
        raw_response: Any,
    ) -> CostRecord:
        provider_cls = get_provider(request.provider)
        response = provider_cls.extract_tokens(request, raw_response)
        return await self.track_cost(request, response)

    async def get_session_cost(self, session_id: str) -> CostSummary:
        self._require_initialized()
        assert self._aggregator is not None
        if not session_id:
            raise ValueError("session_id must be non-empty")
        return await self._aggregator.summary(
            Filter(session_id=session_id),
            AggregationScope.SESSION,
            session_id,
        )

    async def get_workflow_cost(self, workflow_id: str) -> CostSummary:
        self._require_initialized()
        assert self._aggregator is not None
        if not workflow_id:
            raise ValueError("workflow_id must be non-empty")
        return await self._aggregator.summary(
            Filter(workflow_id=workflow_id),
            AggregationScope.WORKFLOW,
            workflow_id,
        )

    async def get_agent_cost(self, agent: str, time_range: TimeRange) -> CostSummary:
        self._require_initialized()
        assert self._aggregator is not None
        if not agent:
            raise ValueError("agent must be non-empty")
        return await self._aggregator.summary(
            Filter(agent=agent, time_range=time_range),
            AggregationScope.AGENT,
            agent,
        )

    async def get_cost_summary(self, filter_: Filter) -> CostSummary:
        self._require_initialized()
        assert self._aggregator is not None
        return await self._aggregator.summary(filter_, AggregationScope.ALL, "all")

    async def get_lifetime_cost(self) -> CostSummary:
        self._require_initialized()
        assert self._aggregator is not None
        return await self._aggregator.summary(
            Filter(), AggregationScope.ALL, "lifetime"
        )

    async def stream_events(
        self,
        filter_: Filter,
        from_event_id: str | None = None,
        poll_interval_ms: int = 100,
    ) -> AsyncIterator[CostEvent]:
        self._require_initialized()
        assert self._event_stream is not None
        async for event in self._event_stream.stream(filter_, from_event_id, poll_interval_ms):
            yield event

    async def reconcile(
        self,
        invoice: Invoice,
        tolerance_pct: str | None = None,
    ) -> "ReconciliationReport":  # noqa: F821
        self._require_initialized()
        assert self._reconciler is not None
        from decimal import Decimal

        tolerance = Decimal(tolerance_pct) if tolerance_pct else Decimal("0.001")
        return await self._reconciler.reconcile(invoice, tolerance)

    async def health(self) -> dict:
        try:
            undelivered = await self._repo.outbox_undelivered_count() if self._initialized else 0
            db_ok = self._initialized
        except Exception:  # noqa: BLE001
            undelivered = 0
            db_ok = False
        status = "healthy" if db_ok else "unhealthy"
        return {
            "status": status,
            "db_reachable": db_ok,
            "outbox_undelivered_count": undelivered,
            "pricing_catalog_loaded": self._catalog is not None,
            "pricing_catalog_rows": len(self._catalog) if self._catalog else 0,
        }
