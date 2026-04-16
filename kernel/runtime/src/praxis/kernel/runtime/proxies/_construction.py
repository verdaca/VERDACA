"""Single proxy creation point — architecture §4.1.5 / §9.1.1.

This is the ONLY place in the runtime that may call
ProducerMemoryProxy(...) or ReviewerMemoryProxy(...).

The static grep audit in test_construction_single_point.py
(§11.2.2) enforces this at CI time — any construction elsewhere
is a Layer 2 back-door that bypasses role-based selection.
"""

from __future__ import annotations

from uuid import UUID

from praxis.kernel.runtime.proxies._base import AgentRole
from praxis.kernel.runtime.proxies.producer import ProducerMemoryProxy
from praxis.kernel.runtime.proxies.reviewer import ReviewerMemoryProxy


def _construct_memory_proxy(
    *,
    memory: object,
    tenant_id: str,
    agent_name: str,
    spawn_id: UUID,
    role: AgentRole,
) -> ProducerMemoryProxy | ReviewerMemoryProxy:
    """Return the correct proxy type for *role*.

    This is the single authorised construction point.  The Spawner
    (Stage 4.3 Checkpoint 2) calls this function; nothing else does.
    """
    if role is AgentRole.PRODUCER:
        return ProducerMemoryProxy(
            memory=memory,
            tenant_id=tenant_id,
            agent_name=agent_name,
            spawn_id=spawn_id,
        )
    if role is AgentRole.REVIEWER:
        return ReviewerMemoryProxy(
            memory=memory,
            tenant_id=tenant_id,
            agent_name=agent_name,
            spawn_id=spawn_id,
        )
    raise ValueError(f"Unknown role: {role!r}")


__all__ = ["_construct_memory_proxy"]
