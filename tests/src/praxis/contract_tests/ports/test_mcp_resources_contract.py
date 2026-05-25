"""Stage 11 E2 MCP resource contracts."""

from __future__ import annotations

import pytest

from praxis.adapters.mcp_server.resources import (
    RESOURCE_URIS,
    GatewayReadApiGapError,
    artifact_payload,
    methodology_payload,
    session_summary_payload,
    session_transcript_payload,
    templates_payload,
)
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class _ReadGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        raise AssertionError("resources must not execute a new gateway request")

    def get_session_summary(self, session_id: str) -> dict[str, object]:
        self.calls.append(("summary", (session_id,)))
        return {
            "session_id": session_id,
            "kind": "summary",
            "synopsis": "Recommendation with cited tradeoffs.",
        }

    def get_session_transcript(self, session_id: str) -> dict[str, object]:
        self.calls.append(("transcript", (session_id,)))
        return {
            "session_id": session_id,
            "kind": "transcript",
            "transcript": ["frame-1", "frame-2"],
        }

    def get_artifact(self, session_id: str, artifact_id: str) -> dict[str, object]:
        self.calls.append(("artifact", (session_id, artifact_id)))
        return {
            "session_id": session_id,
            "artifact_id": artifact_id,
            "kind": "brief",
            "uri": f"verdaca://sessions/{session_id}/artifacts/{artifact_id}",
        }


class _ExecuteOnlyGateway:
    def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        raise AssertionError("not used")


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

    assert payload["session_id"] == "sess-001"
    assert payload["kind"] == "summary"
    assert "synopsis" in payload
    assert gateway.calls == [("summary", ("sess-001",))]


def test_M_T_MCP_RESOURCES_RESULT_SUMMARY_01_transcript_uses_full_path() -> None:
    gateway = _ReadGateway()

    payload = session_transcript_payload(gateway, "sess-001")

    assert payload["session_id"] == "sess-001"
    assert payload["kind"] == "transcript"
    assert "transcript" in payload
    assert gateway.calls == [("transcript", ("sess-001",))]


def test_M_T_MCP_RESOURCES_ARTIFACT_01_resolves_through_gateway_binding() -> None:
    gateway = _ReadGateway()

    payload = artifact_payload(gateway, "sess-001", "artifact-001")

    assert payload["session_id"] == "sess-001"
    assert payload["artifact_id"] == "artifact-001"
    assert payload["uri"] == "verdaca://sessions/sess-001/artifacts/artifact-001"
    assert gateway.calls == [("artifact", ("sess-001", "artifact-001"))]


def test_M_T_MCP_RESOURCES_ARTIFACT_01_surfaces_gateway_read_api_gap() -> None:
    with pytest.raises(GatewayReadApiGapError, match="GatewayPort has no resource read API"):
        session_summary_payload(_ExecuteOnlyGateway(), "sess-001")
