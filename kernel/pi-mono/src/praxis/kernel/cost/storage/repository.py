"""Async data access for cost records, events, and reconciliation reports."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..errors import StorageError
from ..models import (
    AggregationScope,
    CacheRetention,
    CostAmount,
    CostEvent,
    CostRecord,
    CostSummary,
    Currency,
    Filter,
    ProviderName,
)
from .dialects import dialect_specific_upsert
from .schema import Base, CostRecordRow, EventRow, ReconciliationReportRow


def _row_to_cost_record(row: CostRecordRow) -> CostRecord:
    cost = CostAmount(
        input=row.cost_input,
        output=row.cost_output,
        cache_read=row.cost_cache_read,
        cache_write=row.cost_cache_write,
        total=row.cost_total,
        currency=Currency(row.currency),
    )
    return CostRecord(
        record_id=row.record_id,
        request_id=row.request_id,
        provider=ProviderName(row.provider),
        model_id=row.model_id,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        cache_read_tokens=row.cache_read_tokens,
        cache_write_tokens=row.cache_write_tokens,
        total_tokens=row.total_tokens,
        cost=cost,
        pricing_effective_from=_ensure_utc(row.pricing_effective_from),
        pricing_snapshot_sha256=row.pricing_snapshot_sha256,
        session_id=row.session_id,
        workflow_id=row.workflow_id,
        agent=row.agent,
        parent_request_id=row.parent_request_id,
        tags=row.tags or {},
        started_at=_ensure_utc(row.started_at),
        finished_at=_ensure_utc(row.finished_at),
        latency_ms=row.latency_ms,
        stop_reason=row.stop_reason,  # type: ignore[arg-type]
        error_message=row.error_message,
        cache_retention=CacheRetention(row.cache_retention),
        created_at=_ensure_utc(row.created_at),
    )


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _cost_record_to_values(record: CostRecord) -> dict:
    return {
        "record_id": record.record_id,
        "request_id": record.request_id,
        "provider": record.provider.value,
        "model_id": record.model_id,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "cache_read_tokens": record.cache_read_tokens,
        "cache_write_tokens": record.cache_write_tokens,
        "total_tokens": record.total_tokens,
        "cost_input": record.cost.input,
        "cost_output": record.cost.output,
        "cost_cache_read": record.cost.cache_read,
        "cost_cache_write": record.cost.cache_write,
        "cost_total": record.cost.total,
        "currency": record.cost.currency.value,
        "pricing_effective_from": record.pricing_effective_from,
        "pricing_snapshot_sha256": record.pricing_snapshot_sha256,
        "session_id": record.session_id,
        "workflow_id": record.workflow_id,
        "agent": record.agent,
        "parent_request_id": record.parent_request_id,
        "tags": record.tags,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "latency_ms": record.latency_ms,
        "stop_reason": record.stop_reason,
        "error_message": record.error_message,
        "cache_retention": record.cache_retention.value,
        "lifecycle_state": "active",
        "amended_by_record_id": None,
        "created_at": record.created_at,
    }


class CostRepository:
    def __init__(self, storage_url: str, engine_options: dict | None = None) -> None:
        opts = engine_options or {}
        self._engine = create_async_engine(storage_url, future=True, **opts)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )
        self._initialized = False

    async def initialize(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def close(self) -> None:
        await self._engine.dispose()
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    def session(self) -> AsyncSession:
        return self._session_factory()

    async def insert_record_with_event(
        self,
        record: CostRecord,
        event: CostEvent,
    ) -> CostRecord:
        try:
            async with self._session_factory() as session, session.begin():
                values = _cost_record_to_values(record)
                row = await dialect_specific_upsert(session, values)

                event_payload = json.loads(event.model_dump_json())
                existing_event = await session.execute(
                    select(EventRow).where(EventRow.record_id == row.record_id)
                )
                if existing_event.scalar_one_or_none() is None:
                    session.add(
                        EventRow(
                            event_id=event.event_id,
                            event_type=event.event_type,
                            record_id=row.record_id,
                            payload=event_payload,
                            emitted_at=event.emitted_at,
                        )
                    )

                return _row_to_cost_record(row)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"insert_record_with_event failed: {exc}") from exc

    async def get_record_by_request_id(self, request_id: str) -> CostRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(CostRecordRow).where(CostRecordRow.request_id == request_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_cost_record(row) if row else None

    async def summary(
        self,
        filter_: Filter,
        scope: AggregationScope,
        scope_id: str,
        clock: datetime,
    ) -> CostSummary:
        async with self._session_factory() as session:
            stmt = select(
                func.coalesce(func.sum(CostRecordRow.input_tokens), 0),
                func.coalesce(func.sum(CostRecordRow.output_tokens), 0),
                func.coalesce(func.sum(CostRecordRow.cache_read_tokens), 0),
                func.coalesce(func.sum(CostRecordRow.cache_write_tokens), 0),
                func.coalesce(func.sum(CostRecordRow.total_tokens), 0),
                func.coalesce(func.sum(CostRecordRow.cost_input), 0),
                func.coalesce(func.sum(CostRecordRow.cost_output), 0),
                func.coalesce(func.sum(CostRecordRow.cost_cache_read), 0),
                func.coalesce(func.sum(CostRecordRow.cost_cache_write), 0),
                func.coalesce(func.sum(CostRecordRow.cost_total), 0),
                func.count(CostRecordRow.record_id),
                func.coalesce(
                    func.sum(
                        case(
                            (CostRecordRow.stop_reason.in_(("error", "aborted")), 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.min(CostRecordRow.started_at),
                func.max(CostRecordRow.started_at),
            ).where(*self._where_for_filter(filter_))

            result = await session.execute(stmt)
            row = result.one()
            (
                input_tokens,
                output_tokens,
                cache_read_tokens,
                cache_write_tokens,
                total_tokens,
                cost_input,
                cost_output,
                cost_cache_read,
                cost_cache_write,
                cost_total,
                request_count,
                error_count,
                first_at,
                last_at,
            ) = row

            def _d(v: Decimal | int | float | None) -> Decimal:
                if v is None:
                    return Decimal("0")
                if isinstance(v, Decimal):
                    return v
                return Decimal(str(v))

            cost = CostAmount(
                input=_d(cost_input),
                output=_d(cost_output),
                cache_read=_d(cost_cache_read),
                cache_write=_d(cost_cache_write),
                total=_d(cost_total),
                currency=Currency.USD,
            )

            return CostSummary(
                scope=scope,
                scope_id=scope_id,
                input_tokens=int(input_tokens or 0),
                output_tokens=int(output_tokens or 0),
                cache_read_tokens=int(cache_read_tokens or 0),
                cache_write_tokens=int(cache_write_tokens or 0),
                total_tokens=int(total_tokens or 0),
                cost=cost,
                request_count=int(request_count or 0),
                error_count=int(error_count or 0),
                first_request_at=_ensure_utc(first_at) if first_at else None,
                last_request_at=_ensure_utc(last_at) if last_at else None,
                computed_at=clock,
            )

    @staticmethod
    def _where_for_filter(f: Filter) -> list:
        conditions: list = []
        if f.provider is not None:
            conditions.append(CostRecordRow.provider == f.provider.value)
        if f.model_id is not None:
            conditions.append(CostRecordRow.model_id == f.model_id)
        if f.session_id is not None:
            conditions.append(CostRecordRow.session_id == f.session_id)
        if f.workflow_id is not None:
            conditions.append(CostRecordRow.workflow_id == f.workflow_id)
        if f.agent is not None:
            conditions.append(CostRecordRow.agent == f.agent)
        if f.stop_reason is not None:
            conditions.append(CostRecordRow.stop_reason == f.stop_reason)
        if f.time_range is not None:
            conditions.append(CostRecordRow.started_at >= f.time_range.start)
            conditions.append(CostRecordRow.started_at < f.time_range.end)
        if not conditions:
            return [CostRecordRow.record_id.is_not(None)]
        return [and_(*conditions)]

    async def lifetime_totals(self, clock: datetime) -> CostSummary:
        return await self.summary(Filter(), AggregationScope.ALL, "all", clock)

    async def insert_reconciliation(self, row_values: dict) -> None:
        async with self._session_factory() as session, session.begin():
            session.add(ReconciliationReportRow(**row_values))

    async def outbox_undelivered_count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count(EventRow.event_id)).where(
                    EventRow.delivered_at.is_(None)
                )
            )
            return int(result.scalar_one())
