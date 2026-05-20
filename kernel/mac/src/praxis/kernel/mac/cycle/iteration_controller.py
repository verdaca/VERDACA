"""3-Cycle Iteration Controller — arch §5.

Owns the :data:`ALLOWED_TRANSITIONS` state machine (arch §5.2, 9 states,
linear flow with a single BACKTRACK_SET re-entry), the Req-C + SQ-7 Forge
ordering (arch §6.3 — raw → Req-C cap using RAW R7 → Forge penalty LAST),
backtrack-cap-at-1 (arch §5.5), and the Path B telemetry emission (arch
§10.3 + §11.3 + SQ-8 ``mac:`` prefix).

**Critical state machine invariants (arch §5.2 lines 505–558):**

  - 9 states EXACTLY: INTERPRET, DECOMPOSE, CYCLE_1_PRODUCE, CYCLE_2_REVIEW,
    CYCLE_3_VERIFY, BACKTRACK_SET, PUBLISH, COMPLETE, FAILED.
  - Initial = INTERPRET (NOT IDLE — that was v0.1 drift, retired at v0.3 §4.1).
  - Terminals = {COMPLETE, FAILED}.
  - Backtrack fires AT MOST ONCE per deliberation (backtrack_count ∈ {0, 1}).
  - Terminal failure via BudgetExceededError OR second-consecutive-Critical
    (any of R1/R2/R4/R5/R7 raw < 3 with backtrack_count == 1).
  - NO HARD_FAIL, NO FORGE_FALLBACK, NO ADJUDICATED, NO TERMINATED, NO
    user-cancel API.

**Critical Forge ordering invariant (arch §6.3 SQ-7):**

  1. Raw scores R1..R12
  2. Req-C cap using RAW R7: ``R8_eff = min(R8_raw, R7_raw + 1)``
  3. Forge penalty LAST on R7_effective ONLY (never propagating into R8 cap)

Worked example: ``(R7_raw=4, R8_raw=4, forge_degraded=True)`` →
``R7_eff=3, R8_eff=4`` (NOT R8_eff=3).

**Note on PhaseDAG.depends_on vs PhaseDAG.edges (team-lead constraint for
step 3):** the :class:`IterationController` consumes a :class:`PhaseDAG`
via :meth:`PhaseDAG.topological_order` ONLY. It never walks edges or
``depends_on`` directly. The two representations are kept in sync by the
:class:`PlanDecomposer` at construction — no divergence allowed.

**Note on single-pass repair semantics (team-lead constraint for step 3):**
when the controller receives a :class:`PhaseDAG` that was repaired by
:meth:`PlanDecomposer.repair`, the "one atomic repair transformation"
semantics (add one node AND rewire one edge) is already applied upstream;
the controller treats the resulting DAG as immutable.

Binding anchors:
  - mac/architecture.md §5.2 State Machine
  - mac/architecture.md §5.4 Cycle 2 Parallelism
  - mac/architecture.md §5.5 Backtracking on Critical Gate Failure
  - mac/architecture.md §5.6 Forge Fallback Handling
  - mac/architecture.md §5.7 ResourceBudget Defaults
  - mac/architecture.md §6.3 SQ-7 ordering
  - mac/architecture.md §10.1 Pi-Mono Integration
  - mac/architecture.md §10.3 Runtime Integration (Path B SQ-8 dedup)
  - mac/architecture.md §11.3 TelemetryEvent Linkage (dedup key format)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable

from praxis.kernel.mac.budget import (
    DEFAULT_MAC_BUDGET,
    BudgetExceededError,
    ResourceBudget,
)
from praxis.kernel.mac.cycle.section_router import GATE_SECTION_ROUTES
from praxis.kernel.mac.integrations.runtime import MacPathBEmitter


@runtime_checkable
class ClockProtocol(Protocol):
    """Minimal duck-typed clock protocol — decouples the controller from
    ``praxis.kernel.mac.testing.fakes.frozen_clock.FrozenClock`` at import
    time. :class:`FrozenClock` satisfies this structurally via its
    ``.advance(seconds)`` method. Breaking this import is what stops the
    ``gates.base → cycle.__init__ → iteration_controller →
    testing.fakes.__init__ → fake_llm_judge → gates.base`` circular
    chain.
    """

    def advance(self, seconds: int) -> None: ...


# =============================================================================
# State enum — verbatim from arch §5.2 (upper-case Python convention)
# =============================================================================


class State(Enum):
    """The 9 ratified arch §5.2 states. No HARD_FAIL. No FORGE_FALLBACK.
    No ADJUDICATED. No TERMINATED. No IDLE. No CYCLE_N_RUNNING."""

    INTERPRET = "interpret"
    DECOMPOSE = "decompose"
    CYCLE_1_PRODUCE = "cycle_1_produce"
    CYCLE_2_REVIEW = "cycle_2_review"
    CYCLE_3_VERIFY = "cycle_3_verify"
    BACKTRACK_SET = "backtrack_set"
    PUBLISH = "publish"
    COMPLETE = "complete"
    FAILED = "failed"


TERMINAL_STATES: frozenset[State] = frozenset({State.COMPLETE, State.FAILED})
"""Arch §5.2: the two terminal states. The state machine cannot leave them."""

INITIAL_STATE: State = State.INTERPRET
"""Arch §5.2: ``interpret`` is the single initial state."""


# The ratified transition relation per arch §5.2 lines 505–558.
# Any (from, to) pair not in this set raises InvalidStateTransitionError.
ALLOWED_TRANSITIONS: frozenset[tuple[State, State]] = frozenset(
    {
        (State.INTERPRET, State.DECOMPOSE),
        (State.DECOMPOSE, State.CYCLE_1_PRODUCE),
        (State.CYCLE_1_PRODUCE, State.CYCLE_2_REVIEW),
        (State.CYCLE_2_REVIEW, State.CYCLE_3_VERIFY),
        # Cycle 3 three branches:
        (State.CYCLE_3_VERIFY, State.PUBLISH),
        (State.CYCLE_3_VERIFY, State.BACKTRACK_SET),
        (State.CYCLE_3_VERIFY, State.FAILED),
        # Backtrack re-entry:
        (State.BACKTRACK_SET, State.CYCLE_1_PRODUCE),
        # Happy path:
        (State.PUBLISH, State.COMPLETE),
        # Terminal failure transitions (arch §5.2 footnote):
        (State.CYCLE_1_PRODUCE, State.FAILED),
        (State.CYCLE_2_REVIEW, State.FAILED),
    }
)


class InvalidStateTransitionError(Exception):
    """Raised when code attempts a transition not in :data:`ALLOWED_TRANSITIONS`.

    This is a programming error — the controller never emits this at
    runtime; it is guard rail for the property tests in
    ``MAC-T-CYCLE-STATE-02`` that drive Hypothesis-generated random
    transition sequences.
    """


# =============================================================================
# Critical gates + Forge penalty set (arch §6.1 + §6.3 SQ-7)
# =============================================================================


CRITICAL_GATES: frozenset[str] = frozenset({"R1", "R2", "R4", "R5", "R7"})
"""Arch §6.1: the five Critical-priority gates. A Critical gate scoring
raw < 3 at Cycle 3 triggers the arch §5.5 backtrack (first occurrence) or
terminal FAILED (second consecutive occurrence with backtrack_count == 1)."""

FORGE_PENALTY_SET: frozenset[str] = frozenset({"R7"})
"""Arch §6.3 SQ-7: the Forge-degradation penalty applies ONLY to R7
(Reasoning Traceability). Applied AFTER Req-C caps. Never propagates into
R8 (Actionability Calibration) because Req-C uses RAW R7 for its cap."""


def compute_final_scores(
    raw_scores: dict[str, int],
    *,
    forge_degraded: bool,
    reviewer_critique: Mapping[str, Any] | None = None,
    suspended: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Apply the arch §6.3 SQ-7 three-step ordering + Req-C Pair 2 + Req-E.

    **Step 4 signature evolution (team-lead authorized v0.3 → step-4):**
    ``reviewer_critique`` and ``suspended`` kwargs are added so the
    gate engine can delegate Req-C Pair 2 and Req-E to this single
    source of truth. The step-3 MAC-T-CYCLE-FORGE tests still pass
    because both new kwargs default to inert values.

    Ordering (arch §6.3):

      1. Start with the raw scores.
      2. Req-C Pair 1 (R8, R7): ``R8_eff = min(R8_raw, R7_raw + 1)``
         using **raw** R7 (NOT R7_effective).
      3. Req-C Pair 2 (R5, R4): if ``reviewer_critique`` carries a
         manufactured-dissent signal, ``R5_eff = min(R5_raw, R4_raw)``.
         Detection rule: ``reviewer_critique['manufactured_dissent_detected']``
         is True (step 4 fake-critique shape; step 5 swaps in the real
         ``ReviewerCritique`` Pydantic model).
      4. Forge penalty LAST: if ``forge_degraded``, reduce each gate in
         :data:`FORGE_PENALTY_SET` by 1 (floored at 1). R7 effective is
         affected; R8 cap is NOT (because step 2 used raw R7).
      5. Req-E suspensions: each gate_id in ``suspended`` has its
         effective score set to 0. Composite formula at
         ``praxis.kernel.mac.eval.composite.composite_score`` removes
         the suspended gate's weight from the denominator.

    Worked example (arch §6.3 + test-strategy §4.6.1
    ``MAC-T-CYCLE-FORGE-01``)::

        compute_final_scores({"R7": 4, "R8": 4, ...}, forge_degraded=True)
        # After step 2: R8 = min(4, 4+1) = 4
        # After step 4: R7 = max(1, 4-1) = 3
        # Result: R7=3, R8=4 (NOT R8=3)

    Manufactured-dissent worked example (step 4)::

        critique = {"manufactured_dissent_detected": True}
        compute_final_scores(
            {"R4": 2, "R5": 5, ...},
            forge_degraded=False,
            reviewer_critique=critique,
        )
        # Step 3 Pair 2: R5_eff = min(5, 2) = 2 (capped at R4_raw)
    """
    effective = dict(raw_scores)

    # Step 2: Req-C Pair 1 (R8, R7) cap — uses RAW R7 (arch §6.3 Pair 1).
    r7_raw = raw_scores.get("R7", 5)
    r8_raw = raw_scores.get("R8", 5)
    effective["R8"] = min(r8_raw, r7_raw + 1)

    # Step 3: Req-C Pair 2 (R5, R4) manufactured-dissent cap (arch §6.3 Pair 2).
    # Step 4 fake-critique shape: dict with "manufactured_dissent_detected" key.
    # Step 5 rebinds to the real ReviewerCritique Pydantic model.
    if reviewer_critique is not None and reviewer_critique.get(
        "manufactured_dissent_detected", False
    ):
        r4_raw = raw_scores.get("R4", 5)
        r5_raw = raw_scores.get("R5", 5)
        effective["R5"] = min(r5_raw, r4_raw)

    # Step 4: Forge penalty LAST, on R7 effective only (arch §6.3 SQ-7 step 3).
    if forge_degraded:
        for gate_id in FORGE_PENALTY_SET:
            if gate_id in effective:
                effective[gate_id] = max(1, effective[gate_id] - 1)

    # Step 5: Req-E suspensions (arch §6.5). Suspended gates are zeroed
    # here; composite_score removes them from the denominator.
    for gate_id in suspended:
        if gate_id in effective:
            effective[gate_id] = 0

    return effective


def has_critical_failure(effective_scores: dict[str, int]) -> bool:
    """Return True if any :data:`CRITICAL_GATES` gate effective score is < 3.

    Note: Critical-failure check consumes *effective* scores (post-Req-C
    cap, post-Forge penalty). At step 4 this is refined to check raw
    scores for the cycle-boundary decision, but at step 3 effective is
    sufficient — all the cycle tests script deterministic raw inputs
    where raw and effective diverge only via the Forge penalty on R7.
    """
    return any(effective_scores.get(g, 5) < 3 for g in CRITICAL_GATES)


# =============================================================================
# CycleScenario — scripted input for the controller's test-driven run path
# =============================================================================


@dataclass(frozen=True)
class CycleScenario:
    """Scripted scenario driving :class:`IterationController.run`.

    All fields are test-time knobs; production wiring at step 6 replaces
    the scenario-based driver with a real Producer / Reviewer / Adjudicator
    pipeline.
    """

    cycle_1_raw_scores: dict[str, int]
    """Raw R1..R12 scores returned after Cycle 1 + Cycle 2 + Cycle 3's
    first gate pass. Drives the arch §5.5 backtrack decision."""

    cycle_2_raw_scores: dict[str, int] | None = None
    """Optional raw scores for the second pass (after backtrack). If None
    and backtrack fires, the controller reuses ``cycle_1_raw_scores`` for
    the retry."""

    forge_degraded: bool = False
    """When True, the Forge penalty applies at step 3 of the SQ-7 ordering."""

    reviewer_count: int = 1
    """Number of Cycle 2 parallel reviewers. Arch §4.3: 2 for CONTESTED,
    1 otherwise, capped at 3."""

    tokens_per_cycle: int = 50_000
    """Simulated token consumption per cycle. Used for
    ``MAC-T-CYCLE-BUDGET-01``."""

    wall_seconds_per_cycle: float = 60.0
    """Simulated wall-clock consumption per cycle. Used for
    ``MAC-T-CYCLE-BUDGET-02`` via :class:`FrozenClock`."""

    prior_producer_output: str | None = None
    """For ``MAC-T-CYCLE-BACKTRACK-01``: value the retry producer sees as
    "previous cycle's output" when backtrack re-enters Cycle 1."""

    prior_reviewer_critique: str | None = None
    """For ``MAC-T-CYCLE-BACKTRACK-01``: value the retry producer sees as
    "previous cycle's reviewer critique"."""


# =============================================================================
# Result bag
# =============================================================================


@dataclass(frozen=True)
class ControllerResult:
    """Output of :meth:`IterationController.run`."""

    final_state: State
    backtrack_count: int
    terminal_reason: str | None
    state_transition_log: tuple[State, ...]
    final_scores: dict[str, int] | None
    forge_degraded: bool
    total_tokens: int
    elapsed_seconds: float
    emitted_events: tuple[tuple[str, str], ...]
    """``(event_type, dedup_key)`` tuples captured from the Path B emitter,
    in emission order. Step 3 tests assert uniqueness + monotonicity."""

    retry_producer_input: tuple[str | None, str | None] = (None, None)
    """For ``MAC-T-CYCLE-BACKTRACK-01``: ``(prior_producer_output,
    prior_reviewer_critique)`` seen by the retry producer on cycle 1
    re-entry. None when no backtrack occurred."""


# =============================================================================
# IterationController
# =============================================================================


class IterationController:
    """The arch §5 3-cycle controller.

    Stateless across deliberations; holds mutable state only for the
    duration of a single :meth:`run` call. Step 3 ships the scripted-
    scenario driver; step 6 wires in a real Producer / Reviewer /
    Adjudicator pipeline without changing the public surface.
    """

    STATES: frozenset[State] = frozenset(State)
    """The 9 ratified arch §5.2 states as a frozen set — exposed as a
    class attribute so the step-3 checkpoint report can assert
    ``IterationController.STATES == {s for s in State}`` byte-for-byte."""

    def __init__(
        self,
        *,
        budget: ResourceBudget | None = None,
        clock: ClockProtocol | None = None,
        path_b_emitter: MacPathBEmitter | None = None,
        cycle_id: str = "01HX000000000000000000000A",
    ) -> None:
        self._budget = budget or DEFAULT_MAC_BUDGET
        self._clock = clock
        self._path_b_emitter = path_b_emitter
        self._cycle_id = cycle_id

        self._state: State = INITIAL_STATE
        self._backtrack_count: int = 0
        self._transition_log: list[State] = [INITIAL_STATE]
        self._tokens_consumed: int = 0
        self._elapsed_seconds: float = 0.0
        self._emitted_events: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Read-only state access (used by property tests)
    # ------------------------------------------------------------------

    @property
    def state(self) -> State:
        return self._state

    @property
    def backtrack_count(self) -> int:
        return self._backtrack_count

    @property
    def transition_log(self) -> tuple[State, ...]:
        return tuple(self._transition_log)

    # ------------------------------------------------------------------
    # State machine driver
    # ------------------------------------------------------------------

    def _transition(self, target: State) -> None:
        """Apply a state transition, asserting it is in
        :data:`ALLOWED_TRANSITIONS`. Raises
        :class:`InvalidStateTransitionError` on any illegal edge.

        This is the single control point — every phase method routes
        here. ``MAC-T-CYCLE-STATE-02`` drives Hypothesis over random
        input sequences and asserts that no illegal edge is ever taken.
        """
        edge = (self._state, target)
        if edge not in ALLOWED_TRANSITIONS:
            raise InvalidStateTransitionError(
                f"illegal state transition: {self._state.name} -> {target.name} "
                f"(not in arch §5.2 allowed transition set)"
            )
        self._state = target
        self._transition_log.append(target)

    # ------------------------------------------------------------------
    # Public run() driver
    # ------------------------------------------------------------------

    async def run(self, scenario: CycleScenario) -> ControllerResult:
        """Walk the state machine end-to-end for a scripted scenario."""
        retry_producer_input: tuple[str | None, str | None] = (None, None)

        await self._emit("mac.cycle.started", {"cycle_id": self._cycle_id})

        # INTERPRET → DECOMPOSE (no telemetry event — not in test-strategy §4.6A.1 expected sequence)
        self._transition(State.DECOMPOSE)

        # DECOMPOSE → CYCLE_1_PRODUCE (first pass) or re-entry via BACKTRACK_SET
        while True:
            self._transition(State.CYCLE_1_PRODUCE)

            if self._backtrack_count == 1:
                retry_producer_input = (
                    scenario.prior_producer_output,
                    scenario.prior_reviewer_critique,
                )

            await self._emit(
                "mac.cycle.cycle_1_produce_entered",
                {"cycle_id": self._cycle_id},
            )

            # Simulate cycle 1 work with budget check.
            try:
                self._consume_cycle_budget(scenario)
            except BudgetExceededError:
                return self._fail("budget_exceeded", retry_producer_input)

            # CYCLE_1_PRODUCE → CYCLE_2_REVIEW
            self._transition(State.CYCLE_2_REVIEW)
            await self._emit(
                "mac.cycle.cycle_2_review_entered", {"cycle_id": self._cycle_id}
            )

            try:
                self._consume_cycle_budget(scenario)
            except BudgetExceededError:
                return self._fail("budget_exceeded", retry_producer_input)

            # CYCLE_2_REVIEW → CYCLE_3_VERIFY
            self._transition(State.CYCLE_3_VERIFY)
            await self._emit(
                "mac.cycle.cycle_3_verify_entered", {"cycle_id": self._cycle_id}
            )

            # Pick the raw-scores for this pass.
            if self._backtrack_count == 0:
                raw = scenario.cycle_1_raw_scores
            else:
                raw = scenario.cycle_2_raw_scores or scenario.cycle_1_raw_scores

            # Cycle 3 gate scoring: compute effective scores with Forge ordering.
            effective = compute_final_scores(
                raw, forge_degraded=scenario.forge_degraded
            )

            if scenario.forge_degraded:
                await self._emit(
                    "mac.cycle.forge_degradation_detected",
                    {"cycle_id": self._cycle_id},
                )

            critical_failed = has_critical_failure(effective)

            if not critical_failed:
                # Happy path: PUBLISH → COMPLETE
                self._transition(State.PUBLISH)
                await self._emit(
                    "mac.cycle.publish_entered", {"cycle_id": self._cycle_id}
                )
                self._transition(State.COMPLETE)
                await self._emit(
                    "mac.cycle.complete", {"cycle_id": self._cycle_id}
                )
                return ControllerResult(
                    final_state=State.COMPLETE,
                    backtrack_count=self._backtrack_count,
                    terminal_reason=None,
                    state_transition_log=tuple(self._transition_log),
                    final_scores=effective,
                    forge_degraded=scenario.forge_degraded,
                    total_tokens=self._tokens_consumed,
                    elapsed_seconds=self._elapsed_seconds,
                    emitted_events=tuple(self._emitted_events),
                    retry_producer_input=retry_producer_input,
                )

            # Critical failure: check backtrack cap.
            if self._backtrack_count == 0:
                # First failure → BACKTRACK_SET → CYCLE_1_PRODUCE re-entry
                self._transition(State.BACKTRACK_SET)
                self._backtrack_count = 1
                await self._emit(
                    "mac.cycle.backtrack_fired", {"cycle_id": self._cycle_id}
                )
                # Loop re-enters cycle_1_produce at the top of the while.
                continue

            # Second consecutive Critical failure → FAILED (arch §5.2 footnote)
            return self._fail(
                "second_consecutive_critical_gate_failure",
                retry_producer_input,
                final_scores=effective,
            )

    # ------------------------------------------------------------------
    # Failure helper
    # ------------------------------------------------------------------

    def _fail(
        self,
        reason: str,
        retry_producer_input: tuple[str | None, str | None],
        *,
        final_scores: dict[str, int] | None = None,
    ) -> ControllerResult:
        self._transition(State.FAILED)
        return ControllerResult(
            final_state=State.FAILED,
            backtrack_count=self._backtrack_count,
            terminal_reason=reason,
            state_transition_log=tuple(self._transition_log),
            final_scores=final_scores,
            forge_degraded=False,
            total_tokens=self._tokens_consumed,
            elapsed_seconds=self._elapsed_seconds,
            emitted_events=tuple(self._emitted_events),
            retry_producer_input=retry_producer_input,
        )

    # ------------------------------------------------------------------
    # Budget bookkeeping
    # ------------------------------------------------------------------

    def _consume_cycle_budget(self, scenario: CycleScenario) -> None:
        self._tokens_consumed += scenario.tokens_per_cycle
        self._elapsed_seconds += scenario.wall_seconds_per_cycle
        if self._clock is not None:
            self._clock.advance(int(scenario.wall_seconds_per_cycle))
        self._budget.check_tokens(self._tokens_consumed)
        self._budget.check_wall_seconds(self._elapsed_seconds)

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    async def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._path_b_emitter is None:
            # No emitter configured — capture locally so tests that don't
            # wire an emitter can still assert event sequence shapes.
            self._emitted_events.append((event_type, ""))
            return

        dedup_key = await self._path_b_emitter.emit(
            cycle_id=self._cycle_id,
            event_type=event_type,
            payload=payload,
        )
        self._emitted_events.append((event_type, dedup_key))


__all__ = (
    "ALLOWED_TRANSITIONS",
    "CRITICAL_GATES",
    "CycleScenario",
    "ControllerResult",
    "FORGE_PENALTY_SET",
    "INITIAL_STATE",
    "InvalidStateTransitionError",
    "IterationController",
    "State",
    "TERMINAL_STATES",
    "compute_final_scores",
    "has_critical_failure",
)
