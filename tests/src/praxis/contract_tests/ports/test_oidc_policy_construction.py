"""Stage 13 OIDC policy construction MAC-Ts."""

from __future__ import annotations

import pytest

from praxis.kernel.auth import OidcPolicy, extract_claims


def test_M_T_AUTH_OIDC_POLICY_VERIFIER_REQUIRED_01_missing_verifier_raises_typeerror() -> None:
    with pytest.raises(TypeError):
        OidcPolicy(audience="api://verdaca")  # type: ignore[call-arg]


def test_M_T_AUTH_EXTRACT_CLAIMS_VERIFIER_REQUIRED_01_missing_verifier_raises_typeerror() -> None:
    with pytest.raises(TypeError):
        extract_claims("token-string")  # type: ignore[call-arg]
