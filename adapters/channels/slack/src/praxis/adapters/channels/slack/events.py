"""Slack event parsing."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from praxis.kernel.auth import extract_claims
from praxis.kernel.auth.jwt import JwtVerifier
from praxis.ports.gateway_dto import (
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)


@dataclass(frozen=True, slots=True)
class SlackEvent:
    intent: StartAnalysisRequest
    ctx: ChannelContext
    response_url: str | None = None


def parse_event(
    envelope: Mapping[str, Any],
    *,
    claims: Mapping[str, Any] | str | None = None,
    authorization_header: str | None = None,
    verifier: JwtVerifier,
) -> SlackEvent | None:
    event = _as_mapping(envelope.get("event"))
    if event.get("type") != "app_mention":
        return None

    user_id = str(event.get("user") or "")
    channel_id = str(event.get("channel") or "")
    team_id = str(envelope.get("team_id") or event.get("team") or "")
    event_ts = str(event.get("event_ts") or event.get("ts") or uuid.uuid4())
    thread_ts = str(event.get("thread_ts") or event.get("ts") or channel_id)
    text = str(event.get("text") or "").strip()

    bearer_token = _extract_bearer_token(
        authorization_header
        or _optional_str(envelope.get("authorization"))
        or _optional_str(envelope.get("bearer_token"))
    )
    claim_payload = claims or bearer_token
    auth_claims = _resolve_claims(claim_payload, verifier=verifier)
    intent = StartAnalysisRequest(
        question=text,
        requester_user_id=user_id,
        workspace_id=team_id,
        idempotency_key=event_ts,
        metadata={
            "channel_id": channel_id,
            "event_ts": event_ts,
            "team_id": team_id,
            "thread_ts": thread_ts,
        },
    )
    ctx = ChannelContext(
        caller_id=user_id,
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims=auth_claims),
        channel=ChannelKind.SLACK,
        channel_session_id=thread_ts,
        request_id=str(uuid.uuid4()),
        trace_id=event_ts,
        rate_limit_token=bearer_token,
    )
    return SlackEvent(intent=intent, ctx=ctx, response_url=_response_url(envelope))


def _resolve_claims(
    payload: Mapping[str, Any] | str | None,
    *,
    verifier: JwtVerifier,
) -> dict[str, str]:
    if payload is None:
        raise ValueError("Slack auth claims or bearer token are required")
    if isinstance(payload, str):
        if verifier is None:
            raise ValueError("Slack bearer token requires a JwtVerifier")
        return extract_claims(payload, verifier)
    return {str(key): str(value) for key, value in payload.items()}


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_str(value: object) -> str | None:
    return str(value) if value else None


def _extract_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("Bearer ").strip() or None


def _response_url(envelope: Mapping[str, Any]) -> str | None:
    response_url = envelope.get("response_url")
    return str(response_url) if response_url else None
