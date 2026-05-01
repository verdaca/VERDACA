"""Tenant-identity hard-fail coverage — every method that takes tenant_id.

§8.2: the facade validates `tenant_id == manifest.tenant_id` BEFORE
dispatching to any backend. On mismatch, raise `TenantIdentityError`
(subclass of `PermissionError`) — this is designed to hard-fail the
process under managed single-tenant because a mismatch can only
happen via a bug.

Every non-health method on `MemoryProtocol` must refuse to proceed on
a mismatched tenant_id. `health()` is excluded (no tenant_id parameter
per §2.1).
"""

from __future__ import annotations

import pytest

from praxis.kernel.memory import (
    DeleteCriteria,
    ExportCriteria,
    QuarantineReason,
    TenantIdentityError,
)
from tests.memory.facade._helpers import (
    make_memory,
    sample_decision,
    sample_fact,
    sample_signature,
    sample_task_outcome,
)

WRONG_TENANT = "unauthorized-caller"


async def test_store_task_outcome_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.store_task_outcome(WRONG_TENANT, sample_signature(), sample_task_outcome())


async def test_store_decision_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.store_decision(WRONG_TENANT, sample_decision())


async def test_store_fact_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.store_fact(WRONG_TENANT, "a", "r", sample_fact())


async def test_retrieve_similar_tasks_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.retrieve_similar_tasks(WRONG_TENANT, sample_signature())


async def test_retrieve_decisions_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.retrieve_decisions(WRONG_TENANT, "q")


async def test_retrieve_facts_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.retrieve_facts(WRONG_TENANT, "a", "r", "q")


async def test_delete_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.delete(WRONG_TENANT, DeleteCriteria(full_tenant=True))


async def test_export_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.export(WRONG_TENANT, ExportCriteria(full_tenant=True))


async def test_flag_and_quarantine_rejects_wrong_tenant() -> None:
    memory = make_memory()
    with pytest.raises(TenantIdentityError):
        await memory.flag_and_quarantine(WRONG_TENANT, "any-id", QuarantineReason.OUTDATED)


async def test_tenant_identity_error_is_permission_error() -> None:
    """§8.2 says TenantIdentityError must be a PermissionError subclass.

    Catchable as `PermissionError` by process-level error handlers that
    want to hard-fail the process on any privacy-category exception.
    """
    memory = make_memory()
    try:
        await memory.store_decision(WRONG_TENANT, sample_decision())
    except PermissionError as exc:
        assert isinstance(exc, TenantIdentityError)
    else:
        raise AssertionError("expected TenantIdentityError")


async def test_rejected_calls_do_not_reach_backends() -> None:
    """Tenant rejection happens BEFORE any backend call."""
    memory = make_memory()
    beads_len_before = len(memory._beads)  # noqa: SLF001

    with pytest.raises(TenantIdentityError):
        await memory.store_decision(WRONG_TENANT, sample_decision())

    # Beads chain did NOT grow — the store_decision audit bead was
    # never appended because the facade rejected the call first.
    assert len(memory._beads) == beads_len_before  # noqa: SLF001
