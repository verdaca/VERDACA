"""Composition-only types for gateway startup wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from praxis.ports.gateway_dto import ChannelKind


@dataclass(frozen=True, slots=True)
class WebhookSigningKeyResolver:
    """Resolve inbound webhook signing keys without promoting a new port."""

    secrets: Mapping[ChannelKind, str]

    def __post_init__(self) -> None:
        for kind, secret in self.secrets.items():
            if not secret:
                raise ValueError(f"Webhook signing secret for {kind.value!r} is empty")

    def resolve(self, kind: ChannelKind) -> str:
        try:
            return self.secrets[kind]
        except KeyError as exc:
            raise KeyError(f"No webhook signing secret configured for {kind.value!r}") from exc


__all__ = ["WebhookSigningKeyResolver"]
