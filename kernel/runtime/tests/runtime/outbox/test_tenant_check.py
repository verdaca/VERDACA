"""
Tests for R4 Layer C cross-check (tenant hash verification).
All pure unit tests — no DB or Docker required.
"""

import pytest

from praxis.kernel.runtime.outbox.tenant_check import TenantDriftError, check_tenant

# ---------------------------------------------------------------------------
# Tenant check contract tests
# ---------------------------------------------------------------------------


def test_matching_tenant_hashes_pass():
    """Matching hashes must not raise any exception."""
    check_tenant("abc", "abc")  # should complete without raising


def test_mismatched_tenant_hashes_raise_tenant_drift_error():
    """Non-matching hashes must raise TenantDriftError."""
    with pytest.raises(TenantDriftError):
        check_tenant("abc", "xyz")


def test_empty_event_tenant_hash_raises():
    """An empty event tenant hash is invalid and must raise."""
    with pytest.raises((TenantDriftError, ValueError)):
        check_tenant("", "abc")


def test_error_message_includes_both_hashes():
    """The TenantDriftError message must reference both the event hash and the manifest hash."""
    event_hash = "event_hash_value"
    manifest_hash = "manifest_hash_value"
    with pytest.raises(TenantDriftError) as exc_info:
        check_tenant(event_hash, manifest_hash)
    error_message = str(exc_info.value)
    assert event_hash in error_message, (
        f"TenantDriftError message does not contain event hash {event_hash!r}: {error_message!r}"
    )
    assert manifest_hash in error_message, (
        f"TenantDriftError message does not contain manifest hash {manifest_hash!r}: {error_message!r}"
    )
