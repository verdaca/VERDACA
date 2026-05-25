"""Verdaca channel-neutral gateway implementation package.

Port Protocols and DTOs remain canonical under ``praxis.ports``. This package
exports implementation types only.
"""

from praxis.kernel.gateway.dial import (
    DIAL_API_BASE,
    DIAL_API_VERSION,
    DIAL_LITELLM_MODEL,
    DIAL_LITELLM_PROVIDER,
    create_dial_llm_proxy,
)
from praxis.kernel.gateway.execution import NormalizedExecution, normalize_execution_request
from praxis.kernel.gateway.policy import GatewayPolicy, PolicyDecision
from praxis.kernel.gateway.service import VerdacaGatewayService
from praxis.kernel.gateway.wal import (
    WAL_PRAGMAS,
    AsyncSessionIndex,
    GatewayWalConfig,
    GatewayWalStore,
)

__all__ = [
    "AsyncSessionIndex",
    "DIAL_API_BASE",
    "DIAL_API_VERSION",
    "DIAL_LITELLM_MODEL",
    "DIAL_LITELLM_PROVIDER",
    "GatewayPolicy",
    "GatewayWalConfig",
    "GatewayWalStore",
    "NormalizedExecution",
    "PolicyDecision",
    "VerdacaGatewayService",
    "WAL_PRAGMAS",
    "create_dial_llm_proxy",
    "normalize_execution_request",
]
