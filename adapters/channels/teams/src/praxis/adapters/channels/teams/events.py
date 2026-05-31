"""Teams event parsing."""

from __future__ import annotations

import uuid
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


class BearerRequiredError(ValueError):
    """Raised when parse_activity / parse_event receives no bearer token
    (payload is None). Typed so _dispatch catches ONLY this case and not
    all ValueError. The dict-claims branch (IdP-claim coercion, D2
    cross-window contract test_M_T_AUTH_E1_CONSUMES_E2_IDP_FIXTURE_01)
    is intentionally preserved: it is unreachable from the live transport
    (webhook_app._dispatch never passes claims=; always uses
    authorization_header). F-13-V3-PARSE-ACTIVITY-CLAIMS-DICT-BYPASS-01
    merge-gate: this types the exception to close the _dispatch over-broad
    catch; full dict-path removal is a separate scoped decision if desired.
    """


@dataclass(frozen=True, slots=True)
class TeamsEvent:
    intent: StartAnalysisRequest
    ctx: ChannelContext
    callback_url: str | None = None


def parse_activity(
    activity: Mapping[str, Any],
    *,
    claims: Mapping[str, Any] | str | None = None,
    authorization_header: str | None = None,
    verifier: JwtVerifier,
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
    claim_payload = claims or bearer_token
    auth_claims = _resolve_claims(claim_payload, verifier=verifier)
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


def _resolve_claims(
    payload: Mapping[str, Any] | str | None,
    *,
    verifier: JwtVerifier,
) -> dict[str, str]:
    if payload is None:
        raise BearerRequiredError("Teams auth claims or bearer token are required")
    if isinstance(payload, str):
        if verifier is None:
            raise ValueError("Teams bearer token requires a JwtVerifier")
        # Stage 14 V3.A (Option β): production str-bearer path no longer
        # decodes at channel layer. Raw bearer is stored in
        # ctx.rate_limit_token; full verification (kid-aware JwksCache + audience
        # + signature) happens at kernel _auth_first via OidcPolicy.authenticate.
        # The verifier param is required at signature level (H-2 invariant
        # preserved) but unused on this path. ctx.auth_claims remains empty
        # for production bearer flow; production tokens MUST include nonce/jti
        # claim — standard IdP practice (Entra/Okta/Auth0 issue jti by default).
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_str(value: object) -> str | None:
    return str(value) if value else None


def _extract_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("Bearer ").strip() or None
