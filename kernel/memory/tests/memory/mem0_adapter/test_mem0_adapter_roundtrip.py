"""Round-trip tests for Mem0Adapter against a FakeMem0Client.

Exercises:

- store_fact → search round-trip via the adapter's fact methods
- delete by entry_id → subsequent search returns zero hits
- full-tenant delete → records removed
- export (full and by-id)
- health reports OK when client responds
- health reports DOWN when client raises
- PII stub redacts email/SSN at write time
- Non-fact-shaped methods raise NotImplementedError (as designed)

These are adapter-LOGIC tests, not Mem0-behavior tests. Quinn's
Step 3.4 is expected to add live-backend integration coverage.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.memory._internal.mem0_adapter.adapter import Mem0Adapter
from praxis.kernel.memory.models import (
    DecisionDraft,
    DeleteCriteria,
    EvidenceItem,
    ExportCriteria,
    FactDraft,
    QuarantineReason,
    ReasoningStep,
    TaskOutcomeDraft,
    TaskSignature,
    TenantIdentityError,
)
from tests.memory.mem0_adapter.fake_client import FakeMem0Client

TENANT = "mem0-adapter-tenant"


def _new_adapter_with_fake() -> tuple[Mem0Adapter, FakeMem0Client]:
    fake = FakeMem0Client()
    adapter = Mem0Adapter(client=fake, tenant_hash=TENANT)
    return adapter, fake


# =============================================================================
# Fact round-trip
# =============================================================================


async def test_store_fact_persists_via_fake_client() -> None:
    adapter, fake = _new_adapter_with_fake()
    draft = FactDraft(fact="ICP segment X converts at 3x", source_excerpt="call 7")

    record = await adapter.store_fact(TENANT, "winston", "run-1", draft)

    assert record.tenant_hash == TENANT
    assert record.fact == "ICP segment X converts at 3x"
    assert record.record_type == "fact"
    assert fake.add_calls == 1
    assert fake.total_records() == 1


async def test_store_fact_redacts_pii_at_write_time() -> None:
    adapter, fake = _new_adapter_with_fake()
    draft = FactDraft(
        fact="Contact: ceo@example.com phone 555-12-3456",
        source_excerpt="SSN was 123-45-6789",
    )

    record = await adapter.store_fact(TENANT, "winston", "run-1", draft)

    # Email is redacted; so is the SSN in the source excerpt.
    assert "[REDACTED_EMAIL]" in record.fact
    assert "ceo@example.com" not in record.fact
    assert record.source_excerpt is not None
    assert "[REDACTED_SSN]" in record.source_excerpt
    assert "123-45-6789" not in record.source_excerpt

    # The fake store has the redacted version, not the original.
    stored = fake.records_for(TENANT)[0]
    assert "ceo@example.com" not in stored.memory


async def test_retrieve_facts_returns_matching_hits() -> None:
    adapter, fake = _new_adapter_with_fake()
    await adapter.store_fact(TENANT, "winston", "run-1", FactDraft(fact="pricing anchors at $99"))
    await adapter.store_fact(
        TENANT, "winston", "run-1", FactDraft(fact="churn driven by onboarding")
    )

    result = await adapter.retrieve_facts(TENANT, "winston", "run-1", "pricing", top_k=5)

    assert len(result.hits) == 1
    assert "pricing" in result.hits[0].record.fact.lower()  # type: ignore[union-attr]
    assert result.hits[0].record_type == "fact"
    assert result.source_distribution.tenant_hits == 1
    assert result.source_distribution.seed_hits == 0


async def test_retrieve_facts_rejects_invalid_top_k() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(ValueError):
        await adapter.retrieve_facts(TENANT, "a", "r", "q", top_k=0)


async def test_retrieve_facts_rejects_empty_query() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(ValueError):
        await adapter.retrieve_facts(TENANT, "a", "r", "   ")


# =============================================================================
# Delete / export
# =============================================================================


async def test_delete_by_entry_ids_removes_records() -> None:
    adapter, fake = _new_adapter_with_fake()
    r1 = await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="one"))
    await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="two"))

    result = await adapter.delete(TENANT, DeleteCriteria(entry_ids=[r1.entry_id]))

    assert result.deleted_entry_count == 1
    assert fake.total_records() == 1
    assert fake.delete_calls == 1


async def test_delete_full_tenant_drains_store_and_flags_crypto_shred() -> None:
    adapter, fake = _new_adapter_with_fake()
    await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="one"))
    await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="two"))

    result = await adapter.delete(TENANT, DeleteCriteria(full_tenant=True))

    assert result.crypto_shred_initiated is True
    assert fake.total_records() == 0
    assert fake.delete_all_calls == 1


async def test_delete_requires_criteria() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(ValueError):
        await adapter.delete(TENANT, DeleteCriteria())


async def test_export_full_tenant_walks_all_records() -> None:
    adapter, fake = _new_adapter_with_fake()
    for i in range(3):
        await adapter.store_fact(TENANT, "a", "r", FactDraft(fact=f"fact-{i}"))

    result = await adapter.export(TENANT, ExportCriteria(full_tenant=True))

    assert result.record_count == 3
    assert fake.get_all_calls == 1


async def test_export_by_entry_ids_walks_named_records() -> None:
    adapter, fake = _new_adapter_with_fake()
    r1 = await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="one"))
    r2 = await adapter.store_fact(TENANT, "a", "r", FactDraft(fact="two"))

    result = await adapter.export(TENANT, ExportCriteria(entry_ids=[r1.entry_id, r2.entry_id]))

    assert result.record_count == 2
    assert fake.get_calls == 2


async def test_export_requires_criteria() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(ValueError):
        await adapter.export(TENANT, ExportCriteria())


# =============================================================================
# Health
# =============================================================================


async def test_health_reports_ok_when_fake_responds() -> None:
    adapter, _ = _new_adapter_with_fake()
    report = await adapter.health()
    assert report.overall.value == "ok"
    assert report.backends[0].backend == "mem0"


async def test_health_reports_down_on_vendor_failure() -> None:
    fake = FakeMem0Client()

    def _boom(**_kwargs: object) -> object:
        raise RuntimeError("fake backend unreachable")

    fake.get_all = _boom  # type: ignore[method-assign]
    adapter = Mem0Adapter(client=fake, tenant_hash=TENANT)

    report = await adapter.health()
    assert report.overall.value == "down"
    assert report.backends[0].status.value == "down"
    assert report.backends[0].detail is not None
    assert "fake backend unreachable" in report.backends[0].detail


# =============================================================================
# Non-fact methods — raise NotImplementedError (Atelier/Beads territory)
# =============================================================================


async def test_store_task_outcome_raises_not_implemented() -> None:
    adapter, _ = _new_adapter_with_fake()
    sig = TaskSignature(
        task_type="t",
        input_hash="a" * 64,
        agents_involved=("x",),
        context_fingerprint="f",
    )
    draft = TaskOutcomeDraft(
        quality_score=0.8,
        quality_confidence=0.7,
        cost_usd=1.0,
        reasoning_trace=[ReasoningStep(step_index=0, agent_id="x", summary="s")],
        approach_summary="summary",
    )
    with pytest.raises(NotImplementedError):
        await adapter.store_task_outcome(TENANT, sig, draft)


async def test_store_decision_raises_not_implemented() -> None:
    adapter, _ = _new_adapter_with_fake()
    draft = DecisionDraft(
        decision="d",
        rationale="r",
        alternatives_considered=[],
        evidence=[EvidenceItem(source="s", excerpt="e")],
        confidence=0.5,
        captured_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
    )
    with pytest.raises(NotImplementedError):
        await adapter.store_decision(TENANT, draft)


async def test_retrieve_similar_tasks_raises_not_implemented() -> None:
    adapter, _ = _new_adapter_with_fake()
    sig = TaskSignature(
        task_type="t",
        input_hash="a" * 64,
        agents_involved=("x",),
        context_fingerprint="f",
    )
    with pytest.raises(NotImplementedError):
        await adapter.retrieve_similar_tasks(TENANT, sig)


async def test_retrieve_decisions_raises_not_implemented() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(NotImplementedError):
        await adapter.retrieve_decisions(TENANT, "q")


async def test_flag_and_quarantine_raises_not_implemented() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(NotImplementedError):
        await adapter.flag_and_quarantine(TENANT, "e1", QuarantineReason.OUTDATED)


# =============================================================================
# Tenant guard — defense in depth
# =============================================================================


async def test_store_fact_rejects_wrong_tenant() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(TenantIdentityError):
        await adapter.store_fact("wrong", "a", "r", FactDraft(fact="x"))


async def test_retrieve_facts_rejects_wrong_tenant() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(TenantIdentityError):
        await adapter.retrieve_facts("wrong", "a", "r", "q")


async def test_delete_rejects_wrong_tenant() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(TenantIdentityError):
        await adapter.delete("wrong", DeleteCriteria(full_tenant=True))


async def test_export_rejects_wrong_tenant() -> None:
    adapter, _ = _new_adapter_with_fake()
    with pytest.raises(TenantIdentityError):
        await adapter.export("wrong", ExportCriteria(full_tenant=True))
