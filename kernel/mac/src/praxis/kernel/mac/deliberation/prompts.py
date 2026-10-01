"""Role prompts and strict parsers for the deliberation roles.

Structured output is enforced by validating the model's JSON reply against
pydantic models, not by a provider feature: a reply that does not validate is
a failure the controller turns into an ``escalate`` receipt.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from praxis.kernel.mac.deliberation.receipt import (
    Critique,
    EvidenceSpan,
    FinalAnswer,
    Outcome,
)

PRODUCER_SYSTEM = (
    "You are the PRODUCER in a governed decision workflow. Draft an answer to the "
    "question using ONLY the numbered evidence. Cite the evidence id in square "
    "brackets after every claim, e.g. [E1]. If the evidence is insufficient, say "
    "exactly what is missing instead of guessing."
)

REVIEWER_COUNTER_SYSTEM = (
    "You are an independent REVIEWER. You have NOT seen any draft. From the "
    "question and the evidence alone, write the strongest case AGAINST the answer "
    "a hasty reader would give. Name risks, gaps and contradictions in the evidence."
)

REVIEWER_CRITIQUE_SYSTEM = (
    "You are an independent REVIEWER. You wrote the counterargument below before "
    "seeing the draft. Now critique the draft against the evidence and your "
    "counterargument. Reply with ONLY a JSON object: "
    '{"blocking": <true if the draft is unsafe to publish as-is>, '
    '"issues": [<short strings>], "summary": <one sentence>}.'
)

SYNTHESIZER_SYSTEM = (
    "You are the SYNTHESIZER. Produce the final decision record from the draft and "
    "the critique. Reply with ONLY a JSON object: "
    '{"outcome": "answer"|"clarify"|"abstain"|"escalate", "answer": <text, cite '
    'evidence ids like [E1]>, "cited_evidence_ids": [<ids you relied on>], '
    '"rationale": <one or two sentences>}. Use "clarify" when the question needs '
    'more input, "abstain" when the evidence cannot support any answer, "escalate" '
    "when a human must decide. Use only evidence ids that appear below."
)


def format_evidence(evidence: Sequence[EvidenceSpan]) -> str:
    return "\n".join(f"[{e.id}] ({e.source}) {e.text}" for e in evidence)


def producer_user(
    question: str,
    evidence: Sequence[EvidenceSpan],
    prior_draft: str | None = None,
    prior_critique: Critique | None = None,
) -> str:
    parts = [f"QUESTION:\n{question}", f"EVIDENCE:\n{format_evidence(evidence)}"]
    if prior_draft is not None and prior_critique is not None:
        issues = "\n".join(f"- {i}" for i in prior_critique.issues) or "- (none listed)"
        parts.append(
            "YOUR PREVIOUS DRAFT WAS REJECTED.\n"
            f"PREVIOUS DRAFT:\n{prior_draft}\nREVIEWER ISSUES:\n{issues}\n"
            f"REVIEWER SUMMARY: {prior_critique.summary}\nWrite a corrected draft."
        )
    return "\n\n".join(parts)


def reviewer_counter_user(question: str, evidence: Sequence[EvidenceSpan]) -> str:
    return f"QUESTION:\n{question}\n\nEVIDENCE:\n{format_evidence(evidence)}"


def reviewer_critique_user(
    question: str, evidence: Sequence[EvidenceSpan], draft: str, counterargument: str
) -> str:
    return (
        f"QUESTION:\n{question}\n\nEVIDENCE:\n{format_evidence(evidence)}\n\n"
        f"YOUR COUNTERARGUMENT (written before seeing the draft):\n{counterargument}\n\n"
        f"DRAFT TO CRITIQUE:\n{draft}"
    )


def synthesizer_user(
    question: str, evidence: Sequence[EvidenceSpan], draft: str, critique: Critique
) -> str:
    issues = "\n".join(f"- {i}" for i in critique.issues) or "- (none listed)"
    return (
        f"QUESTION:\n{question}\n\nEVIDENCE:\n{format_evidence(evidence)}\n\n"
        f"DRAFT:\n{draft}\n\nREVIEWER COUNTERARGUMENT:\n{critique.counterargument}\n\n"
        f"REVIEWER ISSUES:\n{issues}\nREVIEWER SUMMARY: {critique.summary}"
    )


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


class ReplyInvalid(Exception):
    """The model's reply did not validate against the expected schema."""


class _CritiqueReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blocking: bool
    issues: list[str]
    summary: str


class _FinalReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Outcome
    answer: str
    cited_evidence_ids: list[str]
    rationale: str


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _json_object(text: str) -> object:
    stripped = _FENCE.sub("", text.strip())
    start = stripped.find("{")
    if start < 0:
        raise ReplyInvalid("no JSON object in reply")
    try:
        obj, _ = json.JSONDecoder().raw_decode(stripped[start:])
    except json.JSONDecodeError as exc:
        raise ReplyInvalid(f"invalid JSON: {exc}") from exc
    return obj


def parse_critique(counterargument: str, text: str) -> Critique:
    try:
        r = _CritiqueReply.model_validate(_json_object(text))
    except ValidationError as exc:
        raise ReplyInvalid(str(exc)) from exc
    return Critique(
        counterargument=counterargument,
        blocking=r.blocking,
        issues=tuple(r.issues),
        summary=r.summary,
    )


def parse_final(text: str) -> FinalAnswer:
    try:
        r = _FinalReply.model_validate(_json_object(text))
    except ValidationError as exc:
        raise ReplyInvalid(str(exc)) from exc
    return FinalAnswer(
        outcome=r.outcome,
        answer=r.answer,
        cited_evidence_ids=tuple(r.cited_evidence_ids),
        rationale=r.rationale,
    )
