from __future__ import annotations

import base64
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from praxis.ports.gateway_dto import (
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)


@dataclass(frozen=True, slots=True)
class TeamsEvent:
    intent: StartAnalysisRequest
    ctx: ChannelContext
    callback_url: str | None = None


def extract_claims(token_or_claims: Mapping[str, Any] | str) -> dict[str, str]:
    if isinstance(token_or_claims, str):
        claims = _decode_unverified_jwt_payload(token_or_claims)
    else:
        claims = token_or_claims
    return {str(key): str(value) for key, value in claims.items()}


def parse_activity(
    activity: Mapping[str, Any],
    *,
    claims: Mapping[str, Any] | str | None = None,
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

    auth_claims = extract_claims(
        claims or _fallback_claims(caller_id=caller_id, tenant_id=tenant_id)
    )
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
    )
    return TeamsEvent(
        intent=intent,
        ctx=ctx,
        callback_url=str(activity.get("serviceUrl") or "") or None,
    )


def _decode_unverified_jwt_payload(token: str) -> Mapping[str, Any]:
    try:
        _header, payload, _signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Teams token must be a compact JWT") from exc
    padded = payload + "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(decoded.decode("utf-8"))


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _fallback_claims(*, caller_id: str, tenant_id: str) -> dict[str, str]:
    return {
        "aud": "verdaca-channel-adapter",
        "exp": "0",
        "iat": "0",
        "iss": f"teams:{tenant_id}",
        "sub": caller_id,
    }
