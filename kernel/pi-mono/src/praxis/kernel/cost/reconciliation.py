"""Invoice reconciliation against stored CostRecords."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from .errors import ReconciliationError
from .models import (
    Invoice,
    ReconciliationDrift,
    ReconciliationReport,
    TokenClass,
)
from .storage import CostRepository
from .storage.schema import CostRecordRow

ZERO = Decimal("0")


class Reconciler:
    def __init__(self, repo: CostRepository, clock: Callable[[], datetime]) -> None:
        self._repo = repo
        self._clock = clock

    async def reconcile(
        self,
        invoice: Invoice,
        tolerance_pct: Decimal,
    ) -> ReconciliationReport:
        if not invoice.lines:
            raise ReconciliationError("invoice has no lines")

        drift_lines: list[ReconciliationDrift] = []
        total_internal = ZERO
        total_invoice = ZERO

        async with self._repo.session() as session:
            for line in invoice.lines:
                stmt = select(CostRecordRow).where(
                    CostRecordRow.provider == line.provider.value,
                    CostRecordRow.model_id == line.model_id,
                    CostRecordRow.started_at >= line.period_start,
                    CostRecordRow.started_at < line.period_end,
                )
                result = await session.execute(stmt)
                rows = list(result.scalars().all())

                internal_input = sum((r.input_tokens for r in rows), 0)
                internal_output = sum((r.output_tokens for r in rows), 0)
                internal_cread = sum((r.cache_read_tokens for r in rows), 0)
                internal_cwrite = sum((r.cache_write_tokens for r in rows), 0)
                internal_cost = sum((r.cost_total for r in rows), ZERO)

                drift_lines.append(
                    ReconciliationDrift(
                        provider=line.provider,
                        model_id=line.model_id,
                        period_start=line.period_start,
                        period_end=line.period_end,
                        internal_tokens_by_class={
                            TokenClass.INPUT: internal_input,
                            TokenClass.OUTPUT: internal_output,
                            TokenClass.CACHE_READ: internal_cread,
                            TokenClass.CACHE_WRITE: internal_cwrite,
                        },
                        invoice_tokens_by_class={
                            TokenClass.INPUT: line.input_tokens,
                            TokenClass.OUTPUT: line.output_tokens,
                            TokenClass.CACHE_READ: line.cache_read_tokens,
                            TokenClass.CACHE_WRITE: line.cache_write_tokens,
                        },
                        token_delta_by_class={
                            TokenClass.INPUT: line.input_tokens - internal_input,
                            TokenClass.OUTPUT: line.output_tokens - internal_output,
                            TokenClass.CACHE_READ: line.cache_read_tokens - internal_cread,
                            TokenClass.CACHE_WRITE: line.cache_write_tokens - internal_cwrite,
                        },
                        internal_cost=internal_cost,
                        invoice_cost=line.amount,
                        cost_delta=line.amount - internal_cost,
                        drift_pct=(
                            (line.amount - internal_cost) / line.amount
                            if line.amount != ZERO
                            else ZERO
                        ),
                    )
                )
                total_internal += internal_cost
                total_invoice += line.amount

        cost_delta = total_invoice - total_internal
        total_drift_pct = (
            cost_delta / total_invoice if total_invoice != ZERO else ZERO
        )
        abs_drift = abs(total_drift_pct)

        if abs_drift < Decimal("0.001"):
            status = "clean"
        elif abs_drift < Decimal("0.01"):
            status = "within_tolerance"
        elif abs_drift < Decimal("0.05"):
            status = "drift_detected"
        else:
            status = "critical_drift"

        return ReconciliationReport(
            invoice_id=invoice.invoice_id,
            reconciled_at=self._clock(),
            lines=drift_lines,
            total_internal=total_internal,
            total_invoice=total_invoice,
            total_delta=cost_delta,
            total_drift_pct=total_drift_pct,
            status=status,  # type: ignore[arg-type]
        )
