from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.adapters.channels.teams.adapter import TeamsAdapter
from praxis.adapters.channels.teams.events import parse_activity
from praxis.adapters.channels.teams.manifest import BOT_ID_ENV, SCOPES, SUPPORTS_FILES, manifest_template
from praxis.ports.gateway import ChannelAdapterPort
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef, SessionHandle


class StubGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    def execute(self, intent, ctx) -> AnalysisResult:  # noqa: ANN001
        self.calls.append((intent, ctx))
        return _result()


def _result() -> AnalysisResult:
    return AnalysisResult(
        session=SessionHandle(session_id="session-1", status="complete", source_uri="teams://thread"),
        recommendation="Proceed with the lower-risk path.",
        cited_tradeoffs=("Lower latency", "Higher audit cost"),
        dissent_frames=("Budget pressure remains",),
        artifacts=(
            ArtifactRef(
                artifact_id="artifact-1",
                session_id="session-1",
                kind="memo",
                uri="artifact://session-1/artifact-1",
                title="Decision memo",
            ),
        ),
        cost_usd=Decimal("0.42"),
    )


def _event():
    activity = {
        "id": "teams-activity-1",
        "type": "message",
        "text": "Which option should we choose?",
        "from": {"aadObjectId": "user-1"},
        "conversation": {"id": "conversation-1"},
        "channelData": {"tenant": {"id": "tenant-1"}},
        "serviceUrl": "https://smba.example.invalid/apis/",
    }
    event = parse_activity(activity)
    assert event is not None
    return event


@pytest.mark.no_waiver
def test_M_T_TEAMS_CHANNEL_ADAPTER_PORT_CONTRACT_01_matches_frozen_port() -> None:
    adapter = TeamsAdapter()

    assert isinstance(adapter, ChannelAdapterPort)


def test_M_T_TEAMS_GATEWAY_ROUNDTRIP_01_delegates_to_gateway() -> None:
    event = _event()
    gateway = StubGateway()
    adapter = TeamsAdapter()

    result = adapter.execute(event.intent, event.ctx, gateway)

    assert result.session.status == "complete"
    assert gateway.calls == [(event.intent, event.ctx)]


def test_M_T_TEAMS_RESPONSE_SHAPE_01_returns_frozen_result_dto_and_card_payload() -> None:
    adapter = TeamsAdapter()
    result = _result()

    card = adapter.result_to_adaptive_card(result)

    assert isinstance(result, AnalysisResult)
    assert card["type"] == "AdaptiveCard"
    assert card["body"][0]["text"] == result.recommendation
    assert card["body"][1]["facts"][0] == {"title": "Session", "value": "session-1"}


def test_M_T_TEAMS_MANIFEST_REQUIRED_FIELDS_01_manifest_has_required_bot_fields() -> None:
    manifest = manifest_template(bot_id="bot-stage12")
    bot = manifest["bots"][0]

    assert BOT_ID_ENV == "TEAMS_BOT_ID"
    assert bot["botId"] == "bot-stage12"
    assert tuple(bot["scopes"]) == SCOPES
    assert bot["supportsFiles"] is SUPPORTS_FILES is False
