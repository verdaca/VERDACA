"""Stage 13 WebhookSigningKeyResolver MAC-Ts."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from praxis.kernel.gateway.composition_types import WebhookSigningKeyResolver
from praxis.ports.gateway_dto import ChannelKind

ROOT = Path(__file__).parents[5]
RESOLVER_PATH = (
    ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway"
    / "composition_types.py"
)


def test_M_T_AUTH_WEBHOOK_RESOLVER_FAIL_FAST_EMPTY_01_empty_secret_raises() -> None:
    with pytest.raises(ValueError):
        WebhookSigningKeyResolver(secrets={ChannelKind.TEAMS: ""})


def test_M_T_AUTH_WEBHOOK_RESOLVER_FAIL_FAST_UNKNOWN_CHANNEL_01_missing_channel_raises() -> None:
    resolver = WebhookSigningKeyResolver(secrets={ChannelKind.TEAMS: "secret"})

    with pytest.raises(KeyError):
        resolver.resolve(ChannelKind.SLACK)


def test_M_T_AUTH_WEBHOOK_RESOLVER_NOT_A_PORT_01_resolver_is_not_protocol() -> None:
    tree = ast.parse(RESOLVER_PATH.read_text(encoding="utf-8"))
    resolver = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "WebhookSigningKeyResolver"
    )
    base_names = {
        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
        for base in resolver.bases
    }

    assert "Protocol" not in base_names
