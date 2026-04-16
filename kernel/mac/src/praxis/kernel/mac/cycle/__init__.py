"""MAC cycle subpackage — arch §5 3-Cycle Iteration Controller.

Public surface at step 3:

  - :class:`IterationController` — the state-machine executor (arch §5.2)
  - :class:`State`, :data:`ALLOWED_TRANSITIONS`, :data:`TERMINAL_STATES`,
    :data:`INITIAL_STATE` — state-machine primitives
  - :class:`InvalidStateTransitionError` — guard rail for property tests
  - :class:`CycleScenario`, :class:`ControllerResult` — scripted driver + result bag
  - :func:`compute_final_scores`, :func:`has_critical_failure` — Req-C + SQ-7 ordering
  - :data:`CRITICAL_GATES`, :data:`FORGE_PENALTY_SET`
  - :class:`ParallelReviewerPool`, :class:`DeterministicReplayPool`,
    :class:`ReviewerSubmission` — Cycle 2 parallelism (Tension #2)
  - :data:`GATE_SECTION_ROUTES`, :class:`SectionSelector`,
    :func:`route_for`, :func:`serialize_routes_to_binary` — Req-B section router
"""

from __future__ import annotations

from praxis.kernel.mac.cycle.iteration_controller import (
    ALLOWED_TRANSITIONS,
    CRITICAL_GATES,
    FORGE_PENALTY_SET,
    INITIAL_STATE,
    TERMINAL_STATES,
    ControllerResult,
    CycleScenario,
    InvalidStateTransitionError,
    IterationController,
    State,
    compute_final_scores,
    has_critical_failure,
)
from praxis.kernel.mac.cycle.parallel_pool import (
    DeterministicReplayPool,
    ParallelReviewerPool,
    ReviewerSubmission,
)
from praxis.kernel.mac.cycle.section_router import (
    GATE_SECTION_ROUTES,
    SectionSelector,
    route_for,
    serialize_routes_to_binary,
)

__all__ = (
    "ALLOWED_TRANSITIONS",
    "CRITICAL_GATES",
    "ControllerResult",
    "CycleScenario",
    "DeterministicReplayPool",
    "FORGE_PENALTY_SET",
    "GATE_SECTION_ROUTES",
    "INITIAL_STATE",
    "InvalidStateTransitionError",
    "IterationController",
    "ParallelReviewerPool",
    "ReviewerSubmission",
    "SectionSelector",
    "State",
    "TERMINAL_STATES",
    "compute_final_scores",
    "has_critical_failure",
    "route_for",
    "serialize_routes_to_binary",
)
