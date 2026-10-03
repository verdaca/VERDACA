"""Stage 11 E2 MCP tool contracts."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Any

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.adapters.mcp_server.tools import (
    TOOL_DESCRIPTIONS,
    analysis_result_to_payload,
    build_channel_context,
    build_start_analysis_request,
)
from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    ChannelContext,
    ChannelKind,
    SessionHandle,
    StartAnalysisRequest,
)

EXPECTED_TOOL_DESCRIPTIONS = {
    "verdaca_start_analysis": (
        "Get a defensible recommendation with cited tradeoffs for a strategic decision question."
    ),
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

EXPECTED_TOOL_TITLES = {
    "verdaca_start_analysis": "Start Recommendation",
    "verdaca_estimate_cost": "Estimate Cost",
    "verdaca_get_result": "Get Recommendation",
    "verdaca_list_sessions": "List Sessions",
    "verdaca_get_artifact": "Get Document",
}


class _RecordingGateway:
    def __init__(self) -> None:
        self.intent: StartAnalysisRequest | None = None
        self.ctx: ChannelContext | None = None
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        self.intent = intent
        self.ctx = ctx
        return AnalysisResult(
            session=SessionHandle(
                session_id="sess-001",
                status="complete",
                source_uri="verdaca://sessions/sess-001",
            ),
            recommendation="Proceed with a bounded pilot.",
            cited_tradeoffs=("speed vs governance",),
        )

    def get_session_summary(self, session_id: str) -> str:
        self.calls.append(("summary", (session_id,)))
        return f"{session_id}: short recommendation."

    def get_session_transcript(self, session_id: str) -> str:
        self.calls.append(("transcript", (session_id,)))
        return f"{session_id}: recommendation plus dissenting positions."

    def get_artifact(self, session_id: str, artifact_id: str) -> ArtifactRef:
        self.calls.append(("artifact", (session_id, artifact_id)))
        return ArtifactRef(
            artifact_id=artifact_id,
            session_id=session_id,
            kind="memo",
            uri=f"verdaca://sessions/{session_id}/artifacts/{artifact_id}",
            title="Decision memo",
        )

    def list_sessions(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 50,
    ) -> list[SessionHandle]:
        self.calls.append(("list_sessions", (workspace_id, limit)))
        return [
            SessionHandle(
                session_id="sess-001",
                status="complete",
                source_uri="verdaca://sessions/sess-001",
            )
        ]


def test_M_T_MCP_TOOLS_BUYER_LANGUAGE_01_descriptions_are_ratified() -> None:
    assert dict(TOOL_DESCRIPTIONS) == EXPECTED_TOOL_DESCRIPTIONS


def test_M_T_MCP_TOOLS_BUYER_LANGUAGE_MARY_H7_01_descriptions_and_titles_are_ratified() -> None:
    server = create_verdaca_mcp_server()
    tools = {tool.name: tool for tool in server._tool_manager.list_tools()}  # noqa: SLF001

    assert dict(TOOL_DESCRIPTIONS) == EXPECTED_TOOL_DESCRIPTIONS
    assert {name: tool.title for name, tool in tools.items()} == EXPECTED_TOOL_TITLES


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


def test_verdaca_strategy_question_prompt_is_registered() -> None:
    server = create_verdaca_mcp_server()
    prompt_names = {prompt.name for prompt in server._prompt_manager.list_prompts()}  # noqa: SLF001

    assert "verdaca-strategy-question" in prompt_names


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


def test_M_T_MCP_TOOLS_START_ANALYSIS_01_tool_delegates_to_gateway() -> None:
    gateway = _RecordingGateway()
    server = create_verdaca_mcp_server(gateway=gateway)
    tool = server._tool_manager.get_tool("verdaca_start_analysis")  # noqa: SLF001
    assert tool is not None

    payload = asyncio.run(
        tool.run(
            {
                "question": "Should we launch the regulated market pilot?",
                "requester_user_id": "user-123",
                "workspace_id": "workspace-abc",
                "idempotency_key": "idem-001",
                "channel_session_id": "chan-001",
                "request_id": "req-001",
                "depth": "standard",
                "metadata": {"source": "test"},
            }
        )
    )

    assert isinstance(payload, dict)
    typed_payload: dict[str, Any] = payload
    assert typed_payload["session"]["session_id"] == "sess-001"
    assert gateway.intent is not None
    assert gateway.intent.question == "Should we launch the regulated market pilot?"
    assert gateway.intent.metadata == {"source": "test"}
    assert gateway.ctx is not None
    assert gateway.ctx.channel is ChannelKind.CLAUDE_DESKTOP


def test_M_T_MCP_TOOLS_GET_RESULT_01_tool_delegates_to_gateway_transcript() -> None:
    gateway = _RecordingGateway()
    server = create_verdaca_mcp_server(gateway=gateway)
    tool = server._tool_manager.get_tool("verdaca_get_result")  # noqa: SLF001
    assert tool is not None

    payload = asyncio.run(tool.run({"session_id": "sess-001"}))

    assert isinstance(payload, dict)
    typed_payload: dict[str, Any] = payload
    assert typed_payload == {
        "session_id": "sess-001",
        "transcript": "sess-001: recommendation plus dissenting positions.",
    }
    assert gateway.calls == [("transcript", ("sess-001",))]


def test_M_T_MCP_TOOLS_LIST_SESSIONS_01_tool_delegates_to_gateway() -> None:
    gateway = _RecordingGateway()
    server = create_verdaca_mcp_server(gateway=gateway)
    tool = server._tool_manager.get_tool("verdaca_list_sessions")  # noqa: SLF001
    assert tool is not None

    payload = asyncio.run(tool.run({"workspace_id": "workspace-abc"}))

    assert isinstance(payload, dict)
    typed_payload: dict[str, Any] = payload
    assert typed_payload == {
        "sessions": [
            {
                "session_id": "sess-001",
                "status": "complete",
                "source_uri": "verdaca://sessions/sess-001",
            }
        ]
    }
    assert gateway.calls == [("list_sessions", ("workspace-abc", 50))]


def test_M_T_MCP_TOOLS_GET_ARTIFACT_01_tool_delegates_to_gateway() -> None:
    gateway = _RecordingGateway()
    server = create_verdaca_mcp_server(gateway=gateway)
    tool = server._tool_manager.get_tool("verdaca_get_artifact")  # noqa: SLF001
    assert tool is not None

    payload = asyncio.run(
        tool.run({"session_id": "sess-001", "artifact_id": "artifact-001"})
    )

    assert isinstance(payload, dict)
    typed_payload: dict[str, Any] = payload
    assert typed_payload == {
        "artifact_id": "artifact-001",
        "session_id": "sess-001",
        "kind": "memo",
        "uri": "verdaca://sessions/sess-001/artifacts/artifact-001",
        "title": "Decision memo",
    }
    assert gateway.calls == [("artifact", ("sess-001", "artifact-001"))]
