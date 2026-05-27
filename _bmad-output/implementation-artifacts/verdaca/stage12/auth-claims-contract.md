# Stage 12 H#1.5 Auth Claims Contract

**Status:** H#1.5 freeze document, pending H#2 charter ratification.
**Branch:** `stage-12.0-channel-adapters`
**Pre-freeze HEAD:** `57fd348`

## §1 Frozen DTO Surface

Source: `ports/src/praxis/ports/gateway_dto.py`.

Freeze-line comment:

```python
"""GatewayPort DTOs frozen at Stage 11 [E1-H#1.5-PORT-FROZEN]."""
```

AuthClaims definition:

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthClaims:
    """Opaque wrapper around auth claims. PII protection by construction."""

    _claims: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_claims", _ImmutableClaims(self._claims))

    def __repr__(self) -> str:
        return f"AuthClaims(<{len(self._claims)} redacted>)"

    def __iter__(self) -> NoReturn:
        raise AuthClaimsAccessError("Use .unwrap() to access claims")

    def unwrap(self) -> Mapping[str, str]:
        return self._claims
```

Frozen field list:

```text
_claims: Mapping[str, str]
```

Stage 11 freeze is sufficient for Stage 12 H#1.5. No Stage 12 `AuthClaims` DTO additions are required. Any request to add fields or change visibility requires REFREEZE-03.

## §2 SHA Freeze Stamp

H#1.5 freeze commit SHA: `3257304`

The following commit back-fills this stamp into the contract doc.

## §3 Fixture Inventory

All fixture payloads are synthetic. They contain no real tokens, no real keys, and no real tenant IDs. Numeric JWT timestamp claims are stored as strings to satisfy `AuthClaims(_claims: Mapping[str, str])`.

| Fixture | Bytes | SHA-256 | Notes |
|---|---:|---|---|
| `tests/fixtures/auth_claims/entra_basic.json` | 500 | `9197755685D5E269D21608D8CCF8EC72B652166BD26416A5A109F3179BDE7B01` | Entra-style `tid`, `oid`, `preferred_username`, `scp`. |
| `tests/fixtures/auth_claims/okta_basic.json` | 446 | `5A3F438017FE3A43085EE09B87B1CBC6118EAC28B0B45AA15C1160A5CFED15E8` | Okta-style `groups`, `cid`, `uid`, `scope`. |
| `tests/fixtures/auth_claims/auth0_basic.json` | 410 | `1663384E483400F20E29A7ED90408BC2C3DC221A935FF604FCA9A574F1E25F62` | Auth0-style `azp`, `permissions`, namespaced issuer. |

## §4 Auth API Signature Freeze

These signatures are the H#1.5 cross-window contract for E1 stubbing and E2 implementation planning. H#2 charter may refine names and DTO classes, but any post-H#1.5 signature drift must be surfaced as a REFREEZE-03 candidate.

```python
from collections.abc import Mapping

from praxis.ports.gateway_dto import AuthClaims


def validate_jwt(
    token: str,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> Mapping[str, str]:
    """Validate a JWT and return normalized string claims."""


def map_claims_to_auth_claims(claims: Mapping[str, str]) -> AuthClaims:
    """Wrap normalized IdP claims in the frozen AuthClaims DTO."""


def discover_idp(issuer_url: str) -> "OidcMetadata":
    """Discover OIDC metadata for an issuer URL."""
```

E2 may implement `OidcMetadata` under `praxis.kernel.auth`; the public discovery function remains `discover_idp(...)` unless H#2 explicitly ratifies the D3 `discover(issuer: str) -> OidcMetadata` spelling instead.

## §5 REFREEZE-03 Trigger Conditions

Open REFREEZE-03 if any of the following happen:

- E2 needs to add fields to `AuthClaims`.
- E2 needs to expose raw claims through iteration or serialization instead of `.unwrap()`.
- E2 changes `validate_jwt(...)`, `map_claims_to_auth_claims(...)`, or `discover_idp(...)` after H#1.5 without H#2 ratification.
- E1 cannot map Teams or Slack identity data into the three fixture shapes without changing `AuthClaims`.
- A channel adapter needs a new method on `ChannelAdapterPort` instead of event-intake wrapper code around the frozen `execute(...)` method.

REFREEZE-03 is an advisor + Winston escalation, not an executor-local edit.

## §6 Cross-Window Contract Test Pointer

Deferred implementation target:

```text
tests/src/praxis/contract_tests/ports/test_auth_claims_channel_contract.py
```

The future test should bind E1 and E2 by loading the three fixtures in `tests/fixtures/auth_claims/`, mapping each through E2's claims mapper, and proving Teams/Slack channel context creation consumes frozen `AuthClaims` without mock substitution.

## §provenance

| Field | Value |
|---|---|
| Surface | Codex CLI/API runtime |
| Model | GPT-5 / Codex |
| Working directory | `C:\Users\AndreyPopov\Documents\Anthropic` |
| Session JSONL path | `C:\Users\AndreyPopov\.codex\sessions\2026\05\26\rollout-2026-05-26T18-33-56-019e64eb-cfb5-7ae2-a906-5c431a8986a5.jsonl` |
| Python | `Python 3.12.12` |
| uv | `uv 0.10.6` |
| Pre-freeze branch | `stage-12.0-channel-adapters` |
| Pre-freeze HEAD | `57fd348` |
| Memory loaded | `project_verdaca_stage12_scope`, `project_verdaca_strategic_sequencing`, `feedback_escalation_criticality_threshold`, `feedback_no_waiver_discipline`, `feedback_memory_authorization`, `feedback_handover_template_discipline`, `feedback_corrigendum_paired_sweep`, `feedback_provenance_pin` |
