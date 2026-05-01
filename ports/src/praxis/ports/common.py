"""Shared error taxonomy + DTO mixin + payload base for all six ports.

Substance source: `port-contracts.md` v0.2 §0 Cross-Cutting Conventions.
This module is inherited verbatim by every port; it introduces no new
contract substance beyond §0.

§0.1 Base Error Hierarchy — five base classes; adapters MUST raise subclasses
                            (per-port specializations live in each port file).
§0.2 Shared DTO Conventions — VerdacaDTOMixin with frozen + extra="forbid".
§0.3 Deprecation Policy — schema_version on DTOs + API_VERSION on Protocols.
                          Mechanics: see `ports-architecture.md` §6 for the
                          version-bump rules; no executable deprecation
                          machinery lives at this layer.
§0.4 OTEL Trace Context — correlation_id on every DTO; spans named
                          verdaca.port.<port>.<method>.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# §0.1 Base Error Hierarchy
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class VerdacaPortError(Exception):
    """Root of all port-layer exceptions.

    Adapters MUST raise subclasses, never the base directly.
    """

    port_name: str
    correlation_id: str
    occurred_at: datetime
    upstream_name: str | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, f"[{self.port_name}] {type(self).__name__}")


@dataclass(kw_only=True)
class TransientError(VerdacaPortError):
    """Retryable. Caller MAY retry with backoff. Adapter MUST NOT retry internally."""

    retry_after_seconds: float | None = None


@dataclass(kw_only=True)
class ContractViolation(VerdacaPortError):
    """Adapter returned a value the Protocol forbids.

    Non-retryable. Indicates upstream drift — surface to alignment-review
    immediately. Always blocks PR gates.
    """

    violation_class: Literal["type", "value", "invariant", "ordering"]


@dataclass(kw_only=True)
class UpstreamUnavailable(VerdacaPortError):
    """Upstream system unreachable / sidecar down / submodule missing.

    Distinct from TransientError: caller decision is graceful degradation,
    not retry.
    """

    last_known_health: datetime | None = None


@dataclass(kw_only=True)
class BudgetExceeded(VerdacaPortError):
    """Cost or token budget hit.

    Surfaced from Cost Meter port primarily; other ports raise this when
    their own budget guards trigger (e.g., Memory storage budget).
    """

    budget_type: Literal["cost_usd", "tokens", "storage_bytes", "wall_seconds"]
    actual: float
    limit: float


@dataclass(kw_only=True)
class IdempotencyViolation(VerdacaPortError):
    """Idempotency key was reused with non-equivalent payload.

    Indicates caller bug OR replay-storm. Adapter MUST NOT retry; caller
    MUST reconcile.
    """

    idempotency_key: str
    prior_call_at: datetime


# ---------------------------------------------------------------------------
# §0.2 Shared DTO Mixin
# ---------------------------------------------------------------------------


class VerdacaDTOMixin(BaseModel):
    """Base for every Pydantic DTO crossing a port boundary.

    `extra="forbid"` is the structural enforcement of "no upstream-specific
    behavior leaks through the port" — if Mem0 (or any upstream) returns a
    field Verdaca didn't ask for, the DTO rejects it; the adapter must
    explicitly pick what to expose.
    """

    schema_version: int
    correlation_id: str
    idempotency_key: str | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# 9.4.2 — Serialization port landed (ADR-9.2-V2 v0.2 corrigendum 2026-04-28).
# `SerializablePayload` placeholder retired; canonical home is now
# `praxis.ports.serialization.SerializablePayload` per port-contracts.md
# v0.2 §2.3. Per 9.4.2 Finding A disposition (A.2 — 4-file consumer
# rewire, NOT PEP-562 lazy re-export), `common.py` does NOT re-export
# `SerializablePayload`. Consumers (Versioned State port, Migrator
# Protocol, Beads adapter, VS contract tests) import from
# `praxis.ports.serialization` directly. Rationale:
#     - `common.py` ↔ `serialization.py` re-export creates an import cycle
#       that is fragile depending on which module is imported first.
#     - Mechanical 4-file rewire is grep-driven and Cleo-9.6-friendly.
#     - The 9.4.1 placeholder comment's "single-grep-target rewire"
#       wishful intent did not survive Python import semantics.
# Substance source: port-contracts.md v0.2 §2 / ADR-9.1.2-2.
# ---------------------------------------------------------------------------
