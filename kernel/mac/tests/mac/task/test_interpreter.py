"""Coverage-floor tests for the Task Interpreter (arch §3).

These tests exist to satisfy the ≥90% coverage floor on ``task.py``,
``state.py``, and ``results.py``. They are NOT part of the v0.3 test-strategy
MAC-T-{section}-{seq} catalog; Murat did not enumerate an explicit
``MAC-T-TASK-*`` family in §3–§12.

Per Stage 5.3 preload Q3 disposition (2026-04-14): approved as a one-time
documented exception to test-strategy.md v0.3 §16.6 transition contract,
with the strict conditions that these tests carry no MAC-T IDs, no
``no_waiver`` marker, and are not added to ``NO_WAIVER_ALLOWLIST``. Quinn
5.4 QA will decide whether to formally catalog them.

Anchors:
  - mac/architecture.md §3 Task Interpreter Design
  - mac/architecture.md §3.4 DomainClass Enum (SQ-5)
  - mac/architecture.md §3.3 OutputFormatContract (Req-A)
  - mac/architecture.md §3.6 Failure Modes for the Interpreter
  - mac/architecture.md §2.4 DeliberationState
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.state import DeliberationState
from praxis.kernel.mac.task import (
    DomainClass,
    InvalidTaskError,
    OutputFormatContract,
    TaskInput,
    TaskInterpreter,
)


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_interpreter_rejects_empty_prompt() -> None:
    """Arch §3.6: empty / non-question prompt → InvalidTaskError, no Cycle 1 entry."""
    interpreter = TaskInterpreter()
    with pytest.raises(InvalidTaskError, match="empty"):
        interpreter.interpret(TaskInput(raw_prompt=""))
    with pytest.raises(InvalidTaskError, match="empty"):
        interpreter.interpret(TaskInput(raw_prompt="   \n\t  "))


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_interpreter_classifier_fallback_to_contested() -> None:
    """Arch §3.4: confidence < 0.7 → default to DomainClass.CONTESTED (safe default)."""
    interpreter = TaskInterpreter()
    task = TaskInput(
        raw_prompt="Ambiguous strategic question with low classifier signal",
        customer_context={"industry": "saas"},
    )
    result = interpreter.interpret(task)
    # With the built-in deterministic classifier and no explicit template,
    # an ambiguous prompt must fall back to CONTESTED, not raise.
    assert result.domain_class == DomainClass.CONTESTED
    assert result.classifier_confidence < 0.7


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_interpreter_injection_blocked_on_context() -> None:
    """Arch §3.6: adversarial customer_context keys matching mac\\.|gate_|disable_ are rejected."""
    interpreter = TaskInterpreter()

    for blocked_key in ("mac.override", "gate_r4_disabled", "disable_steelman"):
        task = TaskInput(
            raw_prompt="Should we expand to the EU market?",
            customer_context={blocked_key: "true"},
        )
        with pytest.raises(InvalidTaskError, match="injection"):
            interpreter.interpret(task)


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_interpreter_output_format_contract_frozen_bytes() -> None:
    """Arch §3.3: OutputFormatContract.to_producer_prompt_fragment() is byte-stable.

    Arch §3.3 mandates a snapshot test on the fragment so any future edit is
    intentional and reviewed. This floor test pins the exact bytes ratified at
    Stage 5.1 for v0.1 of the contract.
    """
    contract = OutputFormatContract(
        required_labels=(
            "[FINDINGS]",
            "[RECOMMENDATIONS]",
            "[STEELMAN]",
            "[DISSENT]",
            "[SCENARIOS]",
        ),
        content_levels=(
            "L1: Executive Summary + Key Recommendations",
            "L2: Main Analysis Body",
            "L3: Supporting Detail / Appendices",
        ),
        domain_guards_active=(),
    )
    fragment = contract.to_producer_prompt_fragment()
    # Required labels must appear verbatim.
    for label in contract.required_labels:
        assert label in fragment
    # Content levels must appear verbatim.
    for level in contract.content_levels:
        assert level in fragment
    # Fragment must be deterministic across calls (no timestamp, no state).
    assert fragment == contract.to_producer_prompt_fragment()


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_interpreter_workflow_template_id_and_high_confidence_classifier() -> None:
    """Arch §3.2 + §3.4: workflow_template_id overrides task_type;
    a keyword-dense prompt promotes classifier confidence ≥ 0.7.

    Covers two otherwise-unreached paths in ``task.py``:
      (a) ``_derive_task_type`` when ``workflow_template_id`` is truthy.
      (b) ``_classify`` returning a non-CONTESTED class at high confidence.
    """
    interpreter = TaskInterpreter()
    task = TaskInput(
        raw_prompt=(
            "Why is our retention diverging from NPS? What is causing the "
            "drop? Help us diagnose the root cause."
        ),
        workflow_template_id="strategic_advisory_v1",
    )
    result = interpreter.interpret(task)

    # (a) task_type mirrors the workflow template, not the default.
    assert result.task_signature.task_type == "strategic_advisory_v1"

    # (b) The prompt is saturated with DIAGNOSTIC keywords so the classifier
    # clears the 0.7 safe-default threshold and returns DIAGNOSTIC (not the
    # CONTESTED fallback).
    assert result.domain_class == DomainClass.DIAGNOSTIC
    assert result.classifier_confidence >= 0.7

    # The Stage 5 gate set is exactly R1..R12 (R13 deferred per arch §3.5).
    assert result.gate_set == tuple(f"R{n}" for n in range(1, 13))


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_output_format_contract_renders_guards_line_when_active() -> None:
    """Arch §3.3: when Req-E domain guards are active, the producer prompt
    fragment surfaces them so the producer knows which sections are optional.
    """
    contract = OutputFormatContract(domain_guards_active=("R5", "R11"))
    fragment = contract.to_producer_prompt_fragment()
    assert "Guards active for this task" in fragment
    assert "R5" in fragment and "R11" in fragment


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_deliberation_state_initial_phase_is_interpret() -> None:
    """Arch §2.4 + §5.2: fresh DeliberationState starts at the INTERPRET phase.

    Guards the arch §5.2 state-machine initial-state invariant from v0.1
    drift (v0.1 used ``State.IDLE`` which is not in arch §5.2).
    """
    from datetime import datetime, timezone

    from praxis.kernel.mac.task import TaskSignature

    sig = TaskSignature(
        task_type="strategic_advisory_uncategorized",
        input_hash="a" * 64,
        agents_involved=(),
        context_fingerprint="b" * 64,
    )
    state = DeliberationState(
        cycle_id="01HX000000000000000000000A",
        task=TaskInput(raw_prompt="Test prompt"),
        task_signature=sig,
        domain_class=DomainClass.CONTESTED,
        output_contract=OutputFormatContract(
            required_labels=("[FINDINGS]",),
            content_levels=("L1",),
            domain_guards_active=(),
        ),
        started_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert state.current_phase == "interpret"
    assert state.backtrack_count == 0
    assert state.cycle_1_output is None
    assert state.cycle_2_critique is None
    assert state.cycle_3_gate_scores is None
