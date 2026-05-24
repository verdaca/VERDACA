"""Stage 11 H#1.5 GatewayPort frozen-surface contract shell."""

from __future__ import annotations

import dataclasses

import pytest

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

pytestmark = pytest.mark.skip(reason="Stage 11 Phase A gateway impl lands at section 4.3")


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


def test_M_T_GW_PORT_HANDSHAKE_01_channel_context_field_allowlist() -> None:
    actual = frozenset(f.name for f in dataclasses.fields(ChannelContext))

    assert actual == FROZEN_FIELD_ALLOWLIST, (
        f"ChannelContext drift: added={actual - FROZEN_FIELD_ALLOWLIST}, "
        f"removed={FROZEN_FIELD_ALLOWLIST - actual}"
    )
