"""Verdaca MCP tools."""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping

from mcp.server.fastmcp import FastMCP

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import (
    AnalysisResult,
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)

TOOL_DESCRIPTIONS: Mapping[str, str] = MappingProxyType(
    {
        "verdaca_start_analysis": "Get a defensible recommendation with cited tradeoffs "
        "for a strategic decision question.",
        "verdaca_estimate_cost": "Estimate cost and depth before running a deliberation.",
        "verdaca_get_result": (
            "Retrieve the final recommendation and dissent frames for a session."
        ),
        "verdaca_list_sessions": "Browse prior decisions and their cited tradeoffs.",
        "verdaca_get_artifact": "Fetch a specific artifact produced by a session.",
    }
)


def build_start_analysis_request(
    *,
    question: str,
    requester_user_id: str,
    workspace_id: str,
    idempotency_key: str,
    depth: str = "standard",
    metadata: Mapping[str, str] | None = None,
) -> StartAnalysisRequest:
    """Build the GatewayPort request DTO for the start-analysis tool."""

    return StartAnalysisRequest(
        question=question,
        requester_user_id=requester_user_id,
        workspace_id=workspace_id,
        idempotency_key=idempotency_key,
        depth=depth,
        metadata=dict(metadata) if metadata is not None else None,
    )


def build_channel_context(
    *,
    requester_user_id: str,
    request_id: str,
    channel_session_id: str,
) -> ChannelContext:
    """Build the Stage 11 caller context for Claude Desktop MCP requests."""

    return ChannelContext(
        caller_id=requester_user_id,
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims={"requester_user_id": requester_user_id}),
        channel=ChannelKind.CLAUDE_DESKTOP,
        channel_session_id=channel_session_id,
        request_id=request_id,
    )


def analysis_result_to_payload(result: AnalysisResult) -> dict[str, Any]:
    """Convert a GatewayPort result to a JSON-serializable MCP payload."""

    return {
        "session": {
            "session_id": result.session.session_id,
            "status": result.session.status,
            "source_uri": result.session.source_uri,
        },
        "recommendation": result.recommendation,
        "cited_tradeoffs": list(result.cited_tradeoffs),
        "dissent_frames": list(result.dissent_frames),
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "session_id": artifact.session_id,
                "kind": artifact.kind,
                "uri": artifact.uri,
                "title": artifact.title,
            }
            for artifact in result.artifacts
        ],
        "cost_usd": str(result.cost_usd) if result.cost_usd is not None else None,
    }


def _gateway_required(gateway: GatewayPort | None) -> GatewayPort:
    if gateway is None:
        raise NotImplementedError("GatewayPort binding is provided by E1 integration")
    return gateway


def register_tools(server: FastMCP, *, gateway: GatewayPort | None = None) -> None:
    """Register the five Verdaca tools on a FastMCP server."""

    @server.tool(
        name="verdaca_start_analysis",
        title="Start Recommendation",
        description=TOOL_DESCRIPTIONS["verdaca_start_analysis"],
        structured_output=True,
    )
    def verdaca_start_analysis(
        question: str,
        requester_user_id: str,
        workspace_id: str,
        idempotency_key: str,
        channel_session_id: str,
        request_id: str,
        depth: str = "standard",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request = build_start_analysis_request(
            question=question,
            requester_user_id=requester_user_id,
            workspace_id=workspace_id,
            idempotency_key=idempotency_key,
            depth=depth,
            metadata=metadata,
        )
        ctx = build_channel_context(
            requester_user_id=requester_user_id,
            request_id=request_id,
            channel_session_id=channel_session_id,
        )
        return analysis_result_to_payload(_gateway_required(gateway).execute(request, ctx))

    @server.tool(
        name="verdaca_estimate_cost",
        title="Estimate Cost",
        description=TOOL_DESCRIPTIONS["verdaca_estimate_cost"],
        structured_output=True,
    )
    def verdaca_estimate_cost(question: str, depth: str = "standard") -> dict[str, str]:
        depth_multiplier = {
            "quick": Decimal("0.25"),
            "standard": Decimal("1.00"),
            "deep": Decimal("2.50"),
        }
        multiplier = depth_multiplier.get(depth, depth_multiplier["standard"])
        token_estimate = max(750, len(question.split()) * 85)
        estimated_usd = (Decimal(token_estimate) * Decimal("0.000015") * multiplier).quantize(
            Decimal("0.0001")
        )
        return {
            "depth": depth,
            "estimated_input_tokens": str(token_estimate),
            "estimated_cost_usd": str(estimated_usd),
        }

    @server.tool(
        name="verdaca_get_result",
        title="Get Result",
        description=TOOL_DESCRIPTIONS["verdaca_get_result"],
        structured_output=True,
    )
    def verdaca_get_result(session_id: str) -> dict[str, str]:
        raise NotImplementedError(
            f"Result retrieval for {session_id!r} blocks on E1 GatewayPort resources wiring"
        )

    @server.tool(
        name="verdaca_list_sessions",
        title="List Sessions",
        description=TOOL_DESCRIPTIONS["verdaca_list_sessions"],
        structured_output=True,
    )
    def verdaca_list_sessions(workspace_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            f"Session listing for workspace {workspace_id!r} blocks on E1 "
            "GatewayPort resources wiring"
        )

    @server.tool(
        name="verdaca_get_artifact",
        title="Get Artifact",
        description=TOOL_DESCRIPTIONS["verdaca_get_artifact"],
        structured_output=True,
    )
    def verdaca_get_artifact(session_id: str, artifact_id: str) -> dict[str, str]:
        raise NotImplementedError(
            f"Artifact retrieval for {session_id!r}/{artifact_id!r} blocks on E1 resources wiring"
        )
