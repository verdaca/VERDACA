"""Praxis Multi-Agent Cognition (MAC) kernel — Stage 5.

The MAC is the deliberation plane: Task Interpreter → Plan Decomposer →
3-Cycle Iteration Controller → Quality Gate Engine → Information Asymmetry
Router → Cross-Session Learning Loop. See
``_bmad-output/implementation-artifacts/praxis/mac/architecture.md`` v0.1
(RATIFIED 2026-04-14) for the full design and
``mac/test-strategy.md`` v0.3 (RATIFIED 2026-04-14) for the 217-test
contract.

Stage 5.3 builds out the package in USR dependency order (arch §4.6):

  1. Task Interpreter (``task``, ``state``, ``results``)  ← step 1 (this step)
  2. Plan Decomposer (``plan``)                            ← step 2
  3. 3-Cycle Iteration Controller (``cycle/*``)            ← step 3
  4. Quality Gate Engine (``gates/*``, ``engine``)         ← step 4
  5. Information Asymmetry Router (``asymmetry``, ``adversarial/*``) ← step 5
  6. Learning Loop + Bootstrap + Migration + Meta-test     ← step 6

This ``__init__`` re-exports only the step 1 surface. Additional exports
land as each subsequent step completes.
"""

from __future__ import annotations

from praxis.kernel.mac.plan import (
    PhaseDAG,
    PhaseKind,
    PhaseNode,
    PlanDecomposer,
    PlanRepairFailedError,
)
from praxis.kernel.mac.results import DeliberationResult, EvaluatedSection, GateScore
from praxis.kernel.mac.state import DeliberationPhase, DeliberationState
from praxis.kernel.mac.task import (
    DomainClass,
    InvalidTaskError,
    OutputFormatContract,
    TaskInput,
    TaskInterpretation,
    TaskInterpreter,
    TaskSignature,
)

__all__: tuple[str, ...] = (
    "DeliberationPhase",
    "DeliberationResult",
    "DeliberationState",
    "DomainClass",
    "EvaluatedSection",
    "GateScore",
    "InvalidTaskError",
    "OutputFormatContract",
    "PhaseDAG",
    "PhaseKind",
    "PhaseNode",
    "PlanDecomposer",
    "PlanRepairFailedError",
    "TaskInput",
    "TaskInterpretation",
    "TaskInterpreter",
    "TaskSignature",
)
