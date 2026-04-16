"""Praxis Runtime spawner — AgentSpawner.

The Spawner orchestrates agent construction. It is the last subtree
because it depends on all others: proxies, registry, budget, circular guard,
lifecycle, and tools.

Architecture §4.1, §4.3, §9.1, §9.7, §9.8.

Critical invariants:
- _construct_proxy_for_role is the SINGLE proxy creation point (§4.1.5)
- It delegates to proxies._construction._construct_memory_proxy
- compute_child_allowlist enforces parent ∩ child_baseline (§9.7)
- compute_stripped_tools returns the difference for Q5 metric emission
"""

from __future__ import annotations

from uuid import UUID

from praxis.kernel.runtime.models import AgentRole
from praxis.kernel.runtime.proxies import ProducerMemoryProxy, ReviewerMemoryProxy

# Single point of proxy creation — delegates to Checkpoint 1's authoritative function
from praxis.kernel.runtime.proxies._construction import _construct_memory_proxy

# ---------------------------------------------------------------------------
# Proxy construction — single-point delegation to Checkpoint 1 impl
# ---------------------------------------------------------------------------


def _construct_proxy_for_role(
    *,
    role: AgentRole,
    memory: object,
    tenant_id: str,
    agent_name: str,
    spawn_id: UUID,
) -> ProducerMemoryProxy | ReviewerMemoryProxy:
    """Construct the correct memory proxy for *role*.

    Delegates to proxies._construction._construct_memory_proxy — the
    architecture §4.1.5 single-point construction path established in
    Checkpoint 1. This is NOT a new proxy creation; it is a thin forwarding
    shim so the Spawner can call it with keyword arguments.
    """
    return _construct_memory_proxy(
        memory=memory,
        tenant_id=tenant_id,
        agent_name=agent_name,
        spawn_id=spawn_id,
        role=role,
    )


# ---------------------------------------------------------------------------
# Allowlist intersection (architecture §9.7)
# ---------------------------------------------------------------------------


def compute_child_allowlist(
    *,
    parent_allowlist: frozenset[str],
    child_baseline: frozenset[str],
) -> frozenset[str]:
    """Compute the effective child allowlist as parent ∩ child_baseline.

    Architecture §9.7: spawned children cannot have tools the parent doesn't
    have. The intersection is the structural enforcement of privilege
    non-escalation.

    Returns:
        frozenset[str] of tool grants available to the child.
    """
    return parent_allowlist & child_baseline


def compute_stripped_tools(
    *,
    parent_allowlist: frozenset[str],
    child_baseline: frozenset[str],
) -> frozenset[str]:
    """Return the set of tools stripped from child_baseline by parent intersection.

    Used for Q5 metric: runtime.agent.allowlist.stripped.count per stripped tool.
    """
    return child_baseline - parent_allowlist


# ---------------------------------------------------------------------------
# AgentSpawner (lightweight — full async lifecycle deferred to Stage 5)
# ---------------------------------------------------------------------------


class AgentSpawner:
    """The agent construction and lifecycle surface.

    At Stage 4.3, this is a structural stub. The full async context-manager
    lifecycle (spawn_subagent / spawn_team) requires the Communication Bus
    (§7) and MAC integration (§8.5), both of which are Stage 5 concerns.

    What Stage 4.3 provides:
    - _construct_proxy_for_role (single-point delegation to Checkpoint 1)
    - compute_child_allowlist (§9.7 privilege non-escalation)
    - ResourceBudget defaults (§4.3)
    - CircularSpawnGuard (§9.8)
    """

    pass


__all__ = [
    "AgentSpawner",
    "_construct_proxy_for_role",
    "compute_child_allowlist",
    "compute_stripped_tools",
    "_construct_memory_proxy",  # re-exported for audit grep compatibility
]
