from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.adapters.channels.slack.adapter import SlackAdapter
from praxis.adapters.channels.slack.events import parse_event
from praxis.adapters.channels.slack.manifest import BOT_EVENTS, SCOPES, manifest_template
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
        session=SessionHandle(session_id="session-1", status="complete", source_uri="slack://thread"),
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
    envelope = {
        "type": "event_callback",
        "team_id": "T123STAGE12",
        "event": {
            "type": "app_mention",
            "user": "U123STAGE12",
            "channel": "C123STAGE12",
            "text": "<@BOT> compare the options",
            "ts": "1770000000.000100",
        },
    }
    event = parse_event(
        envelope,
        claims={
            "aud": "api://verdaca",
            "exp": "1790784000",
            "iat": "1767225600",
            "iss": "https://issuer.example.invalid",
            "sub": "user-1",
        },
        verifier=object(),
    )
    assert event is not None
    return event


@pytest.mark.no_waiver
def test_M_T_SLACK_CHANNEL_ADAPTER_PORT_CONTRACT_01_matches_frozen_port() -> None:
    adapter = SlackAdapter()

    assert isinstance(adapter, ChannelAdapterPort)


def test_M_T_SLACK_GATEWAY_ROUNDTRIP_01_delegates_to_gateway() -> None:
    event = _event()
    gateway = StubGateway()
    adapter = SlackAdapter()

    result = adapter.execute(event.intent, event.ctx, gateway)

    assert result.session.status == "complete"
    assert gateway.calls == [(event.intent, event.ctx)]


def test_M_T_SLACK_RESPONSE_SHAPE_01_returns_result_dto_and_block_payload() -> None:
    adapter = SlackAdapter()
    result = _result()

    payload = adapter.result_to_block_kit(result)

    assert isinstance(result, AnalysisResult)
    assert payload["blocks"][0]["type"] == "section"
    assert payload["blocks"][0]["text"]["text"] == result.recommendation
    assert "session-1" in payload["blocks"][1]["elements"][0]["text"]


def test_M_T_SLACK_MANIFEST_REQUIRED_FIELDS_01_manifest_has_events_and_scopes() -> None:
    manifest = manifest_template()

    assert manifest["event_subscriptions"]["bot_events"] == list(BOT_EVENTS)
    assert "app_mention" in manifest["event_subscriptions"]["bot_events"]
    assert manifest["oauth_config"]["scopes"]["bot"] == list(SCOPES)
    assert "chat:write" in manifest["oauth_config"]["scopes"]["bot"]
