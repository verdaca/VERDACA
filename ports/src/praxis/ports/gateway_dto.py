"""GatewayPort DTOs frozen at Stage 11 [E1-H#1.5-PORT-FROZEN]."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterator, Mapping, NoReturn

from praxis.ports.gateway_errors import AuthClaimsAccessError


class CallerKind(Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class ChannelKind(Enum):
    CLI = "cli"
    TEAMS = "teams"
    SLACK = "slack"
    CLAUDE_DESKTOP = "claude_desktop"
    WEB = "web"


class _ImmutableClaims(Mapping[str, str]):
    """Deepcopy-safe immutable mapping for dataclasses.asdict traversal."""

    def __init__(self, claims: Mapping[str, str]) -> None:
        self._claims = dict(claims)

    def __getitem__(self, key: str) -> str:
        return self._claims[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._claims)

    def __len__(self) -> int:
        return len(self._claims)

    def __deepcopy__(self, memo: object) -> "_ImmutableClaims":
        return _ImmutableClaims(self._claims)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class ChannelContext:
    """Opaque caller-identity DTO. Stage 12+ auth stage will fill in auth_claims."""

    caller_id: str
    caller_kind: CallerKind
    auth_claims: AuthClaims
    channel: ChannelKind
    channel_session_id: str
    request_id: str
    trace_id: str | None = None
    budget_remaining_usd: Decimal | None = None
    rate_limit_token: str | None = None

    def __repr__(self) -> str:
        return (
            "ChannelContext("
            f"caller_id={self.caller_id!r}, "
            f"caller_kind={self.caller_kind.name}, "
            f"channel={self.channel.name}, "
            f"channel_session_id={self.channel_session_id!r}, "
            f"request_id={self.request_id!r}, "
            f"auth_claims={self.auth_claims!r})"
        )


FROZEN_FIELD_ALLOWLIST: frozenset[str] = frozenset(
    {
        "caller_id",
        "caller_kind",
        "auth_claims",
        "channel",
        "channel_session_id",
        "request_id",
        "trace_id",
        "budget_remaining_usd",
        "rate_limit_token",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StartAnalysisRequest:
    """Channel-neutral analysis request accepted by GatewayPort."""

    question: str
    requester_user_id: str
    workspace_id: str
    idempotency_key: str
    depth: str = "standard"
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionHandle:
    """Stable handle for a persisted Verdaca session."""

    session_id: str
    status: str
    source_uri: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactRef:
    """Gateway-visible artifact reference."""

    artifact_id: str
    session_id: str
    kind: str
    uri: str
    title: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisResult:
    """Channel-neutral gateway execution result."""

    session: SessionHandle
    recommendation: str
    cited_tradeoffs: tuple[str, ...]
    dissent_frames: tuple[str, ...] = ()
    artifacts: tuple[ArtifactRef, ...] = ()
    cost_usd: Decimal | None = None


__all__ = [
    "AnalysisResult",
    "ArtifactRef",
    "AuthClaims",
    "CallerKind",
    "ChannelContext",
    "ChannelKind",
    "FROZEN_FIELD_ALLOWLIST",
    "SessionHandle",
    "StartAnalysisRequest",
]
