from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, Protocol, runtime_checkable

from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    ChannelContext,
    SessionHandle,
    StartAnalysisRequest,
)


@runtime_checkable
class GatewayPort(Protocol):
    """Channel-neutral execution surface for Verdaca analysis requests."""

    API_VERSION: ClassVar[str] = "1.0.0"

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        """Execute one gateway request."""

    def get_session_summary(self, session_id: str) -> str:
        """Return a compact synopsis for a persisted session."""

    def get_session_transcript(self, session_id: str) -> str:
        """Return the full transcript payload for a persisted session."""

    def get_artifact(self, session_id: str, artifact_id: str) -> ArtifactRef:
        """Return a gateway-visible artifact reference."""

    def list_sessions(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 50,
    ) -> Sequence[SessionHandle]:
        """Return persisted session handles for gateway resources and tools."""


@runtime_checkable
class ChannelAdapterPort(Protocol):
    """Thin channel wrapper that delegates execution to a GatewayPort."""

    API_VERSION: ClassVar[str] = "1.0.0"

    def execute(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        gateway: GatewayPort,
    ) -> AnalysisResult:
        """Translate a channel request into a GatewayPort execution."""


__all__ = [
    "API_VERSION",
    "ChannelAdapterPort",
    "GatewayPort",
]

API_VERSION: str = GatewayPort.API_VERSION
