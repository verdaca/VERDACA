"""Cost Meter Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2.2 §3 / ADR-9.1.2-5.
Vendor strategy: `ports-architecture.md` §3 ADR-9.2-V4 (Pi-Mono = in-tree-
native; Python rewrite of MIT-licensed Pi-Mono pricing math; no submodule,
no TS bridge per Stage 9.2 ratification).

This module introduces zero new contract substance. Pure Python, no
upstream imports.

API_VERSION = "1.0.0" (initial version; first stable contract surface).

§3.6 Result + Query DTOs (`CostQuery`, `CostReport`) are pinned per the
Phase A.1 corrigendum at SHA `b0c333c`; the
A.1 commit body is the authoritative substance-of-record per the
`_bmad-output/implementation-artifacts/` gitignore caveat at .gitignore:30.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

8 binding MAC-Ts at `test-strategy.md` Cost-meter section (Murat §4):
    record / query happy paths + budget thresholds + ParityDrift +
    PricingTableMismatch error paths. Cost-meter has ZERO no_waiver
    allow-list entries per advisor §3.1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Literal, Protocol, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    VerdacaDTOMixin,
)


# ---------------------------------------------------------------------------
# DTOs — pinned per ADR-9.1.2-5 §3 (port-contracts.md v0.2.2)
#   §3 base DTOs (5): BudgetScope, CostEvent, CostBreakdown,
#                     CostLedgerEntry, BudgetStatus
#   §3.6 result/query DTOs (2 new at v0.2.2):
#                     CostQuery, CostReport
# ---------------------------------------------------------------------------


class BudgetScope(VerdacaDTOMixin):
    """Aggregation discriminator for cost records and budget queries.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3. `scope_kind` Literal
    enforces the three valid aggregation levels; `scope_id` is the
    caller-supplied identifier within that kind.
    """

    scope_kind: Literal["session", "user", "workspace"]
    scope_id: str


class CostEvent(VerdacaDTOMixin):
    """Single LLM invocation cost record submitted to the meter.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3. `provider` is the
    upstream label (e.g., "anthropic", "openai"); `scope` discriminates
    aggregation level (session | user | workspace) per BudgetScope.
    """

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    occurred_at: datetime
    scope: BudgetScope


class CostBreakdown(VerdacaDTOMixin):
    """Itemized USD cost split by token direction.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3. `pricing_table_version`
    pins the in-tree pricing math snapshot used for this breakdown;
    aggregated by CostReport.pricing_table_versions for parity audit
    (§3.4 ParityDrift). Decimal not float per §4 Pi-Mono stakeholder
    precedent (Stage 5.3 Decimal precedent).
    """

    input_cost_usd: Decimal
    output_cost_usd: Decimal
    pricing_table_version: str


class CostLedgerEntry(VerdacaDTOMixin):
    """Persisted ledger record for a single CostEvent recording.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3. Return DTO for
    `record()`. `ledger_id` is a ULID; `cost_breakdown` carries the
    itemized split per pricing-table snapshot. Decimal not float per §4
    Pi-Mono stakeholder precedent.
    """

    ledger_id: str
    cost_usd: Decimal
    cost_breakdown: CostBreakdown
    written_at: datetime


class BudgetStatus(VerdacaDTOMixin):
    """Current consumption + remaining budget snapshot for a scope.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3. Return DTO for
    `budget_check()`. `limit_usd` and `remaining_usd` are None when no
    budget cap is configured; `status` triple ("ok" | "warning" |
    "exceeded") drives caller back-pressure decisions.
    """

    scope: BudgetScope
    consumed_usd: Decimal
    limit_usd: Decimal | None
    remaining_usd: Decimal | None
    status: Literal["ok", "warning", "exceeded"]


class CostQuery(VerdacaDTOMixin):
    """Parameter DTO for `CostMeterPort.query`; scope-shaped query envelope.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3.6.
    """

    scope: BudgetScope                  # method-sig echo from query(q: CostQuery, ...)
                                        # cross-port sibling: MemoryQuery scope-shaped
                                        # per M-T-COST-QUERY-01 trigger: CostQuery(scope)


class CostReport(VerdacaDTOMixin):
    """Return DTO for `CostMeterPort.query`; aggregate of records + audit-trail.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3.6.
    """

    entries: list[CostLedgerEntry]      # source-pin §3 method-sig: query() returns
                                        # aggregate of records; cross-port sibling:
                                        # MigrationReport multi-field aggregate pattern
    total_usd: Decimal                  # source-pin M-T-COST-QUERY-01: "aggregated
                                        # Decimal sum matches sum-of-records"; NOT float
                                        # per §4 Pi-Mono stakeholder precedent
    query: CostQuery                    # JUDGMENT — self-describing echo; cross-port
                                        # sibling: MigrationReport.migrator_signature
                                        # self-pin pattern
    pricing_table_versions: list[str]   # JUDGMENT — audit-trail for parity verification;
                                        # plural aggregate of CostBreakdown.pricing_table_
                                        # version (singular) across all queried records


# ---------------------------------------------------------------------------
# Error specializations — verbatim per ADR-9.1.2-5 §3.4
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class PricingTableMismatch(ContractViolation):
    """CostEvent's (provider, model) not found in pricing table.

    Indicates upstream model release that the in-tree pricing table hasn't
    tracked yet. Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3.4: raised
    by `record()` when the in-tree pricing table cannot resolve the
    (provider, model) pair. Cost-meter has zero no_waiver allow-list
    entries (advisor §3.1); contract-test enforcement is gate-only.
    """

    provider: str
    model: str
    pricing_table_version: str


@dataclass(kw_only=True)
class ParityDrift(ContractViolation):
    """In-tree pricing math diverged from snapshot reference.

    The snapshot reference is the original TS pricing math (MIT-licensed
    Pi-Mono source per Sophia §4 attribution). Surfaced by parity test,
    not normal operation. Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §3.4:
    snapshot fixture gates Cleo §4 round-table approval. Cost-meter has
    zero no_waiver allow-list entries (advisor §3.1); contract-test
    enforcement is gate-only.
    """

    snapshot_hash: str
    current_hash: str


# ---------------------------------------------------------------------------
# Protocol surface — verbatim per ADR-9.1.2-5 §3 method signatures
# ---------------------------------------------------------------------------


@runtime_checkable
class CostMeterPort(Protocol):
    """In-tree cost meter — Pi-Mono pricing math + ledger storage.

    Per `port-contracts.md` v0.2.2 ADR-9.1.2-5 §1 design intent: pricing
    table + pricing math are Verdaca-owned (in-tree, no upstream); ledger
    storage is adapter-pluggable (in-tree default; SQL/Stripe deferred to
    Stage 10). Substitute-readiness N/A — Cost Meter is in-tree per
    `port-contracts.md` §3.5 / ADR-9.2-V4 (Stage 9.2 ratification).

    Async / streaming / idempotency profile (ADR-9.1.2-5 §3.1):
        record         — sync, idempotent (idempotency_key required —
                         replay-storm safety)
        query          — sync, idempotent
        budget_check   — sync, idempotent

    `@runtime_checkable` decoration follows the 9.4.1 `VersionedStatePort` +
    9.4.2 `SerializationPort` + 9.4.3 `MemoryPort` precedent. Adapter
    `on_init()` performs `isinstance(self, CostMeterPort)` self-check per
    executor playbook §9.C addendum (substrate API surface verified per F7
    precedent — structural Protocol matching, NOT nominal inheritance).
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def record(self, event: CostEvent) -> CostLedgerEntry: ...

    def query(self, q: CostQuery) -> CostReport: ...

    def budget_check(self, scope: BudgetScope) -> BudgetStatus: ...


__all__ = [
    "API_VERSION",
    "BudgetScope",
    "BudgetStatus",
    "CostBreakdown",
    "CostEvent",
    "CostLedgerEntry",
    "CostMeterPort",
    "CostQuery",
    "CostReport",
    "ParityDrift",
    "PricingTableMismatch",
]


API_VERSION: str = CostMeterPort.API_VERSION
