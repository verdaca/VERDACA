"""Execution normalization helpers for the Stage 11 gateway service."""

from __future__ import annotations

from dataclasses import dataclass

from praxis.ports.gateway_dto import ChannelContext, StartAnalysisRequest


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedExecution:
    """Stable internal shape handed from gateway entrypoint to composition."""

    question: str
    caller_id: str
    workspace_id: str
    idempotency_key: str
    request_id: str
    channel_session_id: str


def normalize_execution_request(
    intent: StartAnalysisRequest,
    ctx: ChannelContext,
) -> NormalizedExecution:
    """Normalize public DTOs into the gateway's internal execution shape."""
    return NormalizedExecution(
        question=intent.question,
        caller_id=ctx.caller_id,
        workspace_id=intent.workspace_id,
        idempotency_key=intent.idempotency_key,
        request_id=ctx.request_id,
        channel_session_id=ctx.channel_session_id,
    )


__all__ = [
    "NormalizedExecution",
    "normalize_execution_request",
]
