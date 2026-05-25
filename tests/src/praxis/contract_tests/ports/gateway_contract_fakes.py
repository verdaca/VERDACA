"""Shared fakes for Stage 11 gateway contract tests."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from praxis.kernel.gateway import (
    GatewayPolicy,
    GatewayWalConfig,
    GatewayWalStore,
    VerdacaGatewayService,
)
from praxis.kernel.session_index.models import (
    ArtifactRef as SessionIndexArtifactRef,
)
from praxis.kernel.session_index.models import (
    SessionFilter,
    SessionRecord,
)
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex
from praxis.ports.compaction import CompactionEstimate, CompactionRequest, CompactionResult
from praxis.ports.cost_meter import (
    BudgetScope,
    BudgetStatus,
    CostBreakdown,
    CostEvent,
    CostLedgerEntry,
    CostQuery,
    CostReport,
)
from praxis.ports.gateway_dto import (
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)
from praxis.ports.llm_proxy import LLMRequest, LLMResponse, LLMStreamChunk, ProviderInfo
from praxis.ports.memory import (
    MemoryEntry,
    MemoryHit,
    MemoryQuery,
    MigrationReport,
    PromotedMemory,
    PromotionRationale,
    PromotionTier,
    RevokedPromotion,
    StoredMemory,
)


class FakeLLMProxy:
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[LLMRequest] = []
        self.fail = fail

    def call(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        if self.fail:
            raise RuntimeError("llm failed")
        return LLMResponse(
            schema_version=1,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            content="Use the enterprise buyer path.",
            finish_reason="stop",
            input_tokens=11,
            output_tokens=7,
            raw_response_id="resp-1",
        )

    def stream(self, request: LLMRequest) -> Iterator[LLMStreamChunk]:
        self.calls.append(request)
        return iter(())

    def supported_providers(self) -> Sequence[ProviderInfo]:
        return ()


class FakeMemory:
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self) -> None:
        self.queries: list[MemoryQuery] = []
        self.stores: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> StoredMemory:
        self.stores.append(entry)
        return StoredMemory(
            schema_version=1,
            correlation_id=entry.correlation_id,
            idempotency_key=entry.idempotency_key,
            stored_id="mem-1",
        )

    def query(self, q: MemoryQuery) -> Sequence[MemoryHit]:
        self.queries.append(q)
        return (
            MemoryHit(
                schema_version=1,
                correlation_id=q.correlation_id,
                idempotency_key=q.idempotency_key,
                hit_id="hit-1",
                content="Prior buyer context",
                confidence=0.9,
                tier="session",
            ),
        )

    def promote(
        self,
        hit_id: str,
        target_tier: PromotionTier,
        rationale: PromotionRationale,
    ) -> PromotedMemory:
        return PromotedMemory(
            schema_version=1,
            correlation_id=rationale.correlation_id,
            idempotency_key=rationale.idempotency_key,
            promotion_id=f"{hit_id}:{target_tier.value}",
        )

    def revoke_promotion(self, promotion_id: str, reason: str) -> RevokedPromotion:
        return RevokedPromotion(
            schema_version=1,
            correlation_id="fake-memory",
            idempotency_key=None,
            promotion_id=promotion_id,
            reason=reason,
        )

    def migrate(self, from_version: int, to_version: int) -> MigrationReport:
        return MigrationReport(
            schema_version=1,
            correlation_id="fake-memory",
            idempotency_key=None,
            from_version=from_version,
            to_version=to_version,
            entries_migrated=0,
            migrator_signature="fake",
        )


class FakeCostMeter:
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self, *, consumed_usd: Decimal = Decimal("0")) -> None:
        self.budget_checks: list[BudgetScope] = []
        self.records: list[CostEvent] = []
        self.consumed_usd = consumed_usd

    def record(self, event: CostEvent) -> CostLedgerEntry:
        self.records.append(event)
        return CostLedgerEntry(
            schema_version=1,
            correlation_id=event.correlation_id,
            idempotency_key=event.idempotency_key,
            ledger_id="ledger-1",
            cost_usd=Decimal("0.0123"),
            cost_breakdown=CostBreakdown(
                schema_version=1,
                correlation_id=event.correlation_id,
                idempotency_key=event.idempotency_key,
                input_cost_usd=Decimal("0.0070"),
                output_cost_usd=Decimal("0.0053"),
                pricing_table_version="fake-v1",
            ),
            written_at=datetime.now(timezone.utc),
        )

    def query(self, q: CostQuery) -> CostReport:
        return CostReport(
            schema_version=1,
            correlation_id=q.correlation_id,
            idempotency_key=q.idempotency_key,
            entries=[],
            total_usd=Decimal("0"),
            query=q,
            pricing_table_versions=[],
        )

    def budget_check(self, scope: BudgetScope) -> BudgetStatus:
        self.budget_checks.append(scope)
        return BudgetStatus(
            schema_version=1,
            correlation_id=scope.correlation_id,
            idempotency_key=scope.idempotency_key,
            scope=scope,
            consumed_usd=self.consumed_usd,
            limit_usd=None,
            remaining_usd=None,
            status="ok",
        )


class FakeCompaction:
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self) -> None:
        self.compactions: list[CompactionRequest] = []

    def compact(self, request: CompactionRequest) -> CompactionResult:
        self.compactions.append(request)
        return CompactionResult(
            schema_version=1,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            compacted_payload=request.payload,
            tokens_in=100,
            tokens_out=50,
            strategy_applied=request.compaction_strategy,
            spans_preserved=request.preserve_span_ids,
            spans_evicted=[],
            determinism_hash="deterministic",
        )

    def estimate(self, request: CompactionRequest) -> CompactionEstimate:
        return CompactionEstimate(
            schema_version=1,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            estimated_tokens_out=50,
            estimated_strategy=request.compaction_strategy,
            confidence=1.0,
        )


class CountingSqliteSessionIndex(SqliteSessionIndex):
    def __init__(self, db_path: Path) -> None:
        self.index_calls = 0
        self.get_session_calls = 0
        self.get_artifact_calls = 0
        self.list_sessions_calls = 0
        super().__init__(db_path)

    def index_session(self, session_id: str, content: str) -> None:
        self.index_calls += 1
        super().index_session(session_id, content)

    def get_session(self, session_id: str) -> SessionRecord | None:
        self.get_session_calls += 1
        return super().get_session(session_id)

    def get_artifact(
        self,
        session_id: str,
        artifact_id: str,
    ) -> SessionIndexArtifactRef | None:
        self.get_artifact_calls += 1
        return super().get_artifact(session_id, artifact_id)

    def list_sessions(
        self,
        criteria: SessionFilter | None = None,
    ) -> Sequence[SessionRecord]:
        self.list_sessions_calls += 1
        return super().list_sessions(criteria)


@dataclass(slots=True)
class GatewayHarness:
    gateway: VerdacaGatewayService
    llm: FakeLLMProxy
    memory: FakeMemory
    cost: FakeCostMeter
    compaction: FakeCompaction
    session_index: CountingSqliteSessionIndex


def make_intent(
    idempotency_key: str = "idem-1",
    *,
    workspace_id: str = "workspace-1",
) -> StartAnalysisRequest:
    return StartAnalysisRequest(
        question="Which buyer path should we take?",
        requester_user_id="user-1",
        workspace_id=workspace_id,
        idempotency_key=idempotency_key,
    )


def make_ctx(request_id: str = "req-1") -> ChannelContext:
    return ChannelContext(
        caller_id="user-1",
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims={"sub": "user-1", "email": "user@example.test"}),
        channel=ChannelKind.CLI,
        channel_session_id="cli-session-1",
        request_id=request_id,
    )


def make_gateway_harness(
    tmp_path: Path,
    *,
    fail_llm: bool = False,
    policy: GatewayPolicy | None = None,
    consumed_usd: Decimal = Decimal("0"),
) -> GatewayHarness:
    llm = FakeLLMProxy(fail=fail_llm)
    memory = FakeMemory()
    cost = FakeCostMeter(consumed_usd=consumed_usd)
    compaction = FakeCompaction()
    session_index = CountingSqliteSessionIndex(tmp_path / "session-index.sqlite3")
    gateway = VerdacaGatewayService(
        llm_proxy=llm,
        memory=memory,
        cost_meter=cost,
        compaction=compaction,
        session_index=session_index,
        wal_store=GatewayWalStore(
            GatewayWalConfig(database_path=tmp_path / "gateway-idempotency.sqlite3")
        ),
        policy=policy or GatewayPolicy(allowed_user_ids=frozenset({"user-1"})),
    )
    return GatewayHarness(
        gateway=gateway,
        llm=llm,
        memory=memory,
        cost=cost,
        compaction=compaction,
        session_index=session_index,
    )


__all__ = [
    "CountingSqliteSessionIndex",
    "FakeCompaction",
    "FakeCostMeter",
    "FakeLLMProxy",
    "FakeMemory",
    "GatewayHarness",
    "make_ctx",
    "make_gateway_harness",
    "make_intent",
]
