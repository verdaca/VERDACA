"""Stage 11 H#1.5 gateway adapter stub."""

from __future__ import annotations

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class GatewayStubAdapter(GatewayPort):
    """Importable DI placeholder until kernel/gateway service lands."""

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        raise NotImplementedError("GatewayStubAdapter is a Stage 11 H#1.5 placeholder")


__all__ = ["GatewayStubAdapter"]
