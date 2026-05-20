"""Claim token management for jobs_queue worker fencing.

Architecture §4.2.4: claim_token (UUID) + claim_expires_at = claimed_at + 5 min.
On worker crash, expired claims are reclaimed by the new worker process.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

_CLAIM_DURATION_SECONDS = 300  # NFR-Q6: 5-minute claim window


def new_claim_token() -> str:
    """Generate a fresh UUID4 claim token."""
    return str(uuid.uuid4())


def claim_expires_at(claimed_at: datetime | None = None) -> datetime:
    """Calculate claim_expires_at = claimed_at + 5 minutes."""
    base = claimed_at or datetime.now(timezone.utc)
    return base + timedelta(seconds=_CLAIM_DURATION_SECONDS)


__all__ = ["new_claim_token", "claim_expires_at", "_CLAIM_DURATION_SECONDS"]
