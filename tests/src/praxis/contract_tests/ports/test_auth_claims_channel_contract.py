"""D2 cross-window contract: channel adapter auth_claims -> kernel validation."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from praxis.adapters.channels.slack.events import extract_claims as slack_extract_claims
from praxis.adapters.channels.teams.events import extract_claims as teams_extract_claims
from praxis.kernel.auth.claims import ClaimsValidationError, validate_claims

FIXTURES_DIR = Path(__file__).parents[4] / "fixtures" / "auth_claims"

FIXTURE_FILES: tuple[tuple[str, Callable[..., dict[str, str]]], ...] = (
    ("entra_basic.json", teams_extract_claims),
    ("okta_basic.json", slack_extract_claims),
    ("auth0_basic.json", teams_extract_claims),
)


@pytest.mark.parametrize(("fixture_file", "extract_fn"), FIXTURE_FILES)
def test_M_T_AUTH_E1_CONSUMES_E2_IDP_FIXTURE_01_channel_claims_validate(
    fixture_file: str,
    extract_fn: Callable[[dict[str, object]], dict[str, str]],
) -> None:
    raw_jwt_payload = json.loads((FIXTURES_DIR / fixture_file).read_text(encoding="utf-8"))

    claims = extract_fn(raw_jwt_payload, verifier=None)

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
