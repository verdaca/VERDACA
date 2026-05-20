"""Pi-Mono native adapter — Cost Meter port implementation.

Per ADR-9.2-V4 (`ports-architecture.md` v0.3 §3): in-tree Python
reimplementation of Pi-Mono pricing math. FIRST in-tree-native adapter
in the repo (no upstream package; no submodule; no TS bridge per Stage
9.2 ratification).

ADR rationale (per Q-9.4.4-3 (β) adapter-side disposition): NOT to bridge
TS because (a) Node/Python bridge adds a process boundary for what is
pure math, (b) pricing tables drift at a pace a monthly workflow catches,
(c) the ~200 LOC surface is small enough to own fully. TS source archived
as informational reference at dump-file fragment `8a5edab282632443`.

Substance source: `port-contracts.md` v0.2.2 §3 ADR-9.1.2-5 + §3.6
(CostQuery + CostReport per A.1 corrigendum at b0c333c).

v0.1.0 scope (per Q-9.4.4-* + S1-S12 advisor lock):
    - input + output token costs ONLY (S3: cacheRead/cacheWrite deferred
      to Stage 10; port contract has only 2 cost components)
    - service-tier multiplier defaults to 1.0 (S4: flex/priority deferred
      to Stage 10; CostEvent does not model service_tier)
    - Decimal arithmetic throughout (Q-9.4.4-5 amended: Decimal exact,
      formula-parity NOT byte-parity vs TS source per S2)
    - Pricing table = hardcoded dict in this module (S5)
    - pricing_table_version = sha256(canonical JSON)[:12] (S6)
    - Idempotency = in-process dict (S11; durability across restart N/A
      per in-tree posture; caller-retry with same idempotency_key after
      restart produces fresh CostLedgerEntry — accepted at v0.1.0 since
      pricing math is deterministic)

Lifecycle (per `ports-architecture.md` v0.3 §2.2):
    on_init   — isinstance self-check (no upstream healthcheck — in-tree;
                no AP-5 reconciliation — in-process idempotency dict)
    on_shutdown — no-op (no upstream connections; no fsync — in-tree)

Idempotency profile (per ADR-9.1.2-5 §3.1):
    record       — sync, idempotent (idempotency_key required for
                   replay-storm safety; in-process dict dedup)
    query        — sync, idempotent (read-only ledger scan)
    budget_check — sync, idempotent (read-only ledger aggregation)

Error specializations (per ADR-9.1.2-5 §3.4):
    PricingTableMismatch — raised by record() when (provider, model)
                           not in PRICING_TABLE
    ParityDrift          — raised by parity test (M-T-COST-PARITY-01;
                           NOT normal operation)

8 binding MAC-Ts at `test-strategy.md` v0.2 §2.2.5: M-T-COST-RECORD-01 /
QUERY-01 / BUDGET-OK-01 / BUDGET-EXCEEDED-01 / PARITY-01 /
PRICING-MISMATCH-01 / IDEMPOTENT-01 / SCOPE-01. ZERO `no_waiver`
allow-list entries (advisor §3.1).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar

from praxis.ports.common import ContractViolation
from praxis.ports.cost_meter import (
    BudgetScope,
    BudgetStatus,
    CostBreakdown,
    CostEvent,
    CostLedgerEntry,
    CostMeterPort,
    CostQuery,
    CostReport,
    PricingTableMismatch,
)

from praxis.adapters.pi_mono_native.version_pin import UPSTREAM_NAME

_PORT_NAME = "cost_meter"


# ---------------------------------------------------------------------------
# Pricing table — hardcoded per S5 disposition.
# Prices in USD per 1,000,000 tokens (matches Pi-Mono TS convention:
# `cost.input / 1000000 * tokens` at models.ts:9692). Cache + service tier
# components deferred to Stage 10 per S3 + S4 dispositions.
# ---------------------------------------------------------------------------


PRICING_TABLE: dict[tuple[str, str], dict[str, Decimal]] = {
    ("anthropic", "claude-opus-4-7"):    {"input": Decimal("15"),    "output": Decimal("75")},
    ("anthropic", "claude-opus-4-6"):    {"input": Decimal("5"),     "output": Decimal("25")},
    ("anthropic", "claude-sonnet-4-6"):  {"input": Decimal("3"),     "output": Decimal("15")},
    ("anthropic", "claude-haiku-4-5"):   {"input": Decimal("0.80"),  "output": Decimal("4")},
    ("openai", "gpt-5-chat-latest"):     {"input": Decimal("1.25"),  "output": Decimal("10")},
    ("openai", "gpt-4o"):                {"input": Decimal("2.50"),  "output": Decimal("10")},
    ("google", "gemini-2.0-flash"):      {"input": Decimal("0.10"),  "output": Decimal("0.40")},
    ("google", "gemini-1.5-pro"):        {"input": Decimal("1.25"),  "output": Decimal("5")},
}


def _canonical_pricing_table_hash() -> str:
    """sha256(canonical JSON)[:12] per S6 disposition.

    Decimals serialized as strings to preserve precision in canonical
    form. Computed once at module import; static for the table lifetime.
    Truncated to 12-char prefix per advisor amendment (sufficient for
    audit-trail; avoids 64-char hash in DTOs).
    """
    canonical = json.dumps(
        {
            f"{p}:{m}": {k: str(v) for k, v in costs.items()}
            for (p, m), costs in PRICING_TABLE.items()
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


PRICING_TABLE_VERSION: str = _canonical_pricing_table_hash()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _scope_key(scope: BudgetScope) -> str:
    """Adapter-internal scope identifier per S8 disposition.

    Format: f"{scope_kind}:{scope_id}". Used for ledger partitioning
    + budget_limits dict lookup.
    """
    return f"{scope.scope_kind}:{scope.scope_id}"


# ---------------------------------------------------------------------------
# Pi-Mono native adapter
# ---------------------------------------------------------------------------


class PiMonoNativeAdapter:
    """In-tree Python rewrite of Pi-Mono pricing math against `CostMeterPort`.

    Conforms to `praxis.ports.cost_meter.CostMeterPort` (verify via
    `isinstance(adapter, CostMeterPort)`; the Protocol is `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the attribute,
    # isinstance checks the candidate has it. Per 9.4.1 Beads close-memo §4.1
    # API_VERSION ClassVar lesson.
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        budget_limits: dict[str, Decimal] | None = None,
        warning_threshold_fraction: float = 0.8,
        default_correlation_id: str | None = None,
    ) -> None:
        """Construct an adapter.

        `budget_limits` per S8: `dict[scope_key, limit_usd]` where
        `scope_key = f"{scope_kind}:{scope_id}"`. None or missing key →
        no limit (BudgetStatus.limit_usd = None at budget_check).

        `warning_threshold_fraction` per S7: status="warning" when
        `consumed_usd >= warning_threshold_fraction * limit_usd` (default
        0.8 = 80% of limit).

        `default_correlation_id` per BeadsAdapter sibling precedent.
        """
        self._budget_limits = dict(budget_limits or {})
        self._warning_threshold = warning_threshold_fraction
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        self._ledger: dict[str, list[CostLedgerEntry]] = {}
        self._idempotency_cache: dict[str, CostLedgerEntry] = {}

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.3 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check.

        In-tree-native sibling precedent (Beads): no upstream healthcheck
        (no upstream); no AP-5 reconciliation (no sidecar; in-process
        idempotency dict). Self-check verifies `isinstance` conformance
        per executor playbook §9.C addendum.
        """
        if not isinstance(self, CostMeterPort):
            raise RuntimeError(
                "PiMonoNativeAdapter does not conform to CostMeterPort"
            )

    def on_shutdown(self) -> None:
        """Lifecycle: no-op.

        In-tree-native posture: no upstream connections, no fsync needed
        (durability across restart N/A per S11).
        """

    # ------------------------------------------------------------------
    # CostMeterPort surface (3 methods)
    # ------------------------------------------------------------------

    def record(self, event: CostEvent) -> CostLedgerEntry:
        """Per `port-contracts.md` v0.2.2 §3 record() + §3.1 idempotency
        profile (idempotency_key required — replay-storm safety).

        Pricing math: Decimal((price_per_M / 1_000_000) * tokens) per
        Q-9.4.4-5 amended (Decimal exact, formula-parity). Matches TS
        formula at models.ts:9692 re-expressed in Decimal arithmetic.
        cacheRead + cacheWrite deferred to Stage 10 per S3; service-tier
        multiplier defaults to 1.0 per S4.
        """
        if event.idempotency_key is None:
            raise ContractViolation(
                port_name=_PORT_NAME,
                correlation_id=event.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
            )

        cached = self._idempotency_cache.get(event.idempotency_key)
        if cached is not None:
            return cached

        pricing = PRICING_TABLE.get((event.provider, event.model))
        if pricing is None:
            raise PricingTableMismatch(
                port_name=_PORT_NAME,
                correlation_id=event.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                provider=event.provider,
                model=event.model,
                pricing_table_version=PRICING_TABLE_VERSION,
            )

        breakdown = self._compute_breakdown(event, pricing)
        cost_usd = breakdown.input_cost_usd + breakdown.output_cost_usd

        entry = CostLedgerEntry(
            schema_version=event.schema_version,
            correlation_id=event.correlation_id,
            idempotency_key=event.idempotency_key,
            ledger_id=uuid.uuid4().hex,
            cost_usd=cost_usd,
            cost_breakdown=breakdown,
            written_at=_utc_now(),
        )
        self._ledger.setdefault(_scope_key(event.scope), []).append(entry)
        self._idempotency_cache[event.idempotency_key] = entry
        return entry

    def query(self, q: CostQuery) -> CostReport:
        """Per `port-contracts.md` v0.2.2 §3 query() + §3.6 CostReport.

        Aggregates ledger entries for the scope into total_usd +
        pricing_table_versions list. M-T-COST-SCOPE-01 (Tier 2): no
        cross-scope leakage — only entries matching scope key returned.
        """
        entries = list(self._ledger.get(_scope_key(q.scope), []))
        total = sum((e.cost_usd for e in entries), start=Decimal("0"))
        pricing_versions = sorted(
            {e.cost_breakdown.pricing_table_version for e in entries}
        )
        return CostReport(
            schema_version=q.schema_version,
            correlation_id=q.correlation_id,
            idempotency_key=q.idempotency_key,
            entries=entries,
            total_usd=total,
            query=q,
            pricing_table_versions=pricing_versions,
        )

    def budget_check(self, scope: BudgetScope) -> BudgetStatus:
        """Per `port-contracts.md` v0.2.2 §3 budget_check() + §3.6.

        Status tri-state per S7 (warning_threshold_fraction): "ok" if
        consumed < threshold * limit; "warning" if threshold * limit
        <= consumed <= limit; "exceeded" if consumed > limit. None limit
        → always "ok" with limit_usd=None / remaining_usd=None.
        """
        scope_key = _scope_key(scope)
        consumed = sum(
            (e.cost_usd for e in self._ledger.get(scope_key, [])),
            start=Decimal("0"),
        )
        limit = self._budget_limits.get(scope_key)

        status: str
        remaining: Decimal | None
        if limit is None:
            status = "ok"
            remaining = None
        else:
            warning_band = Decimal(str(self._warning_threshold)) * limit
            if consumed > limit:
                status = "exceeded"
            elif consumed >= warning_band:
                status = "warning"
            else:
                status = "ok"
            remaining = limit - consumed

        return BudgetStatus(
            schema_version=1,
            correlation_id=self._default_correlation_id,
            idempotency_key=None,
            scope=scope,
            consumed_usd=consumed,
            limit_usd=limit,
            remaining_usd=remaining,
            status=status,  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_breakdown(
        self,
        event: CostEvent,
        pricing: dict[str, Decimal],
    ) -> CostBreakdown:
        """Decimal-formula Pi-Mono pricing math per Q-9.4.4-5 amended.

        TS source (models.ts:9692):
            usage.cost.input = (model.cost.input / 1000000) * usage.input
            usage.cost.output = (model.cost.output / 1000000) * usage.output

        Python Decimal equivalent (formula-parity, NOT byte-parity vs IEEE
        754 float TS-output per S2 disposition).
        """
        per_million = Decimal(1_000_000)
        input_cost = (pricing["input"] / per_million) * Decimal(event.input_tokens)
        output_cost = (pricing["output"] / per_million) * Decimal(event.output_tokens)
        return CostBreakdown(
            schema_version=event.schema_version,
            correlation_id=event.correlation_id,
            idempotency_key=event.idempotency_key,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            pricing_table_version=PRICING_TABLE_VERSION,
        )


__all__ = ["PiMonoNativeAdapter", "PRICING_TABLE", "PRICING_TABLE_VERSION"]
