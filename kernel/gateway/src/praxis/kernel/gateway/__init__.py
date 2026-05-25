"""Verdaca channel-neutral gateway implementation package.

Port Protocols and DTOs remain canonical under ``praxis.ports``. This package
exports implementation types only.
"""

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
    "GatewayPolicy",
    "GatewayWalConfig",
    "GatewayWalStore",
    "NormalizedExecution",
    "PolicyDecision",
    "VerdacaGatewayService",
    "WAL_PRAGMAS",
    "normalize_execution_request",
]
