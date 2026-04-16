"""Praxis Runtime spawner — circular spawn prevention.

Three-layer defense: depth limit + cycle detection + budget enforcement.
Architecture §9.8, S4.R-07.
"""

from __future__ import annotations


class MaxSpawnDepthExceededError(Exception):
    """Raised when spawn depth exceeds max_depth per architecture §9.8 item 1."""


class CircularSpawnError(Exception):
    """Raised when the same agent appears >max_recursion_per_agent times per §9.8 item 2."""


class CircularSpawnGuard:
    """Enforces spawn depth + cycle detection invariants.

    Per architecture §9.8:
    1. Depth limit: max_depth (default 8)
    2. Cycle detection: same agent name >max_recursion_per_agent times in ancestor chain
    3. Budget enforcement: owned by ResourceBudget (separate class)
    """

    def __init__(
        self,
        max_depth: int = 8,
        max_recursion_per_agent: int = 2,
    ) -> None:
        self.max_depth = max_depth
        self.max_recursion_per_agent = max_recursion_per_agent

    def check_spawn(
        self,
        agent_name: str,
        spawn_depth: int,
        ancestor_chain: list[str],
    ) -> None:
        """Check depth limit and cycle detection. Raises on violation.

        Args:
            agent_name: Name of the agent being spawned.
            spawn_depth: Current depth (0 = top-level spawn).
            ancestor_chain: List of ancestor agent names (from root to parent).
        """
        # Depth limit (architecture §9.8 item 1)
        if spawn_depth > self.max_depth:
            raise MaxSpawnDepthExceededError(
                f"Spawn depth {spawn_depth} exceeds max_depth={self.max_depth}. "
                f"Possible runaway recursion in {ancestor_chain + [agent_name]}. "
                "Architecture §9.8: increase max_depth via deployment config if needed."
            )

        # Cycle detection (architecture §9.8 item 2)
        # "agents can be recursively invoked up to N deep, but not N+1"
        # means the same agent may appear at most max_recursion_per_agent times
        # in the FULL chain (ancestors + current spawn).
        # A→B→A: full_chain=["agent-a","agent-b","agent-a"], count=2 ≥ 2 → raise.
        full_chain = ancestor_chain + [agent_name]
        occurrences = full_chain.count(agent_name)
        if occurrences >= self.max_recursion_per_agent:
            raise CircularSpawnError(
                f"Agent {agent_name!r} appears {occurrences} time(s) in the spawn chain "
                f"(limit: {self.max_recursion_per_agent - 1} allowed before current spawn). "
                f"Full chain: {full_chain}. "
                "Architecture §9.8 item 2: circular spawning detected."
            )


__all__ = [
    "CircularSpawnGuard",
    "MaxSpawnDepthExceededError",
    "CircularSpawnError",
]
