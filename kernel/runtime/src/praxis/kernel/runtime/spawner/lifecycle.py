"""Praxis Runtime spawner — SpawnedAgent lifecycle container.

SpawnedAgent holds a spawned agent's memory proxy and role.
It does NOT expose the underlying Memory facade (no back-door).

Architecture §4.1.5, §4.4, §9.1. S4.R-01: no _memory back-door.
"""

from __future__ import annotations

from uuid import UUID

from praxis.kernel.runtime.models import AgentRole
from praxis.kernel.runtime.proxies import ProducerMemoryProxy, ReviewerMemoryProxy


class SpawnedAgent:
    """A spawned agent's handle.

    Holds the memory proxy (the ONLY memory access point), the role, and the
    spawn ID. Does NOT expose the raw Memory facade.

    Architecture §4.1.5 critical property: no back-door to underlying Memory.
    """

    def __init__(
        self,
        agent_name: str,
        role: AgentRole,
        memory_proxy: ProducerMemoryProxy | ReviewerMemoryProxy,
        spawn_id: UUID,
    ) -> None:
        self._agent_name = agent_name
        self._role = role
        # The proxy IS the only memory handle. Never expose the raw Memory.
        self._proxy = memory_proxy
        self._spawn_id = spawn_id

    @property
    def agent_name(self) -> str:
        return self._agent_name

    @property
    def role(self) -> AgentRole:
        return self._role

    @property
    def spawn_id(self) -> UUID:
        return self._spawn_id

    @property
    def memory(self) -> ProducerMemoryProxy | ReviewerMemoryProxy:
        """The agent's ONLY memory handle. Always a proxy, never the raw Memory."""
        return self._proxy

    def __repr__(self) -> str:
        return (
            f"SpawnedAgent(agent_name={self._agent_name!r}, "
            f"role={self._role}, "
            f"spawn_id={self._spawn_id})"
        )


__all__ = ["SpawnedAgent"]
