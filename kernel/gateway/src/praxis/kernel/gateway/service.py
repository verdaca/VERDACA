"""Gateway service composition for Stage 11 Phase A."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar, Coroutine, TypeVar

from praxis.kernel.auth import AuthClaims, JwtVerifier, NonceStore, OidcPolicy
from praxis.kernel.gateway.composition_types import WebhookSigningKeyResolver
from praxis.kernel.gateway.dial import DIAL_LITELLM_MODEL, DIAL_LITELLM_PROVIDER
from praxis.kernel.gateway.policy import GatewayPolicy, evaluate_gateway_policy
from praxis.kernel.gateway.wal import AsyncSessionIndex, GatewayWalStore
from praxis.kernel.session_index.models import SessionFilter, SessionRecord
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.common import Message
from praxis.ports.compaction import CompactionPort, CompactionRequest
from praxis.ports.cost_meter import BudgetScope, CostEvent, CostMeterPort
from praxis.ports.gateway import ChannelAdapterPort
from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    ChannelContext,
    ChannelKind,
    SessionHandle,
    StartAnalysisRequest,
)
from praxis.ports.gateway_errors import GatewayCtxError
from praxis.ports.llm_proxy import LLMProxyPort, LLMRequest
from praxis.ports.memory import MemoryEntry, MemoryPort, MemoryQuery
from praxis.ports.serialization import SerializablePayload

_GATEWAY_PORT_NAME = "gateway"
_T = TypeVar("_T")


@dataclass(slots=True, kw_only=True)
class VerdacaGatewayService:
    """Implementation of the channel-neutral GatewayPort service."""

    API_VERSION: ClassVar[str] = "1.0.0"

    llm_proxy: LLMProxyPort
    memory: MemoryPort
    cost_meter: CostMeterPort
    compaction: CompactionPort
    session_index: SessionIndexPort
    channel_adapters: dict[ChannelKind, ChannelAdapterPort]
    jwt_verifier: JwtVerifier
    oidc_policy: OidcPolicy
    nonce_store: NonceStore
    webhook_resolver: WebhookSigningKeyResolver
    policy: GatewayPolicy
    wal_store: GatewayWalStore | None = None

    @property
    def is_wired(self) -> bool:
        """Return whether all required composition ports have been supplied."""
        return True

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        """Execute one channel-neutral analysis request."""
        now = datetime.now(timezone.utc)
        self._run_auth_first(intent, ctx, now)

        policy_decision = evaluate_gateway_policy(intent, ctx, self.policy, self.cost_meter)
        if not policy_decision.allowed:
            raise self._policy_error(ctx, policy_decision.reason, now)

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
                    occurred_at=now,
                    scope=BudgetScope(
                        schema_version=1,
                        correlation_id=ctx.request_id,
                        idempotency_key=intent.idempotency_key,
                        scope_kind="session",
                        scope_id=self._session_id(intent),
                    ),
                )
            )
            result = self._build_result(intent, ctx, llm_response.content, ledger.cost_usd, now)
            self.session_index.index_session(
                result.session.session_id,
                self._session_index_content(intent, ctx, result, now),
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
            raise self._gateway_error(ctx, "execute", exc, now) from exc

        if self.wal_store is not None:
            self.wal_store.complete_attempt(intent.idempotency_key, result)
        return result

    def _run_auth_first(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        now: datetime,
    ) -> AuthClaims:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                return asyncio.run(self._auth_first(intent, ctx))
            except Exception as exc:
                raise self._auth_error(ctx, exc, now) from exc
        raise RuntimeError("Gateway execute API must be called outside an active event loop")

    async def _auth_first(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AuthClaims:
        bearer_token = self._bearer_token(ctx)
        verified_claims = await self.oidc_policy.authenticate(bearer_token)
        await self.nonce_store.check_and_mark(self._nonce_value(ctx, verified_claims))
        await self.policy.enforce_budget(verified_claims)
        return verified_claims

    @staticmethod
    def _bearer_token(ctx: ChannelContext) -> str:
        token = ctx.rate_limit_token
        if token is None or not token.strip():
            raise ValueError("missing bearer token")
        return token

    @staticmethod
    def _nonce_value(ctx: ChannelContext, verified_claims: AuthClaims) -> str:
        nonce = verified_claims.get("nonce") or verified_claims.get("jti")
        if nonce is None:
            ctx_claims = ctx.auth_claims.unwrap()
            nonce = ctx_claims.get("nonce") or ctx_claims.get("jti")
        if nonce is None or not nonce.strip():
            raise ValueError("missing nonce")
        return nonce

    def get_session_summary(self, session_id: str) -> str:
        """Return a compact synopsis for a persisted session."""
        now = datetime.now(timezone.utc)
        record = self._read_session_record(session_id, now)
        payload = {
            "session_id": record.session_id,
            "status": record.status,
            "title": record.title,
            "source_uri": record.source_uri,
            "artifact_ids": record.artifact_ids,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def get_session_transcript(self, session_id: str) -> str:
        """Return the full SessionIndex transcript payload for a persisted session."""
        now = datetime.now(timezone.utc)
        record = self._read_session_record(session_id, now)
        payload = {
            "session_id": record.session_id,
            "user_id": record.user_id,
            "title": record.title,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "status": record.status,
            "skill_ids": record.skill_ids,
            "artifact_ids": record.artifact_ids,
            "source_uri": record.source_uri,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def get_artifact(self, session_id: str, artifact_id: str) -> ArtifactRef:
        """Return a gateway-visible artifact reference for a persisted session."""
        now = datetime.now(timezone.utc)
        artifact = self._run_session_index_read(
            AsyncSessionIndex(self.session_index).get_artifact(session_id, artifact_id)
        )
        if artifact is None:
            raise self._read_error(session_id, f"artifact_missing:{artifact_id}", now)
        return ArtifactRef(
            artifact_id=artifact.id,
            session_id=session_id,
            kind=artifact.kind,
            uri=artifact.payload_uri,
            title=None,
        )

    def list_sessions(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 50,
    ) -> Sequence[SessionHandle]:
        """Return persisted session handles, optionally scoped to a workspace."""
        if limit <= 0:
            return ()

        criteria = SessionFilter(
            schema_version=1,
            correlation_id="gateway:list_sessions",
            source_uri_prefix=(
                f"gateway://workspaces/{workspace_id}/" if workspace_id is not None else None
            ),
        )
        records = self._run_session_index_read(
            AsyncSessionIndex(self.session_index).list_sessions(criteria)
        )
        handles = [
            SessionHandle(
                session_id=record.session_id,
                status=record.status,
                source_uri=record.source_uri or "",
            )
            for record in records
        ]
        return tuple(handles[: min(limit, 50)])

    def _cached_result(self, idempotency_key: str) -> AnalysisResult | None:
        if self.wal_store is None:
            return None
        return self.wal_store.get_result(idempotency_key)

    def _read_session_record(self, session_id: str, now: datetime) -> SessionRecord:
        record = self._run_session_index_read(
            AsyncSessionIndex(self.session_index).get_session(session_id)
        )
        if record is None:
            raise self._read_error(session_id, "session_missing", now)
        return record

    @staticmethod
    def _run_session_index_read(coro: Coroutine[object, object, _T]) -> _T:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        coro.close()
        raise RuntimeError("Gateway read API must be called outside an active event loop")

    def _build_result(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        recommendation: str,
        cost_usd: Decimal,
        now: datetime,
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
                source_uri=self._source_uri(intent, ctx),
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
        now: datetime,
    ) -> str:
        payload = {
            "schema_version": 1,
            "correlation_id": ctx.request_id,
            "idempotency_key": intent.idempotency_key,
            "session_id": result.session.session_id,
            "user_id": intent.requester_user_id,
            "title": intent.question[:80],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
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
        ).hexdigest()[:32]
        return f"gw-{digest}"

    @staticmethod
    def _source_uri(intent: StartAnalysisRequest, ctx: ChannelContext) -> str:
        return (
            f"gateway://workspaces/{intent.workspace_id}/channels/{ctx.channel.value}/"
            f"sessions/{ctx.channel_session_id}"
        )

    @staticmethod
    def _gateway_error(
        ctx: ChannelContext,
        context_field: str,
        exc: Exception,
        occurred_at: datetime,
    ) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=ctx.request_id,
            occurred_at=occurred_at,
            violation_class="invariant",
            context_field=f"{context_field}:{type(exc).__module__}.{type(exc).__name__}",
        )

    @staticmethod
    def _policy_error(
        ctx: ChannelContext,
        reason: str | None,
        occurred_at: datetime,
    ) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=ctx.request_id,
            occurred_at=occurred_at,
            violation_class="invariant",
            context_field=f"policy:{reason or 'rejected'}",
        )

    @staticmethod
    def _auth_error(
        ctx: ChannelContext,
        exc: Exception,
        occurred_at: datetime,
    ) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=ctx.request_id,
            occurred_at=occurred_at,
            violation_class="invariant",
            context_field=f"auth:{type(exc).__module__}.{type(exc).__name__}",
        )

    @staticmethod
    def _read_error(
        session_id: str,
        context_field: str,
        occurred_at: datetime,
    ) -> GatewayCtxError:
        return GatewayCtxError(
            port_name=_GATEWAY_PORT_NAME,
            correlation_id=session_id,
            occurred_at=occurred_at,
            violation_class="invariant",
            context_field=f"read:{context_field}",
        )


__all__ = [
    "VerdacaGatewayService",
]
