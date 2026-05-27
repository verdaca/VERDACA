from __future__ import annotations

import json
from pathlib import Path

from praxis.adapters.channels.slack.events import extract_claims, parse_event
from praxis.ports.gateway_dto import ChannelKind


FIXTURES_DIR = Path(__file__).parents[5] / "fixtures" / "auth_claims"


def _claims() -> dict[str, object]:
    return json.loads((FIXTURES_DIR / "okta_basic.json").read_text(encoding="utf-8"))


def _envelope(event_type: str = "app_mention") -> dict[str, object]:
    return {
        "type": "event_callback",
        "team_id": "T123STAGE12",
        "response_url": "https://hooks.slack.example.invalid/actions",
        "event": {
            "type": event_type,
            "user": "U123STAGE12",
            "channel": "C123STAGE12",
            "text": "<@BOT> compare the options",
            "ts": "1770000000.000100",
            "thread_ts": "1770000000.000099",
            "event_ts": "1770000000.000100",
        },
    }


def test_M_T_SLACK_EVENT_DISPATCH_APP_MENTION_01_app_mention_maps_to_request() -> None:
    event = parse_event(_envelope(), claims=_claims())

    assert event is not None
    assert event.intent.question == "<@BOT> compare the options"
    assert event.intent.requester_user_id == "U123STAGE12"
    assert event.intent.workspace_id == "T123STAGE12"
    assert event.intent.idempotency_key == "1770000000.000100"


def test_M_T_SLACK_EVENT_DISPATCH_UNKNOWN_01_unknown_event_is_noop() -> None:
    assert parse_event(_envelope("message"), claims=_claims()) is None


def test_M_T_SLACK_CHANNEL_CONTEXT_FIELDS_01_context_has_channel_user_workspace() -> None:
    event = parse_event(_envelope(), claims=_claims())

    assert event is not None
    assert event.ctx.channel is ChannelKind.SLACK
    assert event.ctx.caller_id == "U123STAGE12"
    assert event.ctx.channel_session_id == "1770000000.000099"
    assert event.intent.metadata is not None
    assert event.intent.metadata["channel_id"] == "C123STAGE12"
    assert event.intent.metadata["team_id"] == "T123STAGE12"


def test_M_T_SLACK_AUTH_CLAIMS_EXTRACT_01_extracts_claims_as_strings() -> None:
    claims = extract_claims(_claims())

    assert claims["iss"].startswith("https://dev-12345678.okta")
    assert claims["sub"] == "00u123stage12fixture"
    assert claims["exp"] == "1790784000"
    assert all(isinstance(key, str) and isinstance(value, str) for key, value in claims.items())
