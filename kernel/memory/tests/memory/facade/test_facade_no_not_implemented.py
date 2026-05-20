"""Negative test: no facade dispatch path raises NotImplementedError.

Individual backends raise NotImplementedError on out-of-domain methods
(e.g., Mem0Adapter raises on store_decision; AtelierStore raises on
store_fact). The Phase 3C facade must dispatch BY METHOD to the right
backend so a NotImplementedError never escapes. If one does, that is
a routing bug and the test fails loudly.

This test exercises EVERY MemoryProtocol method through the facade in
a happy-path form and asserts no NotImplementedError leaks. It is not
a coverage test — it is a routing-correctness test.
"""

from __future__ import annotations

import pytest

from praxis.kernel.memory import (
    DeleteCriteria,
    ExportCriteria,
    QuarantineReason,
)
from tests.memory.facade._helpers import (
    DEFAULT_TENANT_ID,
    make_memory,
    sample_decision,
    sample_fact,
    sample_signature,
    sample_task_outcome,
)

TENANT = DEFAULT_TENANT_ID


async def test_facade_store_task_outcome_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.store_task_outcome(TENANT, sample_signature(), sample_task_outcome())
    except NotImplementedError:
        pytest.fail("facade.store_task_outcome raised NotImplementedError")


async def test_facade_store_decision_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.store_decision(TENANT, sample_decision())
    except NotImplementedError:
        pytest.fail("facade.store_decision raised NotImplementedError")


async def test_facade_store_fact_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.store_fact(TENANT, "a", "r", sample_fact())
    except NotImplementedError:
        pytest.fail("facade.store_fact raised NotImplementedError")


async def test_facade_retrieve_similar_tasks_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.retrieve_similar_tasks(TENANT, sample_signature())
    except NotImplementedError:
        pytest.fail("facade.retrieve_similar_tasks raised NotImplementedError")


async def test_facade_retrieve_decisions_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.retrieve_decisions(TENANT, "query", top_k=3)
    except NotImplementedError:
        pytest.fail("facade.retrieve_decisions raised NotImplementedError")


async def test_facade_retrieve_facts_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.retrieve_facts(TENANT, "a", "r", "query")
    except NotImplementedError:
        pytest.fail("facade.retrieve_facts raised NotImplementedError")


async def test_facade_delete_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.delete(TENANT, DeleteCriteria(full_tenant=True))
    except NotImplementedError:
        pytest.fail("facade.delete raised NotImplementedError")


async def test_facade_export_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.export(TENANT, ExportCriteria(full_tenant=True))
    except NotImplementedError:
        pytest.fail("facade.export raised NotImplementedError")


async def test_facade_flag_and_quarantine_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    # Need a real entry_id — store a decision first so the quarantine
    # target exists in Atelier.
    record = await memory.store_decision(TENANT, sample_decision())
    try:
        await memory.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.OUTDATED)
    except NotImplementedError:
        pytest.fail("facade.flag_and_quarantine raised NotImplementedError")


async def test_facade_health_does_not_raise_not_implemented() -> None:
    memory = make_memory()
    try:
        await memory.health()
    except NotImplementedError:
        pytest.fail("facade.health raised NotImplementedError")
