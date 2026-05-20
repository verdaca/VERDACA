"""FakeCostTracker — records Pi-Mono label emissions without side effects.

Assertable via emitted_labels() and emitted_cost(label).

Binding: studio/test-strategy.md §14.1.
"""

from __future__ import annotations

from collections import defaultdict


class FakeCostTracker:
    """Test double for Pi-Mono CostTracker.

    Records track_cost calls; assertable in tests without touching Pi-Mono.
    """

    def __init__(self) -> None:
        self._calls: list[tuple[str, float]] = []
        self._by_label: dict[str, list[float]] = defaultdict(list)

    def track_cost(self, label: str, amount_usd: float) -> None:
        self._calls.append((label, amount_usd))
        self._by_label[label].append(amount_usd)

    def emitted_labels(self) -> list[str]:
        """Return all label strings that were emitted (in order)."""
        return [label for label, _ in self._calls]

    def emitted_cost(self, label: str) -> float:
        """Sum of amounts emitted under this label."""
        return sum(self._by_label.get(label, []))

    def all_calls(self) -> list[tuple[str, float]]:
        return list(self._calls)

    def reset(self) -> None:
        self._calls.clear()
        self._by_label.clear()
