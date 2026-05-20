"""MetaAgentController — arch §2.1 public surface.

Top-level entry point for MAC deliberation. Wires together every
prior step:

  - **Step 1** Task Interpreter (``TaskInterpreter``)
  - **Step 2** Plan Decomposer (``PlanDecomposer``)
  - **Step 3** 3-Cycle Iteration Controller (``IterationController``)
  - **Step 4** Quality Gate Engine (``QualityGateEngine``) — exercised
    indirectly via the cycle controller's ``compute_final_scores``
  - **Step 5** Asymmetry Router (``AsymmetryRouter``)
  - **Step 6** Learning Loop + Bootstrap (``LearningLoop``,
    ``BootstrapLoader``)

The :meth:`deliberate` method drives the full ``TaskInput → DeliberationResult``
pipeline. Step 6 ships a smoke-level wiring — production-grade
producer/reviewer LLM calls land at Stage 7 POV Harness via the
real ``LLMJudgeClient.call_live()`` path.

**Critical invariants preserved by the controller:**

  - :class:`BackfillJob` is NEVER auto-invoked. The runbook owns it.
  - :class:`LearningLoop.publish` runs ONLY on
    ``final_phase == "complete"`` AND ``composite_score >=
    confidence_threshold`` (admission gate per arch §8.3).
  - The full pipeline is composable via constructor injection.

Binding anchors:
  - mac/architecture.md §2.1 Public Surface
  - mac/architecture.md §5 3-Cycle Iteration Controller
  - mac/architecture.md §8 Learning Loop
  - mac/test-strategy.md v0.3 §6.4A MAC-T-INT-WIREUP-01..03
"""

from __future__ import annotations

from datetime import datetime, timezone

from praxis.kernel.mac.asymmetry import AsymmetryRouter
from praxis.kernel.mac.bootstrap import BootstrapLoader
from praxis.kernel.mac.cycle.iteration_controller import (
    CycleScenario,
    IterationController,
    State,
)
from praxis.kernel.mac.eval.composite import composite_score
from praxis.kernel.mac.learning import LearningLoop
from praxis.kernel.mac.plan import PlanDecomposer
from praxis.kernel.mac.results import DeliberationResult, GateScore
from praxis.kernel.mac.task import (
    DomainClass,
    TaskInput,
    TaskInterpretation,
    TaskInterpreter,
)


class MetaAgentController:
    """Top-level MAC deliberation controller.

    Composes the full pipeline. Constructor injection lets callers
    substitute real or fake components per deployment context.
    """

    def __init__(
        self,
        *,
        interpreter: TaskInterpreter,
        decomposer: PlanDecomposer,
        iteration_controller: IterationController,
        asymmetry_router: AsymmetryRouter,
        learning_loop: LearningLoop,
    ) -> None:
        self._interpreter = interpreter
        self._decomposer = decomposer
        self._iter_ctrl = iteration_controller
        self._asym = asymmetry_router
        self._learning = learning_loop

    async def deliberate(
        self,
        task: TaskInput,
        *,
        tenant_id: str = "default",
        bootstrap_loader: BootstrapLoader | None = None,
    ) -> DeliberationResult:
        """Drive a full ``TaskInput → DeliberationResult`` pipeline.

        Per the team-lead constraint at step 6: bootstrap loading is
        OPT-IN via the ``bootstrap_loader`` kwarg — the controller
        does NOT auto-invoke bootstrap on every deliberation. Step 7
        deployment runbook calls
        :meth:`BootstrapLoader.load_gold_standards` once at MAC first
        ship, then never again (idempotent per S-Q1 if it is called).

        :class:`BackfillJob` is also NOT invoked here. The runbook owns
        backfill timing per arch §8.4.
        """
        # Step 1: interpret the task.
        interpretation = self._interpreter.interpret(task)

        # Step 2: decompose into the canonical phase DAG.
        plan = self._decomposer.decompose(
            signature=interpretation.task_signature,
            domain_class=interpretation.domain_class,
            output_contract=interpretation.output_contract,
        )

        # Optional bootstrap (OPT-IN — not auto-invoked).
        if bootstrap_loader is not None:
            await bootstrap_loader.load_gold_standards(tenant_id=tenant_id)

        # Step 3: drive the 3-cycle controller.
        # Step 6 ships a smoke-level scenario with all-4 raw scores.
        # Production wiring at Stage 7 POV Harness substitutes real
        # producer/reviewer calls via the asymmetry router that yield
        # actual gate scores.
        scenario = self._build_smoke_scenario(interpretation)
        controller_result = await self._iter_ctrl.run(scenario)

        # Build DeliberationResult from the ControllerResult.
        deliberation = self._build_deliberation_result(
            interpretation=interpretation,
            controller_result=controller_result,
            plan_node_count=len(plan.nodes),
        )

        # Step 6: publish through the learning loop (admission-gated).
        if deliberation.final_phase == "complete":
            await self._learning.publish(
                tenant_id=tenant_id, deliberation=deliberation
            )

        return deliberation

    @staticmethod
    def _build_smoke_scenario(
        interpretation: TaskInterpretation,
    ) -> CycleScenario:
        """Produce a smoke-level :class:`CycleScenario` for step 6 wiring.

        All raw scores set to 4 — well above the Critical threshold,
        no backtrack, no Forge degradation. Stage 7 POV Harness
        replaces this with a real producer/reviewer pipeline that
        emits actual gate scores.
        """
        raw_scores = {f"R{n}": 4 for n in range(1, 13)}
        reviewer_count = 2 if interpretation.domain_class == DomainClass.CONTESTED else 1
        return CycleScenario(
            cycle_1_raw_scores=raw_scores,
            forge_degraded=False,
            reviewer_count=reviewer_count,
        )

    @staticmethod
    def _build_deliberation_result(
        *,
        interpretation: TaskInterpretation,
        controller_result,
        plan_node_count: int,
    ) -> DeliberationResult:
        """Translate :class:`ControllerResult` into the public
        :class:`DeliberationResult`.
        """
        del plan_node_count  # reserved for telemetry annotation

        if controller_result.final_scores is None:
            gate_scores: dict[str, GateScore] = {}
            composite: float | None = None
        else:
            gate_scores = {
                gate_id: GateScore(
                    gate_id=gate_id,
                    raw_score=max(1, score),
                    effective_score=score,
                    weight=2 if gate_id in {"R1", "R2", "R4", "R5", "R7"} else 1,
                    suspended=score == 0,
                    rationale=f"step-6 smoke: {gate_id}={score}",
                    evaluated_section="FULL",
                )
                for gate_id, score in controller_result.final_scores.items()
            }
            try:
                composite = composite_score(
                    effective_scores=controller_result.final_scores,
                    suspended=frozenset(),
                )
            except ValueError:
                composite = None

        final_phase = (
            "complete" if controller_result.final_state == State.COMPLETE else "failed"
        )

        return DeliberationResult(
            cycle_id="01HX000000000000000000000A",
            task_signature=interpretation.task_signature,
            output=None,  # smoke level — Stage 7 wires the real producer output
            gate_scores=gate_scores,
            composite_score=composite,
            backtrack_count=controller_result.backtrack_count,
            cost_usd=0.0,
            duration_seconds=controller_result.elapsed_seconds,
            forge_degraded=controller_result.forge_degraded,
            final_phase=final_phase,
        )


__all__ = ("MetaAgentController",)
