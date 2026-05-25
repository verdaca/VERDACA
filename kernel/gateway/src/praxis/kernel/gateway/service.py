"""Gateway service composition for Stage 11 Phase A."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar

from praxis.kernel.gateway.dial import DIAL_LITELLM_MODEL, DIAL_LITELLM_PROVIDER
from praxis.kernel.gateway.policy import GatewayPolicy, evaluate_gateway_policy
from praxis.kernel.gateway.wal import GatewayWalStore
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.common import Message
from praxis.ports.compaction import CompactionPort, CompactionRequest
from praxis.ports.cost_meter import BudgetScope, CostEvent, CostMeterPort
from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    ChannelContext,
    SessionHandle,
    StartAnalysisRequest,
)
from praxis.ports.gateway_errors import GatewayCtxError
from praxis.ports.llm_proxy import LLMProxyPort, LLMRequest
from praxis.ports.memory import MemoryEntry, MemoryPort, MemoryQuery
from praxis.ports.serialization import SerializablePayload

_GATEWAY_PORT_NAME = "gateway"

@dataclass(slots=True, kw_only=True)
class VerdacaGatewayService:
    """Implementation of the channel-neutral GatewayPort service."""

    API_VERSION: ClassVar[str] = "1.0.0"

    llm_proxy: LLMProxyPort
    memory: MemoryPort
    cost_meter: CostMeterPort
    compaction: CompactionPort
    session_index: SessionIndexPort
    wal_store: GatewayWalStore | None = None
    policy: GatewayPolicy = GatewayPolicy()

    @property
    def is_wired(self) -> bool:
        """Return whether all required composition ports have been supplied."""
        return True

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        """Execute one channel-neutral analysis request."""
        policy_decision = evaluate_gateway_policy(intent, ctx, self.policy, self.cost_meter)
        if not policy_decision.allowed:
            raise self._policy_error(ctx, policy_decision.reason)

        cached = self._cached_result(intent.idempotency_key)
        if cached is not None:
            return cached
        if self.wal_store is not None:
            self.wal_store.begin_attempt(intent.idempotency_key)

        try:
            memory_hits = self.memory.query(
                MemoryQuery(
                    schema_version=1,
                    correlation_id=ctx.request_id,
                    idempotency_key=intent.idempotency_key,
                    query_text=intent.question,
                    k=5,
                )
            )
            compacted = self.compaction.compact(
                CompactionRequest(
                    schema_version=1,
                    correlation_id=ctx.request_id,
                    idempotency_key=intent.idempotency_key,
                    payload=SerializablePayload(
                        schema_version=1,
                        correlation_id=ctx.request_id,
                        idempotency_key=intent.idempotency_key,
                        body={
                            "question": intent.question,
                            "workspace_id": intent.workspace_id,
                            "memory_hits": [hit.content for hit in memory_hits],
                        },
                        payload_kind="gateway_prompt",
                    ),
                    token_budget=4_000,
                    compaction_strategy="lossy_eviction",
                    preserve_span_ids=["question"],
                )
            )
            llm_response = self.llm_proxy.call(
                LLMRequest(
                    schema_version=1,
                    correlation_id=ctx.request_id,
                    idempotency_key=intent.idempotency_key,
                    provider=DIAL_LITELLM_PROVIDER,
                    model=DIAL_LITELLM_MODEL,
                    messages=[
                        Message(
                            schema_version=1,
                            correlation_id=ctx.request_id,
                            idempotency_key=intent.idempotency_key,
                            role="user",
                            content=json.dumps(
                                compacted.compacted_payload.body,
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        )
                    ],
                    max_tokens=1_024,
                    temperature=0.0,
                    compression_hint="none",
                )
            )
            ledger = self.cost_meter.record(
                CostEvent(
                    schema_version=1,
                    correlation_id=ctx.request_id,
                    idempotency_key=intent.idempotency_key,
                    provider=DIAL_LITELLM_PROVIDER,
                    model=DIAL_LITELLM_MODEL,
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                    occurred_at=datetime.now(timezone.utc),
                    scope=BudgetScope(
                        schema_version=1,
                        correlation_id=ctx.request_id,
                        idempotency_key=intent.idempotency_key,
                        scope_kind="session",
                        scope_id=self._session_id(intent),
                    ),
                )
            )
            result = self._build_result(intent, ctx, llm_response.content, ledger.cost_usd)
            self.session_index.index_session(
                result.session.session_id,
                self._session_index_content(intent, ctx, result),
            )
            self.memory.store(
                MemoryEntry(
                    schema_version=1,
                    correlation_id=ctx.request_id,
                    idempotency_key=intent.idempotency_key,
                    content=result.recommendation,
                    metadata={
                        "session_id": result.session.session_id,
                        "workspace_id": intent.workspace_id,
                    },
                    confidence=1.0,
                    source_span_id=ctx.request_id,
                )
            )
        except Exception as exc:
            raise self._gateway_error(ctx, "execute", exc) from exc

        if self.wal_store is not None:
            self.wal_store.complete_attempt(intent.idempotency_key, result)
        return result

    def _cached_result(self, idempotency_key: str) -> AnalysisResult | None:
        if self.wal_store is None:
            return None
        return self.wal_store.get_result(idempotency_key)

    def _build_result(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        recommendation: str,
        cost_usd: Decimal,
    ) -> AnalysisResult:
        session_id = self._session_id(intent)
        artifact = ArtifactRef(
            artifact_id=f"{session_id}-summary",
            session_id=session_id,
            kind="summary",
            uri=f"session://{session_id}/artifacts/{session_id}-summary",
            title="Gateway analysis summary",
        )
        return AnalysisResult(
            session=SessionHandle(
                session_id=session_id,
                status="completed",
                source_uri=f"gateway://{ctx.channel.value}/{ctx.channel_session_id}",
            ),
            recommendation=recommendation,
            cited_tradeoffs=("cost_meter_recorded", "memory_context_queried"),
            artifacts=(artifact,),
            cost_usd=cost_usd,
        )

    def _session_index_content(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        result: AnalysisResult,
    ) -> str:
        payload = {
            "schema_version": 1,
            "correlation_id": ctx.request_id,
            "idempotency_key": intent.idempotency_key,
            "session_id": result.session.session_id,
            "user_id": intent.requester_user_id,
            "title": intent.question[:80],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": result.session.status,
            "skill_ids": ["stage11-gateway"],
            "artifact_ids": [artifact.artifact_id for artifact in result.artifacts],
            "source_uri": result.session.source_uri,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _session_id(intent: StartAnalysisRequest) -> str:
        digest = hashlib.sha256(
            f"{intent.workspace_id}:{intent.idempotency_key}".encode("utf-8")
        ).hexdigest()[:16]
        return f"gw-{digest}"

    @staticmethod
    def _gateway_error(ctx: ChannelContext, context_field: str, exc: Exception) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=ctx.request_id,
            occurred_at=datetime.now(timezone.utc),
            violation_class="invariant",
            context_field=f"{context_field}:{type(exc).__name__}",
        )

    @staticmethod
    def _policy_error(ctx: ChannelContext, reason: str | None) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=ctx.request_id,
            occurred_at=datetime.now(timezone.utc),
            violation_class="invariant",
            context_field=f"policy:{reason or 'rejected'}",
        )


__all__ = [
    "VerdacaGatewayService",
]
