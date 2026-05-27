from __future__ import annotations

import json
from pathlib import Path

from praxis.adapters.channels.teams.events import extract_claims, parse_activity
from praxis.ports.gateway_dto import ChannelKind

FIXTURES_DIR = Path(__file__).parents[5] / "fixtures" / "auth_claims"


def _claims() -> dict[str, object]:
    return json.loads((FIXTURES_DIR / "entra_basic.json").read_text(encoding="utf-8"))


def _activity(activity_type: str = "message") -> dict[str, object]:
    return {
        "id": "teams-activity-1",
        "type": activity_type,
        "text": "Summarize this decision",
        "channelId": "msteams",
        "serviceUrl": "https://smba.example.invalid/apis/",
        "from": {
            "id": "29:user",
            "aadObjectId": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        },
        "conversation": {"id": "19:conversation@example.invalid"},
        "channelData": {
            "tenant": {"id": "11111111-2222-4333-8444-555555555555"},
        },
    }


def test_M_T_TEAMS_EVENT_DISPATCH_MESSAGE_01_message_maps_to_gateway_request() -> None:
    event = parse_activity(_activity(), claims=_claims())

    assert event is not None
    assert event.intent.question == "Summarize this decision"
    assert event.intent.requester_user_id == "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    assert event.intent.workspace_id == "11111111-2222-4333-8444-555555555555"
    assert event.intent.idempotency_key == "teams-activity-1"


def test_M_T_TEAMS_EVENT_DISPATCH_UNKNOWN_01_unknown_activity_is_noop() -> None:
    assert parse_activity(_activity("typing"), claims=_claims()) is None


def test_M_T_TEAMS_CHANNEL_CONTEXT_FIELDS_01_context_has_channel_user_tenant() -> None:
    event = parse_activity(_activity(), claims=_claims())

    assert event is not None
    assert event.ctx.channel is ChannelKind.TEAMS
    assert event.ctx.caller_id == "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    assert event.ctx.channel_session_id == "19:conversation@example.invalid"
    assert event.intent.metadata is not None
    assert event.intent.metadata["tenant_id"] == "11111111-2222-4333-8444-555555555555"
    assert event.intent.metadata["channel_id"] == "msteams"


def test_M_T_TEAMS_AUTH_CLAIMS_EXTRACT_01_extracts_claims_as_strings() -> None:
    claims = extract_claims(_claims())

    assert claims["iss"].startswith("https://login.microsoftonline.com/")
    assert claims["sub"] == "entra-subject-stage12-fixture"
    assert claims["exp"] == "1790784000"
    assert all(isinstance(key, str) and isinstance(value, str) for key, value in claims.items())
