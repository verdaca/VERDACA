"""Path B — tick-drain loop: Memory.audit_buffer → Pi-Mono events_outbox.

Architecture §8.1.5: at-least-once delivery with dedup via event_id (PK).

OQ-N Path (i) — position-based shim:
  The Orchestrator maintains a _drained_count high-water mark.  Each tick:
  1. Snapshot buffer.events() (full list)
  2. Skip first _drained_count events (already drained)
  3. Drain remainder via batch INSERT to events_outbox
  4. On commit success, advance _drained_count

  No compaction: clear() races with concurrent append.  50 MB per-tenant
  per-lifetime ceiling is tolerable under NFR-Q2 (100K entries × ≈500 B).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from praxis.kernel.memory._internal.audit import AuditBuffer, AuditEvent

_log = logging.getLogger(__name__)


class PositionBasedDrainAdapter:
    """OQ-N Path (i) DrainAdapter implementation.

    Wraps an AuditBuffer with a position-based high-water mark.
    Thread-safety: snapshot_undrained() and mark_drained() are called
    ONLY from the single asyncio tick-drain task.  AuditBuffer's
    internal lock guards append() calls from concurrent threads.

    Architecture §12 OQ-N: position-based shim against AuditBuffer's
    public API (append / events / clear / __len__).  Zero memory/src/ edits.
    """

    def __init__(self, buffer: "AuditBuffer") -> None:
        self._buffer = buffer
        self._drained_count: int = 0

    @property
    def buffer(self) -> "AuditBuffer":
        """Public accessor so tests can append events directly."""
        return self._buffer

    def snapshot_undrained(self) -> list["AuditEvent"]:
        """Return events after the current high-water mark (not yet drained)."""
        all_events = self._buffer.events()  # snapshot copy under AuditBuffer lock
        return all_events[self._drained_count :]

    def mark_drained(self, count: int) -> None:
        """Advance the high-water mark by *count* after a successful commit."""
        self._drained_count += count

    def undrained_count(self) -> int:
        """Number of events not yet drained.  For monitoring."""
        return len(self._buffer) - self._drained_count


__all__ = ["PositionBasedDrainAdapter"]
