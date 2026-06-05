"""Stage 12 H#3.3 MAC-Ts for JWT algorithm pinning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

import praxis.kernel.auth.jwt as jwt_module
from praxis.kernel.auth.jwt import JwtVerifier, UnsupportedAlgorithmError
from praxis.kernel.auth.oidc import OidcMetadata

CASSETTES_DIR = Path(__file__).parents[4] / "fixtures" / "vcr_cassettes"
ISSUER = "https://login.microsoftonline.com/stage12-tenant/v2.0"
JWKS_URI = "https://login.microsoftonline.com/stage12-tenant/discovery/v2.0/keys"


def _metadata(algorithms: list[str]) -> OidcMetadata:
    return OidcMetadata(
        issuer=ISSUER,
        jwks_uri=JWKS_URI,
        id_token_signing_alg_values_supported=tuple(algorithms),
    )


def _alg_poison_algorithms() -> list[str]:
    cassette = yaml.safe_load(
        (CASSETTES_DIR / "oidc_discovery_alg_poison.yaml").read_text(encoding="utf-8")
    )
    body = cassette["interactions"][0]["response"]["body"]["string"]
    loaded = json.loads(body)
    return [str(alg) for alg in loaded["id_token_signing_alg_values_supported"]]


@pytest.mark.no_waiver
@pytest.mark.parametrize(
    ("algorithms", "expected_safe"),
    [
        (["none"], None),
        (["HS256"], None),
        (_alg_poison_algorithms(), ["RS256"]),
    ],
)
def test_M_T_AUTH_JWT_ALG_PIN_01_filters_or_rejects_unsafe_algorithms(
    algorithms: list[str],
    expected_safe: list[str] | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructed_algorithms: list[list[str]] = []

    class _RecordingJsonWebToken:
        def __init__(
            self,
            algorithms: list[str],
            private_headers: dict[str, Any] | None = None,
        ) -> None:
            self.private_headers = private_headers
            constructed_algorithms.append(list(algorithms))

    monkeypatch.setattr(jwt_module, "JsonWebToken", _RecordingJsonWebToken)

    if expected_safe is None:
        with pytest.raises(UnsupportedAlgorithmError):
            JwtVerifier(_metadata(algorithms))
        assert constructed_algorithms == []
        return

    JwtVerifier(_metadata(algorithms))

    assert constructed_algorithms == [expected_safe]
