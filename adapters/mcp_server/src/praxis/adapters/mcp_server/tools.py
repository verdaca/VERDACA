"""Verdaca MCP tools.

Stage 14 Phase-0.5 (Option A bridge): the four gateway-backed tool closures
are ``async def`` and offload the FROZEN sync ``GatewayPort`` calls to a worker
thread via ``anyio.to_thread.run_sync``. FastMCP dispatches sync tool handlers
ON the event-loop thread (``func_metadata.py:95`` — direct call, no offload),
which would make the kernel's ``asyncio.run()`` guard in ``service.py`` (both
``_run_auth_first`` and ``_run_session_index_read``) raise
``RuntimeError("... must be called outside an active event loop")`` on the
first real call. Offloading to a worker thread means there is no running loop
in that thread, so the guard's ``except RuntimeError: asyncio.run(...)`` branch
fires as designed. This is an ADAPTER-LAYER concurrency adjustment only — the
kernel execute path, auth ordering, and ``build_gateway`` signature are
untouched. ``verdaca_estimate_cost`` is pure compute (no gateway) and stays
synchronous.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping

import anyio
from mcp.server.fastmcp import FastMCP

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    SessionHandle,
    StartAnalysisRequest,
)

TOOL_DESCRIPTIONS: Mapping[str, str] = MappingProxyType(
    {
        "verdaca_start_analysis": "Get a defensible recommendation with cited tradeoffs "
        "for a strategic decision question.",
        "verdaca_estimate_cost": (
            "Preview cost and depth before committing to a full recommendation."
        ),
        "verdaca_get_result": (
            "Retrieve the recommendation and the dissenting positions captured during the session."
        ),
        "verdaca_list_sessions": "Browse prior decisions and their cited tradeoffs.",
        "verdaca_get_artifact": (
            "Fetch a specific document or memo produced during a decision session."
        ),
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


def session_handle_to_payload(session: SessionHandle) -> dict[str, str]:
    """Convert a GatewayPort session handle to a JSON-serializable MCP payload."""

    return {
        "session_id": session.session_id,
        "status": session.status,
        "source_uri": session.source_uri,
    }


def artifact_ref_to_payload(artifact: ArtifactRef) -> dict[str, str | None]:
    """Convert a GatewayPort artifact reference to a JSON-serializable MCP payload."""

    return {
        "artifact_id": artifact.artifact_id,
        "session_id": artifact.session_id,
        "kind": artifact.kind,
        "uri": artifact.uri,
        "title": artifact.title,
    }


def session_list_to_payload(sessions: Sequence[SessionHandle]) -> dict[str, Any]:
    """Convert GatewayPort session handles to an MCP list payload."""

    return {"sessions": [session_handle_to_payload(session) for session in sessions]}


def _gateway_required(gateway: GatewayPort | None) -> GatewayPort:
    if gateway is None:
        raise RuntimeError("GatewayPort binding is required for MCP tools")
    return gateway


def register_tools(server: FastMCP, *, gateway: GatewayPort | None = None) -> None:
    """Register the five Verdaca tools on a FastMCP server."""

    @server.tool(
        name="verdaca_start_analysis",
        title="Start Recommendation",
        description=TOOL_DESCRIPTIONS["verdaca_start_analysis"],
        structured_output=True,
    )
    async def verdaca_start_analysis(
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
        bound_gateway = _gateway_required(gateway)
        # Phase-0.5 Option A: offload the FROZEN sync execute() to a worker
        # thread so its asyncio.run() guard fires outside the FastMCP loop.
        result = await anyio.to_thread.run_sync(bound_gateway.execute, request, ctx)
        return analysis_result_to_payload(result)

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
        title="Get Recommendation",
        description=TOOL_DESCRIPTIONS["verdaca_get_result"],
        structured_output=True,
    )
    async def verdaca_get_result(session_id: str) -> dict[str, str]:
        bound_gateway = _gateway_required(gateway)
        # Phase-0.5 Option A: get_session_transcript carries the same frozen
        # asyncio.run() read-guard (service.py:_run_session_index_read).
        transcript = await anyio.to_thread.run_sync(
            bound_gateway.get_session_transcript, session_id
        )
        return {"session_id": session_id, "transcript": transcript}

    @server.tool(
        name="verdaca_list_sessions",
        title="List Sessions",
        description=TOOL_DESCRIPTIONS["verdaca_list_sessions"],
        structured_output=True,
    )
    async def verdaca_list_sessions(workspace_id: str | None = None) -> dict[str, Any]:
        bound_gateway = _gateway_required(gateway)
        # Phase-0.5 Option A: list_sessions carries the same frozen
        # asyncio.run() read-guard (service.py:_run_session_index_read).
        # keyword arg passed via a lambda since to_thread.run_sync is positional.
        sessions = await anyio.to_thread.run_sync(
            lambda: bound_gateway.list_sessions(workspace_id=workspace_id, limit=50)
        )
        return session_list_to_payload(sessions)

    @server.tool(
        name="verdaca_get_artifact",
        title="Get Document",
        description=TOOL_DESCRIPTIONS["verdaca_get_artifact"],
        structured_output=True,
    )
    async def verdaca_get_artifact(session_id: str, artifact_id: str) -> dict[str, str | None]:
        bound_gateway = _gateway_required(gateway)
        # Phase-0.5 Option A: get_artifact carries the same frozen
        # asyncio.run() read-guard (service.py:_run_session_index_read).
        artifact = await anyio.to_thread.run_sync(
            bound_gateway.get_artifact, session_id, artifact_id
        )
        return artifact_ref_to_payload(artifact)
