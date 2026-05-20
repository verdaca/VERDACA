"""Memory named-contract integration tests — mac/test-strategy.md v0.3 §6.2.

Covers MAC-T-INT-MEMORY-PUBLISH-01..02, MEMORY-REUSE-01, MEMORY-BACKFILL-01,
MAC-T-INT-WIREUP-03 (deferred from step 3).
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.asymmetry import AsymmetryRouter
from praxis.kernel.mac.backfill import BackfillJob, BackfillReport
from praxis.kernel.mac.bootstrap import BootstrapLoader
from praxis.kernel.mac.controller import MetaAgentController
from praxis.kernel.mac.cycle.iteration_controller import IterationController
from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.integrations.runtime import (
    FakeAgentSpawner,
    MacRuntimeAdapter,
)
from praxis.kernel.mac.learning import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    LearningLoop,
)
from praxis.kernel.mac.plan import PlanDecomposer
from praxis.kernel.mac.results import DeliberationResult, GateScore
from praxis.kernel.mac.task import (
    DomainClass,
    TaskInput,
    TaskInterpreter,
    TaskSignature,
)
from praxis.kernel.mac.testing.fakes.fake_memory_facade import FakeMemoryFacade
from praxis.kernel.mac.testing.fakes.fake_metadata_store import (
    InMemoryMacBootstrapMetadataStore,
)


def _build_pipeline() -> tuple[
    MetaAgentController,
    FakeMemoryFacade,
    InMemoryMacBootstrapMetadataStore,
    LearningLoop,
]:
    """Wire together the full step-1..6 pipeline with fake components."""
    memory = FakeMemoryFacade()
    sidecar = InMemoryMacBootstrapMetadataStore()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    learning = LearningLoop(memory_adapter=adapter)

    spawner = FakeAgentSpawner()
    runtime_adapter = MacRuntimeAdapter(
        spawner=spawner, shape_guard=lambda: None
    )
    asym = AsymmetryRouter(runtime_adapter=runtime_adapter)

    controller = MetaAgentController(
        interpreter=TaskInterpreter(),
        decomposer=PlanDecomposer(),
        iteration_controller=IterationController(),
        asymmetry_router=asym,
        learning_loop=learning,
    )
    return controller, memory, sidecar, learning


def _build_strong_deliberation(score: int = 5) -> DeliberationResult:
    """Construct a passing DeliberationResult with all 12 gates at ``score``.

    With score=5 across all gates: composite = 100.0, well above the
    75.0 threshold; confidence = 1.0 (zero variance).
    """
    sig = TaskSignature(
        task_type="strategic_advisory",
        input_hash="a" * 64,
        agents_involved=(),
        context_fingerprint="b" * 64,
    )
    weights = {"R1": 2, "R2": 2, "R3": 1, "R4": 2, "R5": 2, "R6": 1,
               "R7": 2, "R8": 1, "R9": 1, "R10": 1, "R11": 1, "R12": 1}
    gate_scores = {
        gate_id: GateScore(
            gate_id=gate_id,
            raw_score=score,
            effective_score=score,
            weight=weight,
            suspended=False,
            rationale=f"{gate_id}: strong",
            evaluated_section="FULL",
        )
        for gate_id, weight in weights.items()
    }
    return DeliberationResult(
        cycle_id="01HX000000000000000000000A",
        task_signature=sig,
        output=None,
        gate_scores=gate_scores,
        composite_score=100.0,
        backtrack_count=0,
        cost_usd=0.5,
        duration_seconds=120.0,
        forge_degraded=False,
        final_phase="complete",
    )


# =============================================================================
# §6.2.1 / §6.2.2 — MEMORY-PUBLISH-01 / 02
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_memory_publish_01_high_confidence_publishes() -> None:
    """MAC-T-INT-MEMORY-PUBLISH-01 — high-composite complete deliberation
    publishes to Memory via the named MAC contract.
    """
    _, memory, _, learning = _build_pipeline()
    deliberation = _build_strong_deliberation()

    entry_id = await learning.publish(
        tenant_id="publish-tenant", deliberation=deliberation
    )

    assert entry_id is not None
    assert entry_id.startswith("01HX")
    assert len(memory.stored_outcomes) == 1
    record = memory.stored_outcomes[0]
    assert record["tenant_id"] == "publish-tenant"
    assert record["outcome"]["composite_score"] == 100.0
    assert record["outcome"]["confidence"] == 1.0  # zero variance, all 5s


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_memory_publish_02_low_composite_or_failed_not_published() -> None:
    """MAC-T-INT-MEMORY-PUBLISH-02 — failed deliberations and
    low-composite results are NOT published to Memory.
    """
    _, memory, _, learning = _build_pipeline()

    # (a) Failed deliberation → not published.
    sig = TaskSignature(
        task_type="strategic_advisory",
        input_hash="c" * 64,
        agents_involved=(),
        context_fingerprint="d" * 64,
    )
    failed = DeliberationResult(
        cycle_id="01HX000000000000000000000B",
        task_signature=sig,
        output=None,
        gate_scores={},
        composite_score=None,
        backtrack_count=1,
        cost_usd=0.3,
        duration_seconds=60.0,
        forge_degraded=False,
        final_phase="failed",
    )
    result_a = await learning.publish(
        tenant_id="t1", deliberation=failed
    )
    assert result_a is None
    assert len(memory.stored_outcomes) == 0

    # (b) Low-composite (below 75 threshold) → not published.
    weights = {"R1": 2, "R2": 2, "R3": 1, "R4": 2, "R5": 2, "R6": 1,
               "R7": 2, "R8": 1, "R9": 1, "R10": 1, "R11": 1, "R12": 1}
    low_scores = {
        gid: GateScore(
            gate_id=gid,
            raw_score=2,
            effective_score=2,
            weight=w,
            suspended=False,
            rationale=f"{gid}: weak",
            evaluated_section="FULL",
        )
        for gid, w in weights.items()
    }
    low_result = DeliberationResult(
        cycle_id="01HX000000000000000000000C",
        task_signature=sig,
        output=None,
        gate_scores=low_scores,
        composite_score=40.0,  # below 75.0 threshold
        backtrack_count=0,
        cost_usd=0.3,
        duration_seconds=120.0,
        forge_degraded=False,
        final_phase="complete",
    )
    result_b = await learning.publish(
        tenant_id="t2", deliberation=low_result
    )
    assert result_b is None
    assert len(memory.stored_outcomes) == 0  # still no writes


# =============================================================================
# §6.2.3 — MEMORY-REUSE-01
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_memory_reuse_01_named_contract_passes_through() -> None:
    """MAC-T-INT-MEMORY-REUSE-01 — ``mac.reuse_successful`` named MAC
    contract calls Memory's ``retrieve_similar_tasks`` via the facade.
    """
    _, memory, _, learning = _build_pipeline()
    sig = TaskSignature(
        task_type="strategic_advisory",
        input_hash="e" * 64,
        agents_involved=(),
        context_fingerprint="f" * 64,
    )
    memory.canned_retrieve_results = ["fake_result_1", "fake_result_2"]

    results = await learning.mark_reused_successfully(
        tenant_id="reuse-tenant", signature=sig, top_k=3
    )

    assert results == ["fake_result_1", "fake_result_2"]
    assert len(memory.retrieve_log) == 1
    call = memory.retrieve_log[0]
    assert call["tenant_id"] == "reuse-tenant"
    assert call["top_k"] == 3
    assert call["min_similarity"] == 0.75  # default arch §10.2


# =============================================================================
# §6.2.4 — MEMORY-BACKFILL-01
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_memory_backfill_01_not_auto_invoked_by_controller() -> None:
    """MAC-T-INT-MEMORY-BACKFILL-01 — :class:`BackfillJob` is NOT
    auto-invoked by :class:`MetaAgentController`.

    Per arch §8.4: backfill is a one-time job, owned by the Stage 7
    POV deployment runbook. The controller does NOT call
    :meth:`BackfillJob.run` from its constructor or from
    :meth:`MetaAgentController.deliberate`.
    """
    import inspect as inspect_mod

    controller_source = inspect_mod.getsource(MetaAgentController)
    # The controller source must NOT instantiate BackfillJob
    # implicitly. The only legal instantiation is by the deployment
    # runbook (out of scope for this test). We check for the
    # instantiation syntax ``BackfillJob(`` with a paren — narrative
    # docstring mentions of ``BackfillJob`` are allowed because they
    # explain WHY the controller does not instantiate it.
    assert "BackfillJob(" not in controller_source, (
        "MetaAgentController must not instantiate BackfillJob; "
        "backfill timing is owned by the Stage 7 deployment runbook"
    )

    # Also: the deliberate() method's body does not call .run() on a
    # backfill job. Look for ``backfill_job.run(`` or any local-name
    # backfill-style invocation pattern — narrative ``backfill`` text
    # in docstrings is fine.
    deliberate_source = inspect_mod.getsource(MetaAgentController.deliberate)
    forbidden_invocations = (
        "BackfillJob(",
        ".backfill(",
        "backfill_job.run(",
    )
    for forbidden in forbidden_invocations:
        assert forbidden not in deliberate_source, (
            f"MetaAgentController.deliberate must not invoke "
            f"backfill via {forbidden!r}"
        )

    # The BackfillJob entry point exists and returns a structural
    # report when called explicitly (from the runbook).
    memory = FakeMemoryFacade()
    sidecar = InMemoryMacBootstrapMetadataStore()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    job = BackfillJob(memory_adapter=adapter, metadata_store=sidecar)
    report = await job.run(tenant_id="backfill-tenant")

    assert isinstance(report, BackfillReport)
    assert report.tenant_hash == "backfill-tenant"
    assert report.candidates_inspected == 0  # step 6 stub
    assert report.promoted_count == 0


# =============================================================================
# §6.4A.3 — WIREUP-03 (deferred from step 3)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_wireup_03_bootstrap_then_cycle_ordering() -> None:
    """MAC-T-INT-WIREUP-03 — bootstrap-then-cycle ordering.

    Per arch §8.1 + §5.2: the bootstrap loader runs ONCE at MAC first
    ship (idempotent on re-call), THEN the controller's
    ``deliberate()`` method runs deliberations against a Memory
    instance that already contains the gold standards.

    This test verifies the ordering: bootstrap completes, then a
    subsequent ``deliberate(task)`` call observes the bootstrapped
    Memory state via the learning loop's publish path.
    """
    controller, memory, sidecar, _ = _build_pipeline()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    loader = BootstrapLoader(
        memory_adapter=adapter, metadata_store=sidecar
    )

    # Phase 1: bootstrap. Runs once.
    inserted = await loader.load_gold_standards(tenant_id="wireup-3")
    assert inserted == 10
    assert sidecar.is_loaded("wireup-3")
    initial_outcomes = len(memory.stored_outcomes)
    assert initial_outcomes == 10

    # Phase 2: deliberate. The smoke pipeline runs through all 6
    # build steps and yields a complete DeliberationResult. The
    # learning loop publishes it (composite >= 75 because the smoke
    # scenario uses score=4 across 12 gates → composite = 80.0).
    task = TaskInput(raw_prompt="Should we expand to the EU market?")
    deliberation = await controller.deliberate(
        task, tenant_id="wireup-3"
    )

    assert deliberation.final_phase == "complete"
    assert deliberation.composite_score is not None
    assert deliberation.composite_score >= 75.0

    # Memory now has 10 bootstrap + 1 deliberation outcome = 11.
    assert len(memory.stored_outcomes) == initial_outcomes + 1

    # Bootstrap is idempotent: re-running yields 0 new inserts.
    second_load = await loader.load_gold_standards(tenant_id="wireup-3")
    assert second_load == 0
