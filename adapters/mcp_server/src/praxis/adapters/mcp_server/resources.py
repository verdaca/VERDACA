"""Verdaca MCP resources."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import ArtifactRef

RESOURCE_URIS: tuple[str, ...] = (
    "verdaca://methodology",
    "verdaca://templates",
    "verdaca://sessions/{session_id}/result/summary",
    "verdaca://sessions/{session_id}/result/transcript",
    "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
)
_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

METHODOLOGY = {
    "name": "Verdaca decision methodology",
    "steps": [
        "frame the decision question",
        "collect constraints and evidence",
        "produce a recommendation with cited tradeoffs",
        "record dissent frames",
        "persist artifacts for replay",
    ],
}

TEMPLATES = {
    "decision_brief": {
        "sections": [
            "question",
            "recommendation",
            "cited_tradeoffs",
            "dissent_frames",
            "artifacts",
        ]
    },
    "artifact_summary": {
        "sections": ["artifact_id", "kind", "title", "uri"],
    },
}


def methodology_payload() -> dict[str, Any]:
    """Return static Verdaca methodology context."""

    return METHODOLOGY


def templates_payload() -> dict[str, Any]:
    """Return static Verdaca artifact templates."""

    return TEMPLATES


def session_summary_payload(gateway: GatewayPort, session_id: str) -> str:
    """Return the cheap session summary path via GatewayPort."""

    _validate_id("session_id", session_id)
    return gateway.get_session_summary(session_id)


def session_transcript_payload(gateway: GatewayPort, session_id: str) -> str:
    """Return the full transcript path via GatewayPort."""

    _validate_id("session_id", session_id)
    return gateway.get_session_transcript(session_id)


def artifact_payload(gateway: GatewayPort, session_id: str, artifact_id: str) -> ArtifactRef:
    """Return an artifact through GatewayPort."""

    _validate_id("session_id", session_id)
    _validate_id("artifact_id", artifact_id)
    return gateway.get_artifact(session_id, artifact_id)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2)


def _required_gateway(gateway: GatewayPort | None, resource_name: str) -> GatewayPort:
    if gateway is None:
        raise RuntimeError(f"GatewayPort binding is required for {resource_name}")
    return gateway


def _validate_id(field_name: str, value: str) -> None:
    if _ID_PATTERN.fullmatch(value) is None:
        raise ToolError(
            f"Invalid {field_name}: expected 1-128 ASCII letters, digits, underscores, or hyphens"
        )


def register_resources(server: FastMCP, *, gateway: GatewayPort | None = None) -> None:
    """Register Verdaca resources."""

    @server.resource(
        "verdaca://methodology",
        name="verdaca-methodology",
        title="Verdaca Methodology",
        description="Verdaca's decision workflow and replay methodology.",
        mime_type="application/json",
    )
    def verdaca_methodology() -> str:
        return _json_text(methodology_payload())

    @server.resource(
        "verdaca://templates",
        name="verdaca-templates",
        title="Verdaca Templates",
        description="Decision brief and artifact template shapes.",
        mime_type="application/json",
    )
    def verdaca_templates() -> str:
        return _json_text(templates_payload())

    @server.resource(
        "verdaca://sessions/{session_id}/result/summary",
        name="verdaca-session-summary",
        title="Verdaca Session Summary",
        description="Small synopsis for a completed Verdaca session.",
        mime_type="application/json",
    )
    def verdaca_session_summary(session_id: str) -> str:
        bound_gateway = _required_gateway(gateway, "session summary")
        return _json_text(
            {
                "session_id": session_id,
                "summary": session_summary_payload(bound_gateway, session_id),
            }
        )

    @server.resource(
        "verdaca://sessions/{session_id}/result/transcript",
        name="verdaca-session-transcript",
        title="Verdaca Session Transcript",
        description="Full transcript for a completed Verdaca session.",
        mime_type="application/json",
    )
    def verdaca_session_transcript(session_id: str) -> str:
        bound_gateway = _required_gateway(gateway, "session transcript")
        return _json_text(
            {
                "session_id": session_id,
                "transcript": session_transcript_payload(bound_gateway, session_id),
            }
        )

    @server.resource(
        "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
        name="verdaca-session-artifact",
        title="Verdaca Session Artifact",
        description="Artifact produced by a completed Verdaca session.",
        mime_type="application/json",
    )
    def verdaca_session_artifact(session_id: str, artifact_id: str) -> str:
        bound_gateway = _required_gateway(gateway, "artifact lookup")
        artifact = artifact_payload(bound_gateway, session_id, artifact_id)
        return _json_text(asdict(artifact))
