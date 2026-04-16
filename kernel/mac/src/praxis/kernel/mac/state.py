"""MAC DeliberationState — arch §2.4.

Per-deliberation in-memory state held by :class:`MetaAgentController` for the
duration of a single ``deliberate()`` call. Not persisted between
deliberations; cross-session continuity flows through the Memory facade at
arch §8 (step 6).

The ``current_phase`` field is a :data:`Literal` over the arch §5.2 state
machine node names (lowercase snake-case per arch prose; upper-case enum
forms land in ``praxis.kernel.mac.cycle.iteration_controller`` at step 3).
The initial value is ``"interpret"``, matching arch §5.2's declared initial
state — never ``"idle"`` (v0.1 drift, retired at v0.3 §4.1A).

Binding anchors:
  - mac/architecture.md §2.4 State Management
  - mac/architecture.md §5.2 State Machine (lines 505–558; lowercase node names)
  - mac/architecture.md §2.5 DeliberationResult Output Contract
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from praxis.kernel.mac.task import (
    DomainClass,
    OutputFormatContract,
    TaskInput,
    TaskSignature,
)


DeliberationPhase = Literal[
    "interpret",
    "decompose",
    "cycle_1_produce",
    "cycle_2_review",
    "cycle_3_verify",
    "backtrack_set",
    "publish",
    "complete",
    "failed",
]
"""The nine arch §5.2 state-machine node names. Linear cycle flow with a
single ``backtrack_set`` re-entry and two terminal states (``complete``,
``failed``). No ``hard_fail``, no ``forge_fallback``, no ``adjudicated``,
no ``terminated``, no ``idle``, no ``cycle_N_running`` — all v0.1 drift
retired at v0.3 §4.1."""


class DeliberationState(BaseModel):
    """Per-deliberation mutable state bag.

    Mutable because the state machine progresses through ``current_phase``
    transitions; all other fields flip from ``None`` to their populated form
    exactly once per cycle. Frozen would force a rebuild per transition,
    which complicates the Phase Runner's threading contract in step 3.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=False)

    cycle_id: str
    """ULID, monotonic per deliberation. Populated at the ``interpret``
    phase before any sub-step runs; downstream telemetry keys on this value."""

    task: TaskInput
    """The original user-facing input; preserved verbatim for retrieval and
    debugging."""

    task_signature: TaskSignature
    """Normalized fingerprint produced by the Task Interpreter; used as the
    retrieval key for Cycle 1 seeding (arch §8.1)."""

    domain_class: DomainClass
    """Frozen 5-value classification (arch §3.4, SQ-5). Drives Req-E guard
    activation at the Quality Gate Engine (step 4)."""

    output_contract: OutputFormatContract
    """Req-A label contract embedded in the producer prompt. Byte-stable so
    re-runs and replay deterministic."""

    cycle_1_output: Any | None = None
    """Producer output from Cycle 1. Wired to ``ProducerOutput`` at step 3
    when the iteration controller lands; kept as ``Any`` here to avoid
    a circular import between ``state`` and ``cycle.iteration_controller``."""

    cycle_2_critique: Any | None = None
    """Reviewer critique(s) from Cycle 2. Wired to ``ReviewerCritique`` at
    step 5 when the asymmetry router lands."""

    cycle_3_gate_scores: Any | None = None
    """Dict ``{gate_id: GateScore}`` produced by the Quality Gate Engine at
    step 4. ``Any`` at step 1 to avoid the cycle-time circular import with
    ``praxis.kernel.mac.results.GateScore``."""

    backtrack_count: int = Field(default=0, ge=0, le=1)
    """Capped at 1 per arch §5.5; a second consecutive Critical gate failure
    terminates to ``failed`` rather than incrementing."""

    started_at: datetime
    """Wall-clock at ``interpret`` entry. Used for ``duration_seconds`` in
    :class:`DeliberationResult`."""

    ended_at: datetime | None = None
    """Populated when ``current_phase`` transitions to ``complete`` or
    ``failed``. ``None`` while the deliberation is in-flight."""

    current_phase: DeliberationPhase = "interpret"
    """The arch §5.2 state-machine cursor. Default is ``"interpret"``, the
    initial state; transitions happen inside the Phase Runner at step 3."""


__all__: tuple[str, ...] = (
    "DeliberationPhase",
    "DeliberationState",
)
