"""Stage 11 E2 MCP tool contracts."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.adapters.mcp_server.tools import (
    TOOL_DESCRIPTIONS,
    analysis_result_to_payload,
    build_channel_context,
    build_start_analysis_request,
)
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef, ChannelKind, SessionHandle

EXPECTED_TOOL_DESCRIPTIONS = {
    "verdaca_start_analysis": (
        "Get a defensible recommendation with cited tradeoffs for a strategic decision question."
    ),
    "verdaca_estimate_cost": "Estimate cost and depth before running a deliberation.",
    "verdaca_get_result": "Retrieve the final recommendation and dissent frames for a session.",
    "verdaca_list_sessions": "Browse prior decisions and their cited tradeoffs.",
    "verdaca_get_artifact": "Fetch a specific artifact produced by a session.",
}


def test_M_T_MCP_TOOLS_BUYER_LANGUAGE_01_descriptions_are_ratified() -> None:
    assert dict(TOOL_DESCRIPTIONS) == EXPECTED_TOOL_DESCRIPTIONS


def test_M_T_MCP_TOOLS_BUYER_LANGUAGE_01_tools_file_avoids_forbidden_phrase() -> None:
    tools_path = (
        Path(__file__).resolve().parents[5]
        / "adapters/mcp_server/src/praxis/adapters/mcp_server/tools.py"
    )

    assert "strategic analysis" not in tools_path.read_text(encoding="utf-8")


def test_M_T_MCP_TOOLS_BUYER_LANGUAGE_01_fastmcp_server_lists_five_tools() -> None:
    server = create_verdaca_mcp_server()
    tool_names = {tool.name for tool in server._tool_manager.list_tools()}  # noqa: SLF001

    assert tool_names == set(EXPECTED_TOOL_DESCRIPTIONS)


def test_M_T_MCP_TOOLS_START_ANALYSIS_01_maps_request_to_gateway_dto() -> None:
    request = build_start_analysis_request(
        question="Should we enter the regulated industrial AI market?",
        requester_user_id="user-123",
        workspace_id="workspace-abc",
        idempotency_key="idem-001",
        depth="deep",
        metadata={"source": "claude_desktop"},
    )
    ctx = build_channel_context(
        requester_user_id="user-123",
        request_id="req-001",
        channel_session_id="chan-001",
    )

    assert request.question == "Should we enter the regulated industrial AI market?"
    assert request.requester_user_id == "user-123"
    assert request.workspace_id == "workspace-abc"
    assert request.idempotency_key == "idem-001"
    assert request.depth == "deep"
    assert request.metadata == {"source": "claude_desktop"}
    assert ctx.channel is ChannelKind.CLAUDE_DESKTOP
    assert ctx.caller_id == "user-123"


def test_M_T_MCP_TOOLS_START_ANALYSIS_01_serializes_gateway_result() -> None:
    result = AnalysisResult(
        session=SessionHandle(
            session_id="sess-001",
            status="complete",
            source_uri="verdaca://sessions/sess-001",
        ),
        recommendation="Proceed with a bounded pilot.",
        cited_tradeoffs=("speed vs governance",),
        dissent_frames=("Regulatory approval may dominate timeline.",),
        artifacts=(
            ArtifactRef(
                artifact_id="artifact-001",
                session_id="sess-001",
                kind="brief",
                uri="verdaca://sessions/sess-001/artifacts/artifact-001",
                title="Decision Brief",
            ),
        ),
        cost_usd=Decimal("0.42"),
    )

    assert analysis_result_to_payload(result) == {
        "session": {
            "session_id": "sess-001",
            "status": "complete",
            "source_uri": "verdaca://sessions/sess-001",
        },
        "recommendation": "Proceed with a bounded pilot.",
        "cited_tradeoffs": ["speed vs governance"],
        "dissent_frames": ["Regulatory approval may dominate timeline."],
        "artifacts": [
            {
                "artifact_id": "artifact-001",
                "session_id": "sess-001",
                "kind": "brief",
                "uri": "verdaca://sessions/sess-001/artifacts/artifact-001",
                "title": "Decision Brief",
            }
        ],
        "cost_usd": "0.42",
    }
