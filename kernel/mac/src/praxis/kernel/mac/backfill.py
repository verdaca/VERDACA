"""One-time backfill job — arch §8.4.

:class:`BackfillJob` is the named MAC contract method ``mac.backfill``
per memory §6.6 line 915. It is a **one-time** batch job invoked by
the Stage 7 POV deployment runbook — NOT auto-invoked by
:class:`MetaAgentController` at startup or in the ``deliberate()``
hot path.

The job re-scores existing TENTATIVE experience entries against
current MAC quality criteria, promoting those that meet the
admission gate to CONFIRMED via Memory's facade. Step 6 ships a
structural skeleton; Stage 7 wires in the real promotion loop.

``MAC-T-INT-MEMORY-BACKFILL-01`` verifies the backfill is gated
behind an explicit entry point (``BackfillJob.run``) and is NOT
called from :class:`MetaAgentController.__init__` or
:meth:`MetaAgentController.deliberate`.

Binding anchors:
  - mac/architecture.md §8.4 Backfill — One-Time MAC First-Ship Job
  - memory/architecture.md §6.6 line 915 (named MAC contract: backfill)
  - mac/test-strategy.md v0.3 §6.2 MAC-T-INT-MEMORY-BACKFILL-01
"""

from __future__ import annotations

from dataclasses import dataclass

from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.migrations.mac_bootstrap_metadata_0001 import (
    BootstrapMetadataStore,
)


@dataclass(frozen=True)
class BackfillReport:
    """Result of a :meth:`BackfillJob.run` invocation."""

    tenant_hash: str
    candidates_inspected: int
    promoted_count: int
    skipped_count: int


class BackfillJob:
    """One-time MAC backfill job.

    **NOT auto-invoked.** :class:`MetaAgentController` does NOT call
    :meth:`run` from its constructor or from
    :meth:`MetaAgentController.deliberate`. The Stage 7 POV
    deployment runbook is responsible for invoking this job exactly
    once per first MAC ship per tenant.
    """

    def __init__(
        self,
        *,
        memory_adapter: MacMemoryAdapter,
        metadata_store: BootstrapMetadataStore,
    ) -> None:
        self._memory = memory_adapter
        self._sidecar = metadata_store

    async def run(
        self, *, tenant_id: str, tenant_hash: str | None = None
    ) -> BackfillReport:
        """Execute one backfill pass for ``tenant_id``.

        Step 6 returns a structural :class:`BackfillReport` with zero
        promotions — Stage 7 POV Harness wires the real promotion
        loop. The structural test
        ``MAC-T-INT-MEMORY-BACKFILL-01`` only verifies the entry
        point exists, returns the correct shape, and is not
        auto-invoked from :class:`MetaAgentController`.
        """
        effective_tenant_hash = tenant_hash or tenant_id
        # Stage 7 POV Harness real implementation:
        #   1. Enumerate TENTATIVE entries via Memory facade
        #   2. Re-score against current quality criteria
        #   3. Call mark_reused_successfully for promotions
        #   4. Update sidecar audit trail
        # Step 6 stub:
        return BackfillReport(
            tenant_hash=effective_tenant_hash,
            candidates_inspected=0,
            promoted_count=0,
            skipped_count=0,
        )


__all__ = ("BackfillJob", "BackfillReport")
