"""Fake memory proxies for asymmetry tests — arch §7.2 + runtime §4.1.

These fakes model the Runtime ``ProducerMemoryProxy`` and
``ReviewerMemoryProxy`` shapes at the attribute-existence level only.
They exist so MAC asymmetry tests can verify the structural invariant:

  - :class:`FakeProducerProxy` has ``retrieve_similar_tasks``,
    ``store_task_outcome``, and ``store_decision`` — full R/W access.
  - :class:`FakeReviewerProxy` has ``store_decision`` and
    ``flag_and_quarantine`` but NO ``retrieve_similar_tasks``. Calling
    the missing method raises ``AttributeError`` at the Python
    interpreter level — this is arch §9.0 "the punchline" inherited
    verbatim from Runtime.

MAC code NEVER imports these from ``praxis.kernel.runtime.spawner`` —
the real proxies are constructed by Runtime's
``_construct_memory_proxy`` at ``AgentSpawner.spawn`` time. These
fakes are MAC-local test doubles with the SAME structural contract.

Binding anchors:
  - mac/architecture.md §7.2 Binding to Runtime §4.1 Proxies
  - mac/architecture.md §7.3 Information Hiding (what reviewer sees/doesn't)
  - runtime/architecture.md §4.1.3 ReviewerMemoryProxy attribute set
  - runtime/architecture.md §9.0 "the punchline" (AttributeError)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeProducerProxy:
    """Full R/W memory proxy for a producer agent.

    Mirrors the runtime ``ProducerMemoryProxy`` attribute set:
    ``retrieve_similar_tasks``, ``store_task_outcome``, ``store_decision``.
    All calls are captured in :attr:`call_log`.
    """

    call_log: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    def retrieve_similar_tasks(self, *args: Any, **kwargs: Any) -> Any:
        self.call_log.append(("retrieve_similar_tasks", args))
        return []

    def store_task_outcome(self, *args: Any, **kwargs: Any) -> Any:
        self.call_log.append(("store_task_outcome", args))
        return None

    def store_decision(self, *args: Any, **kwargs: Any) -> Any:
        self.call_log.append(("store_decision", args))
        return None


@dataclass
class FakeReviewerProxy:
    """Write-only memory proxy for a reviewer agent.

    Mirrors the runtime ``ReviewerMemoryProxy`` attribute set: ONLY
    ``store_decision`` and ``flag_and_quarantine`` — no
    ``retrieve_similar_tasks``, no ``store_task_outcome``.

    Attempting to call ``retrieve_similar_tasks`` on an instance
    raises ``AttributeError`` at the Python interpreter level (the
    attribute simply does not exist on the class). This is the arch
    §9.0 "punchline" — no allowlist exception, no fallback, no
    "trusted reviewer" mode.
    """

    call_log: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    def store_decision(self, *args: Any, **kwargs: Any) -> Any:
        self.call_log.append(("store_decision", args))
        return None

    def flag_and_quarantine(self, *args: Any, **kwargs: Any) -> Any:
        self.call_log.append(("flag_and_quarantine", args))
        return None

    # NOTE: retrieve_similar_tasks deliberately absent.
    # Accessing it on an instance raises AttributeError.


__all__ = (
    "FakeProducerProxy",
    "FakeReviewerProxy",
)
