"""Canonical gateway composition root.

All dependencies are caller-supplied and keyword-only. Tests may pass fakes
explicitly; production startup must pass concrete adapters explicitly. This
module does not synthesize fallbacks for missing auth dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping

from praxis.kernel.auth import JwtVerifier, NonceStore, OidcPolicy
from praxis.kernel.gateway.composition_types import WebhookSigningKeyResolver
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.kernel.gateway.service import VerdacaGatewayService
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.compaction import CompactionPort
from praxis.ports.cost_meter import CostMeterPort
from praxis.ports.gateway import ChannelAdapterPort, GatewayPort
from praxis.ports.gateway_dto import ChannelKind
from praxis.ports.llm_proxy import LLMProxyPort
from praxis.ports.memory import MemoryPort


def build_gateway(
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
    """Build the single canonical GatewayPort implementation.

    WebhookSigningKeyResolver is retained for inbound channel webhook verification
    and is not part of the GatewayPort execute path.
    """
    return VerdacaGatewayService(
        llm_proxy=llm_proxy,
        memory=memory,
        cost_meter=cost_meter,
        compaction=compaction,
        session_index=session_index,
        channel_adapters=dict(channel_adapters),
        jwt_verifier=jwt_verifier,
        oidc_policy=oidc_policy,
        nonce_store=nonce_store,
        webhook_resolver=webhook_resolver,
        policy=policy,
    )


__all__ = ["build_gateway"]
