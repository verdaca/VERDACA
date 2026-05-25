"""Stage 11 H#1.5 GatewayPort frozen-surface contract shell."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

from praxis.ports.gateway import ChannelAdapterPort, GatewayPort
from praxis.ports.gateway_dto import (
    FROZEN_FIELD_ALLOWLIST,
    AnalysisResult,
    ArtifactRef,
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    SessionHandle,
    StartAnalysisRequest,
)
from praxis.ports.gateway_errors import AuthClaimsAccessError, GatewayCtxError


def test_M_T_GW_PORT_HANDSHAKE_01_imports_resolve() -> None:
    assert GatewayPort.API_VERSION == "1.0.0"
    assert ChannelAdapterPort.API_VERSION == "1.0.0"
    assert AuthClaimsAccessError is not None
    assert GatewayCtxError is not None
    assert CallerKind.HUMAN.value == "human"
    assert {member.value for member in ChannelKind} == {
        "cli",
        "teams",
        "slack",
        "claude_desktop",
        "web",
    }
    assert StartAnalysisRequest is not None
    assert AnalysisResult is not None
    assert SessionHandle is not None
    assert ArtifactRef is not None
    assert AuthClaims is not None
    assert callable(GatewayPort.get_session_summary)
    assert callable(GatewayPort.get_session_transcript)
    assert callable(GatewayPort.get_artifact)


def test_M_T_GW_PORT_HANDSHAKE_01_channel_context_field_allowlist() -> None:
    actual = frozenset(f.name for f in dataclasses.fields(ChannelContext))

    assert actual == FROZEN_FIELD_ALLOWLIST, (
        f"ChannelContext drift: added={actual - FROZEN_FIELD_ALLOWLIST}, "
        f"removed={FROZEN_FIELD_ALLOWLIST - actual}"
    )


def test_M_T_GW_CHANNELCTX_ALLOWLIST_DRIFT_01_runtime_asdict_keys() -> None:
    ctx = ChannelContext(
        caller_id="user-1",
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims={"sub": "user-1"}),
        channel=ChannelKind.CLI,
        channel_session_id="cli-session-1",
        request_id="req-1",
        trace_id="trace-1",
        budget_remaining_usd=Decimal("1.00"),
        rate_limit_token="token-1",
    )

    assert frozenset(dataclasses.asdict(ctx).keys()) == FROZEN_FIELD_ALLOWLIST
