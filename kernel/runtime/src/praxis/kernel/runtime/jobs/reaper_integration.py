"""Reaper integration — Path A hook for retention job completion.

Architecture §4.2.4 + §8.1.4: the reaper worker calls this module when
it completes a retention job.  The completion and the CostEvent emission
happen in one atomic transaction via CostRepository.session().
"""

from __future__ import annotations

from praxis.kernel.cost.storage.repository import CostRepository
from praxis.kernel.runtime.outbox.path_a import complete_retention_job_path_a


async def complete_and_emit(
    *,
    cost_repo: CostRepository,
    job_id: str,
    claim_token: str | None,
    tenant_hash: str,
    manifest_tenant_hash: str,
) -> None:
    """Complete a retention job and emit its CostEvent atomically (Path A).

    This is a thin delegation to path_a.complete_retention_job_path_a.
    It exists as a named seam for the Spawner integration tests.
    """
    await complete_retention_job_path_a(
        cost_repo=cost_repo,
        job_id=job_id,
        claim_token=claim_token,
        tenant_hash=tenant_hash,
        manifest_tenant_hash=manifest_tenant_hash,
    )


__all__ = ["complete_and_emit"]
