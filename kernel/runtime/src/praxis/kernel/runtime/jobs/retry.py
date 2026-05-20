"""Backoff, poison routing, and alert severity for jobs infrastructure.

Architecture §4.2.5 — retry budget, backoff function, failure routing.
"""

from __future__ import annotations

import random
from datetime import timedelta

from praxis.kernel.runtime.jobs.schema import FailureReason, JobState, JobType


def backoff(retry_count: int) -> timedelta:
    """Exponential backoff with ±25% jitter.  retry_count is 0-indexed.

    Architecture §4.2.5::

        base_seconds = 2 ** min(retry_count, 8)
        jitter = random.uniform(0.75, 1.25)
        return timedelta(seconds=base_seconds * jitter)

    At retry_count=8 the base is ~256 s (≈4 min).  After max_retries=10
    the total elapsed time is in hours — well within the NFR-C-A1 7-day SLA.
    """
    base_seconds = 2 ** min(retry_count, 8)
    jitter = random.uniform(0.75, 1.25)
    return timedelta(seconds=base_seconds * jitter)


_FATAL_REASONS = frozenset(
    {
        FailureReason.INVARIANT_VIOLATION,
        FailureReason.TENANT_DRIFT,
        FailureReason.UNKNOWN,
    }
)

_RETRYABLE_REASONS = frozenset(
    {
        FailureReason.TRANSIENT_BACKEND,
        FailureReason.BACKEND_TIMEOUT,
        FailureReason.RESOURCE_EXHAUSTION,
    }
)


def get_final_state(
    failure_reason: FailureReason | str,
    retry_count: int,
    max_retries: int,
) -> JobState:
    """Return the terminal state for this failure.

    Fatal reasons (invariant_violation, tenant_drift, unknown) immediately
    route to POISONED regardless of retry budget — retrying would not help.

    Retryable reasons (transient_backend, backend_timeout, resource_exhaustion)
    route to FAILED while retries remain, then ABANDONED.
    """
    reason = FailureReason(failure_reason) if isinstance(failure_reason, str) else failure_reason

    if reason in _FATAL_REASONS:
        return JobState.POISONED

    # Retryable reason
    if retry_count < max_retries:
        return JobState.FAILED
    return JobState.ABANDONED


def get_alert_severity(job_type: JobType | str, final_state_name: str) -> str:
    """Return the alert severity for a job reaching terminal state.

    Architecture §4.2.5 severity map::

        retention_shred → P1 (NFR-C-A1 SLA in flight)
        retention_cascade → P1 (GDPR Article 17 obligation)
        backup_rewrite → P1 (backup integrity)
        quarantine_promote → P2 (operational backlog)
    """
    # Accept both value-form ("poisoned") and name-form ("POISONED")
    # Try value lookup first; fall back to name lookup for uppercase callers
    try:
        state = JobState(final_state_name)
    except ValueError:
        state = JobState[final_state_name.upper()]
    if state not in (JobState.ABANDONED, JobState.POISONED):
        return "none"

    jt = JobType(job_type) if isinstance(job_type, str) else job_type
    p1_types = {JobType.RETENTION_SHRED, JobType.RETENTION_CASCADE, JobType.BACKUP_REWRITE}
    return "P1" if jt in p1_types else "P2"


__all__ = ["backoff", "get_final_state", "get_alert_severity", "FailureReason"]
