"""FrozenClock fake — test-strategy v0.3 §14.3.3 frozen interface contract.

Transcribed verbatim from the ratified test-strategy interface contract.
Do NOT add logic here beyond ``now()`` / ``advance()``. Extensions go in
a wrapper, not in the base class.

Binding anchor:
  - mac/test-strategy.md v0.3 §14.3.3 FrozenClock (frozen interface)
"""

from __future__ import annotations

from datetime import datetime, timedelta


class FrozenClock:
    """Injectable clock for ``wall_clock`` tests. Replaces ``datetime.utcnow()``.

    Advance is explicit — the clock never moves unless the test calls
    :meth:`advance`. Used by the Deterministic Replay Pattern at §4.5 to
    synchronize virtual time across parallel reviewer submissions.
    """

    def __init__(self, initial: datetime) -> None:
        self._now = initial

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int) -> None:
        self._now += timedelta(seconds=seconds)


__all__ = ("FrozenClock",)
