"""MAC ResourceBudget defaults — arch §5.7.

The MAC inherits :class:`ResourceBudget` semantics from Runtime §4.3. At
step 3 we do NOT import the real Runtime ResourceBudget type — that would
couple MAC startup to the full Runtime package and its transitive
dependencies. Instead we define a shape-compatible local :class:`ResourceBudget`
frozen model that step 6 (or a later integration pass) can rebind to the
Runtime facade once the full monorepo wiring is available.

The :class:`BudgetExceededError` raised at boundary checks is a local
exception matching the Runtime error by name and message shape, so
callers that catch it do not need to switch exception class when the
rebind lands.

Binding anchors:
  - mac/architecture.md §5.7 ResourceBudget Defaults
  - runtime/architecture.md §4.3 ResourceBudget (semantic contract)
  - mac/test-strategy.md v0.3 §4.3 MAC-T-CYCLE-BUDGET-01..03
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BudgetExceededError(Exception):
    """Raised at cycle boundaries when a :class:`ResourceBudget` dimension
    exceeds its ceiling.

    Shape-compatible with ``praxis.kernel.runtime.spawner.budgets.BudgetExceededError``
    so MAC test fixtures can interchange the two. The Iteration Controller
    catches this at the phase-runner boundary and transitions to
    :attr:`State.FAILED` per arch §5.2 footnote.
    """


class ResourceBudget(BaseModel):
    """Per-deliberation resource ceiling (arch §5.7).

    Defaults match arch §5.7 ``DEFAULT_MAC_BUDGET``:

      - ``max_tokens=400_000`` — 2× producer + 2× reviewer + gate eval overhead
      - ``max_wall_seconds=900.0`` — 15 min worst-case for 3-cycle + 1 backtrack
      - ``max_tool_calls=200`` — generous for retrieval + memory writes
      - ``max_memory_writes=100`` — tentative + confirmed × 3 cycles + backtrack
    """

    model_config = ConfigDict(frozen=True)

    max_tokens: int = Field(default=400_000, gt=0)
    max_wall_seconds: float = Field(default=900.0, gt=0.0)
    max_tool_calls: int = Field(default=200, gt=0)
    max_memory_writes: int = Field(default=100, gt=0)

    def check_tokens(self, consumed_tokens: int) -> None:
        """Raise :class:`BudgetExceededError` if consumption exceeds ceiling."""
        if consumed_tokens > self.max_tokens:
            raise BudgetExceededError(
                f"token budget exceeded: consumed={consumed_tokens} > max={self.max_tokens}"
            )

    def check_wall_seconds(self, elapsed_seconds: float) -> None:
        """Raise :class:`BudgetExceededError` if elapsed wall time exceeds ceiling."""
        if elapsed_seconds > self.max_wall_seconds:
            raise BudgetExceededError(
                f"wall-clock budget exceeded: elapsed={elapsed_seconds:.2f}s "
                f"> max={self.max_wall_seconds:.2f}s"
            )

    def check_tool_calls(self, invoked: int) -> None:
        """Raise :class:`BudgetExceededError` if tool-call count exceeds ceiling."""
        if invoked > self.max_tool_calls:
            raise BudgetExceededError(
                f"tool-call budget exceeded: invoked={invoked} > max={self.max_tool_calls}"
            )

    def check_memory_writes(self, writes: int) -> None:
        """Raise :class:`BudgetExceededError` if memory-write count exceeds ceiling."""
        if writes > self.max_memory_writes:
            raise BudgetExceededError(
                f"memory-write budget exceeded: writes={writes} > max={self.max_memory_writes}"
            )


DEFAULT_MAC_BUDGET: ResourceBudget = ResourceBudget()
"""Arch §5.7 default budget for the MAC role. Used by
:class:`MetaAgentController.deliberate` when the caller passes
``budget=None``."""


__all__: tuple[str, ...] = (
    "BudgetExceededError",
    "DEFAULT_MAC_BUDGET",
    "ResourceBudget",
)
