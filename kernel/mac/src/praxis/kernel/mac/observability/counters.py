"""MAC process-level counters — arch §11.2 metric catalog (gauge/counter subset).

At step 4 we implement only the one counter the SQ-2 registry discipline
requires: ``mac.label_registry.violations``. Step 6 extends to the full
arch §11.2 metric catalog.

The counter is a process-wide in-memory integer — simple but sufficient
for the S-Q2 unit tests that assert ``count == 1`` after a single
violation. :class:`ResetCounterFixture` in
``tests/mac/observability/conftest.py`` calls :meth:`MacCounters.reset`
between tests via ``autouse=True``.

Binding anchors:
  - mac/architecture.md §11.2 Metric Catalog
  - mac/test-strategy.md v0.3 §9.3 Violation Counter (S-Q2 bake-in)
"""

from __future__ import annotations

from typing import ClassVar


class MacCounters:
    """Process-level counter registry.

    Counters are module-global integers keyed by metric name. Not
    thread-safe — at step 4 we don't need it; step 6+ may wrap in a
    ``threading.Lock`` when the production outbox pipeline is wired.
    """

    _counts: ClassVar[dict[str, int]] = {}

    @classmethod
    def increment(cls, metric_name: str, amount: int = 1) -> None:
        cls._counts[metric_name] = cls._counts.get(metric_name, 0) + amount

    @classmethod
    def get(cls, metric_name: str) -> int:
        return cls._counts.get(metric_name, 0)

    @classmethod
    def reset(cls, metric_name: str) -> None:
        cls._counts[metric_name] = 0

    @classmethod
    def reset_all(cls) -> None:
        cls._counts.clear()


__all__ = ("MacCounters",)
