"""Gateway service skeleton for Stage 11 Phase A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.kernel.session_index.port import SessionIndexPort
from praxis.ports.compaction import CompactionPort
from praxis.ports.cost_meter import CostMeterPort
from praxis.ports.llm_proxy import LLMProxyPort
from praxis.ports.memory import MemoryPort


@dataclass(slots=True, kw_only=True)
class VerdacaGatewayService:
    """Implementation holder for the channel-neutral GatewayPort service.

    H#2.2 intentionally lands the package skeleton only. H#2.3 wires
    composition and adds the GatewayPort ``execute`` method.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    llm_proxy: LLMProxyPort | None = None
    memory: MemoryPort | None = None
    cost_meter: CostMeterPort | None = None
    compaction: CompactionPort | None = None
    session_index: SessionIndexPort | None = None
    policy: GatewayPolicy = GatewayPolicy()

    @property
    def is_wired(self) -> bool:
        """Return whether all required composition ports have been supplied."""
        return all(
            dependency is not None
            for dependency in (
                self.llm_proxy,
                self.memory,
                self.cost_meter,
                self.compaction,
                self.session_index,
            )
        )


__all__ = [
    "VerdacaGatewayService",
]
