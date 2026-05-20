"""Audit event stub for Phase 3C facade composition.

Minimum-viable implementation: an in-process `AuditBuffer` that
collects `AuditEvent` records at facade entry points for write, delete,
export, and quarantine operations.

PII / scoping rules (§8.4, Req #33)
-----------------------------------

- NEVER store raw query strings, raw criteria dicts, or raw fact text.
- Store the method name, the tenant_hash, the operation outcome, and
  salted hashes of any criteria. The facade passes pre-hashed values
  here — the buffer does not hash on its own.
- The `allowed_payload_keys` constraint on `AuditEvent` enforces the
  allowlist at construction time so callers cannot silently add free
  fields.

Stage 7 durable sink
--------------------

Phase 3C ships an in-memory buffer. Stage 7 wires a durable sink
(Postgres audit table + forwarder to the central SIEM). The test surface
asserts the buffer receives events with the correct shape — that is
enough to prove the facade wiring is correct.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from threading import Lock

from pydantic import BaseModel, ConfigDict


class AuditEventType(str, Enum):
    """Facade-level operations worth recording."""

    STORE_TASK_OUTCOME = "store_task_outcome"
    STORE_DECISION = "store_decision"
    STORE_FACT = "store_fact"
    DELETE = "delete"
    EXPORT = "export"
    QUARANTINE = "quarantine"


class AuditEvent(BaseModel):
    """Structured audit-log line.

    Fields are restricted to a known allowlist by `extra="forbid"` +
    `strict=True`. New fields require a schema bump and a test update.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    event_type: AuditEventType
    tenant_hash: str
    method: str
    """The facade method the caller invoked. Duplicates event_type for
    callers that want a more readable form, e.g., "store_decision"."""
    created_at: datetime
    criteria_hash: str | None = None
    """Salted sha256 of any delete/export criteria. Never the raw criteria."""
    entry_id: str | None = None
    """For single-entry operations (quarantine, store)."""
    outcome: str = "ok"
    """Short string — "ok", "error", "rejected". Never a raw error message."""


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class AuditBuffer:
    """In-process audit sink.

    Thread-safe via a simple lock — parallel agents within one process
    serialize on append. Stage 7 swaps this for a durable sink without
    changing the facade call sites.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = Lock()

    def append(self, event: AuditEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events(self) -> list[AuditEvent]:
        """Return a snapshot copy — callers cannot mutate the buffer."""
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        return len(self._events)


__all__ = ["AuditBuffer", "AuditEvent", "AuditEventType", "_utc_now"]
