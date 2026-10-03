"""Stage 14 ratified JWKS-rotation invariant (runtime no_waiver, pin 14/9/23).

The Stage 14 scope ratified a single new runtime no_waiver marker —
``M-T-AUTH-JWKS-ROTATION-INVARIANT-01`` — guarding the security-critical
property that the auth spine never accepts a token validated under a retired
key after a JWKS rotation, and that the verifier holds NO persistent JWKS
state (key resolution is delegated to ``JwksCache`` per the Stage 14 V3.A
contract / commit ``15fcc60``). This file is the runtime bearer of that
marker; it is excluded from the Stage 13 collector's scan (it is Stage 14
scope) and recognized by the Stage 14 collector's canonicalizer.
"""

from __future__ import annotations

import base64
import json

import pytest

from praxis.kernel.auth import JwksCache, OidcPolicy, UnknownKeyError
from praxis.kernel.auth.claims import AuthenticationError


def _bearer_with_kid(kid: str) -> str:
    """Craft a bearer whose JWT header advertises ``kid``.

    ``OidcPolicy.authenticate`` parses the header for the kid WITHOUT
    verification (signature is checked later via the cache-resolved key), so a
    crafted header segment is sufficient to drive kid-based cache resolution.
    """
    header = (
        base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "kid": kid}).encode("utf-8"))
        .rstrip(b"=")
        .decode("ascii")
    )
    return f"{header}.cGF5bG9hZA.c2ln"


class _RotatedJwksCache(JwksCache):
    """JWKS snapshot AFTER a rotation: only ``live_kids`` resolve; retired kids raise."""

    def __init__(self, live_kids: set[str]) -> None:
        super().__init__()
        self._live_kids = live_kids

    async def get_key(self, issuer: str, kid: str) -> dict[str, object]:  # type: ignore[override]
        if kid not in self._live_kids:
            raise UnknownKeyError(kid)
        return {"kid": kid, "kty": "RSA"}


class _RecordingVerifier:
    """Verifier stand-in: records which cache-resolved key reached ``decode``.

    Holds no persistent JWKS state of its own — the whole point of the Stage 14
    invariant is that the rotated-in key flows from the cache to ``decode``.
    """

    issuer = "https://issuer.example.invalid"

    def __init__(self) -> None:
        self.decoded_kids: list[str] = []

    def decode(
        self, token: str, *, audience: str, key: dict[str, object]
    ) -> dict[str, object]:
        self.decoded_kids.append(str(key["kid"]))
        return {"sub": "user-1", "aud": audience}


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_ROTATION_INVARIANT_01_retired_key_rejected_rotated_in_accepted() -> (
    None
):
    verifier = _RecordingVerifier()
    # Post-rotation: "key-001" retired, "key-003" rotated in.
    policy = OidcPolicy(
        verifier=verifier,  # type: ignore[arg-type]
        audience="api://verdaca",
        jwks_cache=_RotatedJwksCache(live_kids={"key-003"}),
    )

    # Retired key: rejected at resolution and never reaches decode.
    with pytest.raises(AuthenticationError):
        await policy.authenticate(_bearer_with_kid("key-001"))
    assert verifier.decoded_kids == []

    # Rotated-in key: accepted, and the rotated-in key is exactly what decode used.
    claims = await policy.authenticate(_bearer_with_kid("key-003"))
    assert claims["sub"] == "user-1"
    assert verifier.decoded_kids == ["key-003"]
