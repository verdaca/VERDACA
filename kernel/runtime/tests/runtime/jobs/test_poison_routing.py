"""
Tests for poison routing logic in praxis.kernel.runtime.jobs.retry.
All pure unit tests — no DB or Docker required.
"""

from praxis.kernel.runtime.jobs.retry import get_alert_severity, get_final_state
from praxis.kernel.runtime.jobs.schema import FailureReason, JobType

# ---------------------------------------------------------------------------
# Routing / final-state tests
# ---------------------------------------------------------------------------


def test_transient_backend_routes_to_abandoned():
    """After max_retries exhausted with TRANSIENT_BACKEND failure → ABANDONED."""
    final_state = get_final_state(
        failure_reason=FailureReason.TRANSIENT_BACKEND,
        retry_count=3,
        max_retries=3,
    )
    assert final_state.name == "ABANDONED"


def test_invariant_violation_routes_to_poisoned():
    """INVARIANT_VIOLATION always routes to POISONED regardless of retry count."""
    final_state = get_final_state(
        failure_reason=FailureReason.INVARIANT_VIOLATION,
        retry_count=0,
        max_retries=3,
    )
    assert final_state.name == "POISONED"


def test_tenant_drift_routes_to_poisoned():
    """TENANT_DRIFT always routes to POISONED."""
    final_state = get_final_state(
        failure_reason=FailureReason.TENANT_DRIFT,
        retry_count=0,
        max_retries=3,
    )
    assert final_state.name == "POISONED"


# ---------------------------------------------------------------------------
# Alert severity tests
# ---------------------------------------------------------------------------


def test_abandoned_alert_severity_is_p2_for_quarantine_promote():
    """QUARANTINE_PROMOTE job in POISONED/ABANDONED state → alert severity P2."""
    severity = get_alert_severity(
        job_type=JobType.QUARANTINE_PROMOTE,
        final_state_name="POISONED",
    )
    assert severity == "P2"


def test_poisoned_alert_severity_is_p1_for_retention_shred():
    """RETENTION_SHRED job in POISONED state → alert severity P1."""
    severity = get_alert_severity(
        job_type=JobType.RETENTION_SHRED,
        final_state_name="POISONED",
    )
    assert severity == "P1"
