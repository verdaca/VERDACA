"""D2 cross-window contract: channel adapter auth_claims -> kernel validation."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from praxis.adapters.channels.slack.events import parse_event
from praxis.adapters.channels.teams.events import parse_activity
from praxis.kernel.auth.claims import ClaimsValidationError, validate_claims

FIXTURES_DIR = Path(__file__).parents[4] / "fixtures" / "auth_claims"

FIXTURE_FILES: tuple[tuple[str, Callable[[Mapping[str, object]], dict[str, str]]], ...] = (
    ("entra_basic.json", lambda payload: _teams_claims(payload)),
    ("okta_basic.json", lambda payload: _slack_claims(payload)),
    ("auth0_basic.json", lambda payload: _teams_claims(payload)),
)


def _teams_claims(payload: Mapping[str, object]) -> dict[str, str]:
    event = parse_activity(
        {
            "type": "message",
            "from": {"aadObjectId": "user-1"},
            "conversation": {"id": "conversation-1"},
            "channelData": {"tenant": {"id": "tenant-1"}},
            "id": "activity-1",
            "text": "hello",
        },
        claims=payload,
    )
    assert event is not None
    return dict(event.ctx.auth_claims.unwrap())


def _slack_claims(payload: Mapping[str, object]) -> dict[str, str]:
    event = parse_event(
        {
            "team_id": "team-1",
            "event": {
                "type": "app_mention",
                "user": "user-1",
                "channel": "channel-1",
                "event_ts": "1700000000.000100",
                "text": "hello",
            },
        },
        claims=payload,
    )
    assert event is not None
    return dict(event.ctx.auth_claims.unwrap())


@pytest.mark.parametrize(("fixture_file", "extract_fn"), FIXTURE_FILES)
def test_M_T_AUTH_E1_CONSUMES_E2_IDP_FIXTURE_01_channel_claims_validate(
    fixture_file: str,
    extract_fn: Callable[[Mapping[str, object]], dict[str, str]],
) -> None:
    raw_jwt_payload = json.loads((FIXTURES_DIR / fixture_file).read_text(encoding="utf-8"))

    claims = extract_fn(raw_jwt_payload)

    assert isinstance(claims, dict)
    for key, value in claims.items():
        assert isinstance(key, str)
        assert isinstance(value, str), f"Adapter must coerce {key!r} value to str"
    validate_claims(claims)


def test_M_T_AUTH_E1_CONSUMES_E2_IDP_FIXTURE_01_missing_sub_fails_validation() -> None:
    incomplete = {
        "iss": "https://login.microsoftonline.com/tenant/v2.0",
        "aud": "verdaca-api",
        "iat": "1716800000",
        "exp": "1716803600",
    }

    with pytest.raises(ClaimsValidationError, match="sub"):
        validate_claims(incomplete)
