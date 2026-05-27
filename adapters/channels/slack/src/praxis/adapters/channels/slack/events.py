"""Slack event parsing.

Unverified JWT payload decoding in this module is retained only for tests and
synthetic fixture paths. Production callers must provide pre-verified claims or
use a JwtVerifier with a raw bearer token.
"""

from __future__ import annotations

import base64
import json
import uuid
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from praxis.kernel.auth.jwt import JwtVerifier
from praxis.ports.gateway_dto import (
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)

_AUTH_AUDIENCE = "verdaca-channel-adapter"


@dataclass(frozen=True, slots=True)
class SlackEvent:
    intent: StartAnalysisRequest
    ctx: ChannelContext
    response_url: str | None = None


def extract_claims(
    payload: Mapping[str, Any] | str,
    verifier: JwtVerifier | None = None,
) -> dict[str, str]:
    if verifier is not None:
        if not isinstance(payload, str):
            raise ValueError("Slack verified claim extraction requires a bearer token")
        return dict(verifier.decode(payload, audience=_AUTH_AUDIENCE)._claims)

    warnings.warn(
        "Slack claim extraction without JwtVerifier is for tests and fixtures only",
        RuntimeWarning,
        stacklevel=2,
    )
    if isinstance(payload, str):
        claims = _fallback_claims(user_id="unverified-slack-token", team_id="unverified")
    else:
        claims = payload
    return {str(key): str(value) for key, value in claims.items()}


def parse_event(
    envelope: Mapping[str, Any],
    *,
    claims: Mapping[str, Any] | str | None = None,
    authorization_header: str | None = None,
    verifier: JwtVerifier | None = None,
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
    claim_payload = claims or bearer_token or _fallback_claims(user_id=user_id, team_id=team_id)
    auth_claims = extract_claims(claim_payload, verifier=verifier)
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


def _decode_unverified_jwt_payload_for_testing(token: str) -> Mapping[str, Any]:
    try:
        _header, payload, _signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Slack token must be a compact JWT") from exc
    padded = payload + "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(decoded.decode("utf-8"))


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


def _fallback_claims(*, user_id: str, team_id: str) -> dict[str, str]:
    return {
        "aud": "verdaca-channel-adapter",
        "exp": "0",
        "iat": "0",
        "iss": f"slack:{team_id}",
        "sub": user_id,
    }
