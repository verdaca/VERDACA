"""MAC Task Interpreter — arch §3.

Produces the structured artifacts every downstream MAC phase consumes:

  1. A normalized :class:`TaskSignature` matching Memory's shape (memory §2.2).
  2. A frozen :class:`DomainClass` classification (arch §3.4, SQ-5).
  3. An :class:`OutputFormatContract` declaring required Req-A section labels.
  4. Structural rejection of empty prompts and injection-carrying customer
     context per arch §3.6.

Binding architectural anchors:
  - mac/architecture.md §3 Task Interpreter Design (all subsections)
  - mac/architecture.md §3.3 OutputFormatContract (Req-A)
  - mac/architecture.md §3.4 DomainClass Enum (SQ-5 frozen schema)
  - mac/architecture.md §3.5 R13 Deferral (SQ-3)
  - mac/architecture.md §3.6 Failure Modes

Note on :class:`TaskSignature`: arch §3.2 specifies
``from praxis.kernel.memory.models import TaskSignature``. The MAC package
is implemented under USR dependency isolation (arch §4.6), so step 1 uses
a shape-compatible local mirror. At step 6 (Learning Loop) this mirror is
reconciled with the canonical memory.models version so ``isinstance`` and
wire-format remain bit-identical across the facade boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Exceptions
# =============================================================================


class InvalidTaskError(ValueError):
    """Raised by :class:`TaskInterpreter` when the input cannot enter Cycle 1.

    Arch §3.6 names two trigger conditions:

      - Empty / non-question prompt: extractor returns no inferable question.
      - Adversarial prompt-injection in ``customer_context``: structural check
        fires on keys matching ``mac\\.|gate_|disable_``.

    In both cases the caller sees ``InvalidTaskError``; the MAC emits
    ``mac.task.injection_blocked`` telemetry only for the injection branch
    (wired at step 3 when the observability layer lands).
    """


# =============================================================================
# DomainClass — frozen 5-value enum (SQ-5)
# =============================================================================


class DomainClass(str, Enum):
    """Domain classification for Req-E gate guards (arch §3.4, SQ-5 binding).

    **FROZEN SCHEMA.** Workflow templates MAY override which guards activate
    per ``DomainClass`` value (via arch §6.5 mapping config) but CANNOT
    introduce new enum values. Adding a sixth class requires a new Stage 5
    architecture revision, not a workflow YAML change.

    The MAC structural test ``MAC-T-NEG-DOMAIN-CLASS-01`` greps the package
    for ``class DomainClass`` and asserts exactly one match; the sibling test
    ``MAC-T-NEG-DOMAIN-CLASS-02`` asserts exactly five values.
    """

    CONTESTED = "contested"
    """Genuine disagreement; all gates fully active. Safe default under low
    classifier confidence (arch §3.4)."""

    CONSENSUS = "consensus"
    """Established settled-fact domain; R5 (Dissent Preservation) guard fires
    per arch §6.5 Req-E."""

    DETERMINISTIC = "deterministic"
    """Has a knowable correct answer; R11 (Scenario Coverage) guard fires
    per arch §6.5 Req-E."""

    BINARY = "binary"
    """Pass/fail or yes/no decision; R11 (Scenario Coverage) guard fires
    per arch §6.5 Req-E."""

    DIAGNOSTIC = "diagnostic"
    """Hypothesis-generation problem; R12 (Internal Consistency) is the load-
    bearing gate. Q10 in benchmark-questions.md §2 is the canonical example."""


# =============================================================================
# TaskSignature — MAC-local mirror of memory.models.TaskSignature
# =============================================================================


class TaskSignature(BaseModel):
    """Canonical fingerprint of a task for cross-session retrieval.

    Shape-compatible with ``praxis.kernel.memory.models.TaskSignature``
    (memory §2.2). Fields are ordered and typed identically so the
    reconciliation at step 6 is a rename, not a re-shape.
    """

    model_config = ConfigDict(frozen=True)

    task_type: str
    """High-level task category, e.g. ``'strategic_advisory'``."""

    input_hash: str
    """SHA-256 of the canonicalized user input. Deterministic."""

    agents_involved: tuple[str, ...]
    """Sorted tuple of agent IDs. Tuple (not list) because the model is frozen."""

    context_fingerprint: str
    """Rolling hash of retrieved context. Differs when the world changes."""

    schema_version: int = Field(
        default=1,
        description=(
            "Version of the TaskSignature INPUT schema used by the caller. "
            "Matches memory/models.py §2.2 for wire compatibility."
        ),
    )


# =============================================================================
# TaskInput — entry point data class
# =============================================================================


class TaskInput(BaseModel):
    """User-facing task payload fed to :meth:`MetaAgentController.deliberate`.

    Arch §3.2 defines the minimal shape; the Task Interpreter hashes the
    canonicalized ``raw_prompt`` into the ``TaskSignature.input_hash`` and
    derives ``context_fingerprint`` from ``customer_context``.
    """

    model_config = ConfigDict(frozen=True)

    raw_prompt: str
    """The unstructured question or task description from the caller."""

    customer_context: Mapping[str, str] = Field(default_factory=dict)
    """Customer situation metadata. Injection-screened at interpretation time."""

    workflow_template_id: str | None = None
    """Set by Stage 6 Studio when invoked through a template; None otherwise."""

    explicit_question: str | None = None
    """If the caller pre-extracted the decision question, the interpreter skips
    its own extraction step. None → interpret infers from ``raw_prompt``."""


# =============================================================================
# OutputFormatContract — Req-A mandatory labels
# =============================================================================


class OutputFormatContract(BaseModel):
    """The Req-A section-labelling contract embedded in every producer prompt
    (arch §3.3, quality-rubric.md §7 Req-A).

    The ``to_producer_prompt_fragment()`` rendering MUST be byte-stable across
    calls; any future edit is intentional and reviewed via the snapshot test
    in ``tests/mac/task/test_interpreter.py`` (coverage-floor) plus the
    arch-mandated tier-1 snapshot assertion when the producer pipeline lands.
    """

    model_config = ConfigDict(frozen=True)

    required_labels: tuple[str, ...] = (
        "[FINDINGS]",
        "[RECOMMENDATIONS]",
        "[STEELMAN]",
        "[DISSENT]",
        "[SCENARIOS]",
    )
    content_levels: tuple[str, ...] = (
        "L1: Executive Summary + Key Recommendations",
        "L2: Main Analysis Body",
        "L3: Supporting Detail / Appendices",
    )
    domain_guards_active: tuple[str, ...] = ()
    """Gate IDs whose Req-E guard has fired for this deliberation's
    :class:`DomainClass`; surfaced so the producer prompt can advertise which
    sections are optional under the current guard set."""

    def to_producer_prompt_fragment(self) -> str:
        """Render the byte-stable instruction block for producer prompts.

        Deterministic across calls — no timestamps, no randomness, no
        dependence on instance identity. Any edit requires intentional
        review per arch §3.3.
        """
        lines: list[str] = [
            "Your response MUST use the following section labels verbatim:",
        ]
        lines.extend(f"  - {label}" for label in self.required_labels)
        lines.append("")
        lines.append("Organize content into these three levels:")
        lines.extend(f"  - {level}" for level in self.content_levels)
        if self.domain_guards_active:
            lines.append("")
            lines.append(
                "Guards active for this task (sections may be optional): "
                + ", ".join(self.domain_guards_active)
            )
        return "\n".join(lines)


# =============================================================================
# TaskInterpretation — the artifact returned by TaskInterpreter.interpret()
# =============================================================================


class TaskInterpretation(BaseModel):
    """Structured artifact produced by :meth:`TaskInterpreter.interpret`.

    Bundles the normalized signature, domain classification, confidence
    score, and output-format contract. Downstream phases (Plan Decomposer
    at step 2, Iteration Controller at step 3) consume this as their
    single input.
    """

    model_config = ConfigDict(frozen=True)

    task_signature: TaskSignature
    domain_class: DomainClass
    classifier_confidence: float = Field(ge=0.0, le=1.0)
    output_contract: OutputFormatContract
    gate_set: tuple[str, ...]
    """The 12 gates active for this deliberation. R13 is deferred per arch
    §3.5 / SQ-3; Stage 5 builds always yield exactly R1..R12."""


# =============================================================================
# TaskInterpreter — the executor (arch §3.2 + §3.4 + §3.6)
# =============================================================================


_INJECTION_KEY_PATTERN = re.compile(r"(?:^mac\.|^gate_|^disable_)", re.IGNORECASE)
"""Per arch §3.6: customer_context keys matching this pattern are rejected
with InvalidTaskError. Anchored at start-of-key to avoid flagging legitimate
values that happen to contain the substring."""


_STAGE_5_GATE_SET: tuple[str, ...] = tuple(f"R{n}" for n in range(1, 13))
"""R1..R12. Per arch §3.5 + SQ-3, R13 is deferred to Stage 6; Stage 5 ships
with exactly 12 gates and this tuple is the single source of truth."""


class TaskInterpreter:
    """Deterministic Task Interpreter (arch §3).

    Owns the transformation ``TaskInput → TaskInterpretation``. Stateless;
    no retained cycle state, no LLM calls at this layer (classification is a
    deterministic keyword-anchored fallback at step 1; step 3 will inject a
    lightweight classifier agent when the Runtime spawner is available).
    """

    def interpret(self, task: TaskInput) -> TaskInterpretation:
        """Transform a :class:`TaskInput` into a :class:`TaskInterpretation`.

        Raises :class:`InvalidTaskError` for the two failure modes in arch
        §3.6 (empty prompt, customer_context injection). All other inputs
        produce a valid interpretation with a low-confidence fallback to
        :attr:`DomainClass.CONTESTED` when the classifier signal is weak.
        """
        self._reject_empty_prompt(task.raw_prompt)
        self._reject_injection(task.customer_context)

        input_hash = self._hash_canonical(task.raw_prompt)
        context_fingerprint = self._fingerprint_context(task.customer_context)
        task_type = self._derive_task_type(task.workflow_template_id)

        signature = TaskSignature(
            task_type=task_type,
            input_hash=input_hash,
            agents_involved=(),
            context_fingerprint=context_fingerprint,
        )

        domain_class, confidence = self._classify(task)

        contract = OutputFormatContract(domain_guards_active=())

        return TaskInterpretation(
            task_signature=signature,
            domain_class=domain_class,
            classifier_confidence=confidence,
            output_contract=contract,
            gate_set=_STAGE_5_GATE_SET,
        )

    # ------------------------------------------------------------------
    # Failure-mode guards (arch §3.6)
    # ------------------------------------------------------------------

    @staticmethod
    def _reject_empty_prompt(prompt: str) -> None:
        if not prompt or not prompt.strip():
            raise InvalidTaskError(
                "raw_prompt is empty or whitespace-only; cannot infer a decision question "
                "(arch §3.6 empty prompt failure mode)"
            )

    @staticmethod
    def _reject_injection(customer_context: Mapping[str, str]) -> None:
        for key in customer_context:
            if _INJECTION_KEY_PATTERN.search(key):
                raise InvalidTaskError(
                    f"customer_context contains injection-pattern key {key!r}; "
                    "rejected per arch §3.6 adversarial prompt-injection guard"
                )

    # ------------------------------------------------------------------
    # Hashing / fingerprinting
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_canonical(raw_prompt: str) -> str:
        canonical = raw_prompt.strip().encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _fingerprint_context(customer_context: Mapping[str, str]) -> str:
        canonical = json.dumps(dict(customer_context), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _derive_task_type(workflow_template_id: str | None) -> str:
        if workflow_template_id:
            return workflow_template_id
        return "strategic_advisory_uncategorized"

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify(self, task: TaskInput) -> tuple[DomainClass, float]:
        """Deterministic keyword-anchored classifier.

        Step 1 ships a pure-Python fallback; step 3 (3-cycle controller) will
        replace the internals with a Runtime-spawned lightweight classifier
        agent per arch §3.4. The interface is stable: this method always
        returns ``(DomainClass, confidence ∈ [0, 1])``.

        Safe default: ``DomainClass.CONTESTED`` when confidence < 0.7 per
        arch §3.4 "the most permissive class — no gates suspended".
        """
        prompt_lower = task.raw_prompt.lower()
        signals = {
            DomainClass.DETERMINISTIC: (
                "calculate",
                "compute",
                "exact value",
                "closed-form",
            ),
            DomainClass.BINARY: (
                "yes or no",
                "should we decide",
                "approve or reject",
                "pass/fail",
            ),
            DomainClass.DIAGNOSTIC: (
                "why is",
                "what is causing",
                "diagnose",
                "root cause",
                "diverging",
            ),
            DomainClass.CONSENSUS: (
                "established consensus",
                "well-known",
                "settled",
            ),
            DomainClass.CONTESTED: (
                "should we",
                "trade-off",
                "strategy",
                "risk",
            ),
        }

        hits: dict[DomainClass, int] = {cls: 0 for cls in signals}
        for cls, keywords in signals.items():
            for kw in keywords:
                if kw in prompt_lower:
                    hits[cls] += 1

        best_class = max(hits, key=lambda c: hits[c])
        best_hits = hits[best_class]
        total_hits = sum(hits.values())

        if total_hits == 0:
            # Zero-signal input — default confidence of 0.3, class CONTESTED
            # (safe permissive per arch §3.4 fallback rule).
            return DomainClass.CONTESTED, 0.3

        confidence = best_hits / max(total_hits, 1)

        # Safe-default guard per arch §3.4: confidence < 0.7 → CONTESTED.
        if confidence < 0.7:
            return DomainClass.CONTESTED, confidence

        return best_class, confidence


# =============================================================================
# Re-exports
# =============================================================================


__all__: tuple[str, ...] = (
    "DomainClass",
    "InvalidTaskError",
    "OutputFormatContract",
    "TaskInput",
    "TaskInterpretation",
    "TaskInterpreter",
    "TaskSignature",
)
