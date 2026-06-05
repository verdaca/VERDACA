"""Stage 12 H#3.1 MAC-Ts for kernel auth claim validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from praxis.kernel.auth.claims import ClaimsValidationError, validate_claims

FIXTURES_DIR = Path(__file__).parents[4] / "fixtures" / "auth_claims"
FIXTURE_FILES = (
    "entra_basic.json",
    "okta_basic.json",
    "auth0_basic.json",
)
REQUIRED_CLAIMS = ("sub", "iss", "aud", "iat", "exp")


def _load_fixture(name: str) -> dict[str, str]:
    raw = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in raw.items()}


@pytest.mark.no_waiver
@pytest.mark.parametrize("fixture_name", FIXTURE_FILES)
@pytest.mark.parametrize("missing_claim", REQUIRED_CLAIMS)
def test_M_T_AUTH_CLAIMS_SCHEMA_01_missing_required_claim_raises(
    fixture_name: str,
    missing_claim: str,
) -> None:
    raw = _load_fixture(fixture_name)
    raw.pop(missing_claim)

    with pytest.raises(ClaimsValidationError) as exc_info:
        validate_claims(raw)

    assert set(exc_info.value.missing) == {missing_claim}


def test_M_T_AUTH_CLAIMS_EXTRA_FIELDS_PASS_01_unknown_claims_are_preserved() -> None:
    raw = _load_fixture("entra_basic.json")
    raw["stage12_unknown_claim"] = "opaque"

    claims = validate_claims(raw)

    assert claims.require("stage12_unknown_claim") == "opaque"
