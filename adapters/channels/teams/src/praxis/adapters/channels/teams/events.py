"""Teams event parsing.

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
class TeamsEvent:
    intent: StartAnalysisRequest
    ctx: ChannelContext
    callback_url: str | None = None


def extract_claims(
    payload: Mapping[str, Any] | str,
    verifier: JwtVerifier | None = None,
) -> dict[str, str]:
    if verifier is not None:
        if not isinstance(payload, str):
            raise ValueError("Teams verified claim extraction requires a bearer token")
        return dict(verifier.decode(payload, audience=_AUTH_AUDIENCE)._claims)

    warnings.warn(
        "Teams claim extraction without JwtVerifier is for tests and fixtures only",
        RuntimeWarning,
        stacklevel=2,
    )
    if isinstance(payload, str):
        claims = _fallback_claims(caller_id="unverified-teams-token", tenant_id="unverified")
    else:
        claims = payload
    return {str(key): str(value) for key, value in claims.items()}


def parse_activity(
    activity: Mapping[str, Any],
    *,
    claims: Mapping[str, Any] | str | None = None,
    authorization_header: str | None = None,
    verifier: JwtVerifier | None = None,
) -> TeamsEvent | None:
    if activity.get("type") != "message":
        return None

    from_user = _as_mapping(activity.get("from"))
    conversation = _as_mapping(activity.get("conversation"))
    channel_data = _as_mapping(activity.get("channelData"))
    tenant = _as_mapping(channel_data.get("tenant"))

    caller_id = str(from_user.get("aadObjectId") or from_user.get("id") or "")
    conversation_id = str(conversation.get("id") or "")
    tenant_id = str(tenant.get("id") or channel_data.get("tenantId") or "")
    activity_id = str(activity.get("id") or uuid.uuid4())
    text = str(activity.get("text") or "").strip()

    bearer_token = _extract_bearer_token(
        authorization_header
        or _optional_str(activity.get("authorization"))
        or _optional_str(activity.get("bearer_token"))
    )
    claim_payload = claims or bearer_token or _fallback_claims(
        caller_id=caller_id,
        tenant_id=tenant_id,
    )
    auth_claims = extract_claims(claim_payload, verifier=verifier)
    intent = StartAnalysisRequest(
        question=text,
        requester_user_id=caller_id,
        workspace_id=tenant_id,
        idempotency_key=activity_id,
        metadata={
            "activity_id": activity_id,
            "channel_id": str(activity.get("channelId") or "msteams"),
            "tenant_id": tenant_id,
            "service_url": str(activity.get("serviceUrl") or ""),
        },
    )
    ctx = ChannelContext(
        caller_id=caller_id,
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims=auth_claims),
        channel=ChannelKind.TEAMS,
        channel_session_id=conversation_id,
        request_id=str(uuid.uuid4()),
        trace_id=activity_id,
        rate_limit_token=bearer_token,
    )
    return TeamsEvent(
        intent=intent,
        ctx=ctx,
        callback_url=str(activity.get("serviceUrl") or "") or None,
    )


def _decode_unverified_jwt_payload_for_testing(token: str) -> Mapping[str, Any]:
    try:
        _header, payload, _signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Teams token must be a compact JWT") from exc
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


def _fallback_claims(*, caller_id: str, tenant_id: str) -> dict[str, str]:
    # exp/iat=0 marks a synthetic testing fallback, not a verified token lifetime.
    return {
        "aud": "verdaca-channel-adapter",
        "exp": "0",
        "iat": "0",
        "iss": f"teams:{tenant_id}",
        "sub": caller_id,
    }
