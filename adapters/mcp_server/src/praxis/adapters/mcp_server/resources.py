"""Verdaca MCP resources."""

from __future__ import annotations

import json
from typing import Any, Protocol, cast

from mcp.server.fastmcp import FastMCP

from praxis.ports.gateway import GatewayPort

RESOURCE_URIS: tuple[str, ...] = (
    "verdaca://methodology",
    "verdaca://templates",
    "verdaca://sessions/{session_id}/result/summary",
    "verdaca://sessions/{session_id}/result/transcript",
    "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
)

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


class GatewayReadApiGapError(RuntimeError):
    """Raised when the frozen GatewayPort lacks a resource read method."""


class _GatewayResourceReadSurface(Protocol):
    def get_session_summary(self, session_id: str) -> dict[str, Any]: ...

    def get_session_transcript(self, session_id: str) -> dict[str, Any]: ...

    def get_artifact(self, session_id: str, artifact_id: str) -> dict[str, Any]: ...


def methodology_payload() -> dict[str, Any]:
    """Return static Verdaca methodology context."""

    return METHODOLOGY


def templates_payload() -> dict[str, Any]:
    """Return static Verdaca artifact templates."""

    return TEMPLATES


def session_summary_payload(gateway: GatewayPort, session_id: str) -> dict[str, Any]:
    """Return the cheap session summary path via the gateway read surface."""

    return _resource_reader(gateway).get_session_summary(session_id)


def session_transcript_payload(gateway: GatewayPort, session_id: str) -> dict[str, Any]:
    """Return the full transcript path via the gateway read surface."""

    return _resource_reader(gateway).get_session_transcript(session_id)


def artifact_payload(gateway: GatewayPort, session_id: str, artifact_id: str) -> dict[str, Any]:
    """Return an artifact through the gateway read surface."""

    return _resource_reader(gateway).get_artifact(session_id, artifact_id)


def _resource_reader(gateway: GatewayPort) -> _GatewayResourceReadSurface:
    missing = [
        name
        for name in ("get_session_summary", "get_session_transcript", "get_artifact")
        if not hasattr(gateway, name)
    ]
    if missing:
        raise GatewayReadApiGapError(
            "GatewayPort has no resource read API for MCP resources: "
            + ", ".join(sorted(missing))
        )
    return cast(_GatewayResourceReadSurface, gateway)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2)


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
        if gateway is None:
            raise GatewayReadApiGapError("GatewayPort binding is required for session summary")
        return _json_text(session_summary_payload(gateway, session_id))

    @server.resource(
        "verdaca://sessions/{session_id}/result/transcript",
        name="verdaca-session-transcript",
        title="Verdaca Session Transcript",
        description="Full transcript for a completed Verdaca session.",
        mime_type="application/json",
    )
    def verdaca_session_transcript(session_id: str) -> str:
        if gateway is None:
            raise GatewayReadApiGapError("GatewayPort binding is required for session transcript")
        return _json_text(session_transcript_payload(gateway, session_id))

    @server.resource(
        "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
        name="verdaca-session-artifact",
        title="Verdaca Session Artifact",
        description="Artifact produced by a completed Verdaca session.",
        mime_type="application/json",
    )
    def verdaca_session_artifact(session_id: str, artifact_id: str) -> str:
        if gateway is None:
            raise GatewayReadApiGapError("GatewayPort binding is required for artifact lookup")
        return _json_text(artifact_payload(gateway, session_id, artifact_id))
