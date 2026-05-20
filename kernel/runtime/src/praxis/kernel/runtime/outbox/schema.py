"""Re-exports from Pi-Mono's schema for use across the outbox package.

Runtime uses Pi-Mono's EventRow directly — no parallel events_outbox table.
Architecture §8.1: 'Pi-Mono's outbox pattern is the canonical emission path.'

EventRow.event_id (PK) serves as the dedup key for idempotency.
See path_a.py and path_b.py for how dedup keys are generated.
"""

from __future__ import annotations

from praxis.kernel.cost.storage.schema import EventRow

__all__ = ["EventRow"]
