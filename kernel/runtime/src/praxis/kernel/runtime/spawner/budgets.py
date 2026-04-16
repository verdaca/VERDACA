"""Praxis Runtime spawner — ResourceBudget.

Hard ceilings enforced by the Spawner.
Architecture §4.3, §9.7 (budget is non-bypassable).
"""

from __future__ import annotations

from dataclasses import dataclass

from praxis.kernel.runtime.models import AgentRole


class BudgetExceededError(Exception):
    """Raised when a spawned agent exceeds its ResourceBudget ceiling."""


@dataclass(frozen=True)
class ResourceBudget:
    """Hard ceilings enforced at the proxy layer and tool adapter layer.

    Agents cannot read or modify their own budget.
    Spawner is authoritative.
    """

    max_tokens: int
    max_wall_seconds: float
    max_tool_calls: int
    max_memory_writes: int

    @classmethod
    def default_for_role(cls, role: AgentRole) -> "ResourceBudget":
        """Return default budget per architecture §4.3."""
        if role is AgentRole.PRODUCER:
            return cls(
                max_tokens=200_000,
                max_wall_seconds=600.0,
                max_tool_calls=100,
                max_memory_writes=50,
            )
        if role is AgentRole.REVIEWER:
            return cls(
                max_tokens=100_000,
                max_wall_seconds=300.0,
                max_tool_calls=40,
                max_memory_writes=20,
            )
        raise ValueError(f"Unknown role: {role!r}")

    def check_tokens(self, consumed: int) -> None:
        """Raise BudgetExceededError if token consumption exceeds ceiling."""
        if consumed > self.max_tokens:
            raise BudgetExceededError(
                f"Token budget exceeded: {consumed} > {self.max_tokens} max_tokens"
            )

    def check_tool_calls(self, consumed: int) -> None:
        """Raise BudgetExceededError if tool-call count exceeds ceiling."""
        if consumed > self.max_tool_calls:
            raise BudgetExceededError(
                f"Tool-call budget exceeded: {consumed} > {self.max_tool_calls} max_tool_calls"
            )

    def check_memory_writes(self, consumed: int) -> None:
        """Raise BudgetExceededError if memory-write count exceeds ceiling."""
        if consumed > self.max_memory_writes:
            raise BudgetExceededError(
                f"Memory-write budget exceeded: {consumed} > {self.max_memory_writes}"
            )


__all__ = ["ResourceBudget", "BudgetExceededError"]
