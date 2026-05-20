"""Shared Phase 3C test helpers.

Factories for building a composed Memory facade with the in-memory
backends registered, so every test module starts from a known clean
state. Keeps the facade tests DRY without coupling them to backend
construction details.
"""

from __future__ import annotations

from datetime import datetime, timezone

from praxis.kernel.memory import (
    DecisionDraft,
    DeploymentManifest,
    EvidenceItem,
    FactDraft,
    Memory,
    ReasoningStep,
    TaskOutcomeDraft,
    TaskSignature,
)
from praxis.kernel.memory._internal.atelier.store import AtelierStore
from praxis.kernel.memory._internal.beads.store import BeadsStore
from praxis.kernel.memory._internal.mem0_adapter.adapter import Mem0Adapter
from tests.memory.mem0_adapter.fake_client import FakeMem0Client

DEFAULT_TENANT_ID = "facade-test-tenant"


def make_memory(
    *,
    tenant_id: str = DEFAULT_TENANT_ID,
) -> Memory:
    """Construct a Memory facade with fresh in-memory backends.

    The tenant_hash equals the tenant_id under Phase 3C's minimum
    manifest — the real loader derives tenant_hash via salted sha256.
    """
    manifest = DeploymentManifest(tenant_id=tenant_id, tenant_hash=tenant_id)
    return Memory(
        manifest=manifest,
        beads=BeadsStore(tenant_hash=tenant_id),
        mem0=Mem0Adapter(
            client=FakeMem0Client(),
            tenant_hash=tenant_id,
        ),
        atelier=AtelierStore(tenant_hash=tenant_id),
    )


def sample_signature() -> TaskSignature:
    return TaskSignature(
        task_type="strategic_advisory",
        input_hash="a" * 64,
        agents_involved=("mary", "winston"),
        context_fingerprint="ctx-1",
    )


def sample_task_outcome() -> TaskOutcomeDraft:
    return TaskOutcomeDraft(
        quality_score=0.87,
        quality_confidence=0.75,
        cost_usd=3.21,
        reasoning_trace=[ReasoningStep(step_index=0, agent_id="mary", summary="assess landscape")],
        approach_summary="Pick option A; hedge with B",
    )


def sample_decision() -> DecisionDraft:
    return DecisionDraft(
        decision="ship v1 on Tuesday",
        rationale="compound delay risk outweighs polish budget",
        alternatives_considered=["delay 1 week", "ship with known bug"],
        evidence=[EvidenceItem(source="interview-12", excerpt="pain is acute")],
        confidence=0.82,
        captured_at=datetime(2026, 4, 12, 21, 0, tzinfo=timezone.utc),
    )


def sample_fact() -> FactDraft:
    return FactDraft(
        fact="ICP segment X converts at 3x rate",
        source_excerpt="call transcript 7",
    )
