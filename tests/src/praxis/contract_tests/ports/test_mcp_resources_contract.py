"""Stage 11 E2 MCP resource contracts."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from praxis.adapters.mcp_server.resources import (
    RESOURCE_URIS,
    artifact_payload,
    methodology_payload,
    session_summary_payload,
    session_transcript_payload,
    templates_payload,
)
from praxis.ports.gateway_dto import (
    AnalysisResult,
    ArtifactRef,
    ChannelContext,
    StartAnalysisRequest,
)


class _ReadGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        raise AssertionError("resources must not execute a new gateway request")

    def get_session_summary(self, session_id: str) -> str:
        self.calls.append(("summary", (session_id,)))
        return f"{session_id}: Recommendation with cited tradeoffs."

    def get_session_transcript(self, session_id: str) -> str:
        self.calls.append(("transcript", (session_id,)))
        return f"{session_id}: frame-1\nframe-2"

    def get_artifact(self, session_id: str, artifact_id: str) -> ArtifactRef:
        self.calls.append(("artifact", (session_id, artifact_id)))
        return ArtifactRef(
            session_id=session_id,
            artifact_id=artifact_id,
            kind="brief",
            uri=f"verdaca://sessions/{session_id}/artifacts/{artifact_id}",
            title="Decision brief",
        )


def test_M_T_MCP_RESOURCES_RESULT_SUMMARY_01_static_resources_are_registered() -> None:
    assert RESOURCE_URIS == (
        "verdaca://methodology",
        "verdaca://templates",
        "verdaca://sessions/{session_id}/result/summary",
        "verdaca://sessions/{session_id}/result/transcript",
        "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
    )
    assert "steps" in methodology_payload()
    assert "decision_brief" in templates_payload()


def test_M_T_MCP_RESOURCES_RESULT_SUMMARY_01_uses_cheap_summary_path() -> None:
    gateway = _ReadGateway()

    payload = session_summary_payload(gateway, "sess-001")

    assert payload == "sess-001: Recommendation with cited tradeoffs."
    assert gateway.calls == [("summary", ("sess-001",))]


@pytest.mark.parametrize(
    "session_id",
    ["../../../etc/passwd", "x" * 200, "id with spaces", "", "abc/123", "abc\x00def"],
)
def test_M_T_MCP_RESOURCES_VALIDATE_SESSION_ID_01_rejects_invalid_session_ids(
    session_id: str,
) -> None:
    gateway = _ReadGateway()

    with pytest.raises(ToolError, match="Invalid session_id"):
        session_summary_payload(gateway, session_id)
    with pytest.raises(ToolError, match="Invalid session_id"):
        session_transcript_payload(gateway, session_id)
    with pytest.raises(ToolError, match="Invalid session_id"):
        artifact_payload(gateway, session_id, "artifact-001")

    assert gateway.calls == []


@pytest.mark.parametrize(
    "artifact_id",
    ["../../../etc/passwd", "x" * 200, "id with spaces", "", "abc/123", "abc\x00def"],
)
def test_M_T_MCP_RESOURCES_VALIDATE_ARTIFACT_ID_01_rejects_invalid_artifact_ids(
    artifact_id: str,
) -> None:
    gateway = _ReadGateway()

    with pytest.raises(ToolError, match="Invalid artifact_id"):
        artifact_payload(gateway, "sess-001", artifact_id)

    assert gateway.calls == []


@pytest.mark.parametrize(
    "session_id",
    ["abc123", "session-1", "550e8400-e29b-41d4-a716-446655440000"],
)
def test_M_T_MCP_RESOURCES_VALIDATE_SESSION_ID_01_accepts_valid_session_ids(
    session_id: str,
) -> None:
    gateway = _ReadGateway()

    payload = session_summary_payload(gateway, session_id)

    assert payload == f"{session_id}: Recommendation with cited tradeoffs."
    assert gateway.calls == [("summary", (session_id,))]


@pytest.mark.parametrize(
    "artifact_id",
    ["abc123", "artifact-1", "550e8400-e29b-41d4-a716-446655440000"],
)
def test_M_T_MCP_RESOURCES_VALIDATE_ARTIFACT_ID_01_accepts_valid_artifact_ids(
    artifact_id: str,
) -> None:
    gateway = _ReadGateway()

    payload = artifact_payload(gateway, "sess-001", artifact_id)

    assert payload.artifact_id == artifact_id
    assert gateway.calls == [("artifact", ("sess-001", artifact_id))]


def test_M_T_MCP_RESOURCES_RESULT_TRANSCRIPT_01_uses_full_path() -> None:
    gateway = _ReadGateway()

    payload = session_transcript_payload(gateway, "sess-001")

    assert payload == "sess-001: frame-1\nframe-2"
    assert gateway.calls == [("transcript", ("sess-001",))]


def test_M_T_MCP_RESOURCES_ARTIFACT_01_resolves_through_gateway_binding() -> None:
    gateway = _ReadGateway()

    payload = artifact_payload(gateway, "sess-001", "artifact-001")

    assert payload == ArtifactRef(
        session_id="sess-001",
        artifact_id="artifact-001",
        kind="brief",
        uri="verdaca://sessions/sess-001/artifacts/artifact-001",
        title="Decision brief",
    )
    assert gateway.calls == [("artifact", ("sess-001", "artifact-001"))]
