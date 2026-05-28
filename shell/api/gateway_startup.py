"""Thin shell caller for the kernel gateway composition root."""

from __future__ import annotations

from collections.abc import Mapping

from praxis.kernel.auth import JwtVerifier, NonceStore, OidcPolicy
from praxis.kernel.gateway.composition import build_gateway
from praxis.kernel.gateway.composition_types import WebhookSigningKeyResolver
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.compaction import CompactionPort
from praxis.ports.cost_meter import CostMeterPort
from praxis.ports.gateway import ChannelAdapterPort, GatewayPort
from praxis.ports.gateway_dto import ChannelKind
from praxis.ports.llm_proxy import LLMProxyPort
from praxis.ports.memory import MemoryPort


def create_gateway(
    *,
    session_index: SessionIndexPort,
    compaction: CompactionPort,
    memory: MemoryPort,
    llm_proxy: LLMProxyPort,
    cost_meter: CostMeterPort,
    channel_adapters: Mapping[ChannelKind, ChannelAdapterPort],
    jwt_verifier: JwtVerifier,
    oidc_policy: OidcPolicy,
    nonce_store: NonceStore,
    webhook_resolver: WebhookSigningKeyResolver,
    policy: GatewayPolicy,
) -> GatewayPort:
    """Delegate shell startup to the canonical kernel composition root."""
    return build_gateway(
        session_index=session_index,
        compaction=compaction,
        memory=memory,
        llm_proxy=llm_proxy,
        cost_meter=cost_meter,
        channel_adapters=channel_adapters,
        jwt_verifier=jwt_verifier,
        oidc_policy=oidc_policy,
        nonce_store=nonce_store,
        webhook_resolver=webhook_resolver,
        policy=policy,
    )


__all__ = ["create_gateway"]
