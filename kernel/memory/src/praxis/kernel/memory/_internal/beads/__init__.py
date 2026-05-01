"""Beads — content-addressed audit trail (§3 of architecture.md).

Pattern extraction on top of Postgres (re-implemented from the Go Beads
project per Winston's §3.6 port plan). NOT a literal port.

What lives here:
    - `models.py`        — Bead, BeadOperationType, BeadPayload types
    - `content_hash.py`  — canonical serialization + sha256 addressing
    - `store.py`         — BeadsStore: append-only store + MemoryProtocol

Patterns kept from Beads (ref §1.1 of architecture):
    B1 — hash-based IDs prevent merge conflicts
    B2 — auto-commit per mutation (via Pi-Mono outbox in prod)
    B7 — content-hash comparison for sync
    plus B3/B4/B5 which are retention/ops concerns (deferred past 3B-i)

Patterns dropped: Dolt storage, cell-level 3-way merge, git integration,
issue-tracker semantics, server mode. See §1.1 of architecture for rationale.
"""

__all__: list[str] = []
