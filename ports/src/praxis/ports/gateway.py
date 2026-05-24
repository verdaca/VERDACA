from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


@runtime_checkable
class GatewayPort(Protocol):
    """Channel-neutral execution surface for Verdaca analysis requests."""

    API_VERSION: ClassVar[str] = "1.0.0"

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        """Execute one gateway request."""


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
