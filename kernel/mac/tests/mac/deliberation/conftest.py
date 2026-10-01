"""Scripted model double for deliberation acceptance checks.

Records every call so tests can assert exactly what each role was shown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

import pytest

from praxis.kernel.mac.deliberation import (
    DeliberationRequest,
    DeliberationRoles,
    EvidenceSpan,
    ModelReply,
)

EVIDENCE = (
    EvidenceSpan(id="E1", source="vendor-soc2.pdf p3", text="SOC 2 Type II issued 2026-03."),
    EvidenceSpan(id="E2", source="vendor-dpa.pdf p1", text="Sub-processors listed in Annex 2."),
)
QUESTION = "Can we onboard Acme as a payments vendor?"


def synth_json(outcome: str = "answer", cited: tuple[str, ...] = ("E1",)) -> str:
    return json.dumps(
        {
            "outcome": outcome,
            "answer": "Yes, conditional on DPA Annex 2 review [E1].",
            "cited_evidence_ids": list(cited),
            "rationale": "SOC 2 present; sub-processors still to be reviewed.",
        }
    )


def critique_json(blocking: bool = False) -> str:
    return json.dumps(
        {"blocking": blocking, "issues": ["sub-processor list not checked"], "summary": "minor"}
    )


@dataclass
class ScriptedModel:
    """Replies per role, in order. Each entry is a str (content) or a ModelReply."""

    script: dict[str, list[str]]
    tokens: tuple[int, int] = (100, 50)
    model: str = "fake-model"
    stops: dict[str, list[str]] = field(default_factory=dict)  # role -> stop reasons; default "stop"
    calls: list[dict] = field(default_factory=list)

    async def __call__(self, *, role: str, system: str, user: str) -> ModelReply:
        self.calls.append({"role": role, "system": system, "user": user})
        content = self.script[role].pop(0)
        return ModelReply(
            content=content,
            input_tokens=self.tokens[0],
            output_tokens=self.tokens[1],
            model=self.model,
            provider="fake",
            response_id=f"resp-{len(self.calls)}",
            stop_reason=self.stops[role].pop(0) if self.stops.get(role) else "stop",
        )

    def roles_called(self) -> list[str]:
        return [c["role"] for c in self.calls]


def happy_script(**over: list[str]) -> dict[str, list[str]]:
    base = {
        "producer": ["DRAFT: Acme looks fine, SOC 2 Type II exists [E1]."],
        "reviewer_counter": ["COUNTER: sub-processors in Annex 2 could be non-EU."],
        "reviewer_critique": [critique_json(False)],
        "synthesizer": [synth_json()],
    }
    base.update(over)
    return base


def price_flat(reply: ModelReply) -> Decimal | None:
    return Decimal(reply.input_tokens) * Decimal("0.00001") + Decimal(
        reply.output_tokens
    ) * Decimal("0.00004")


@pytest.fixture
def request_() -> DeliberationRequest:
    return DeliberationRequest(question=QUESTION, evidence=EVIDENCE)


@pytest.fixture
def make_roles():
    def _make(model: ScriptedModel, price=price_flat) -> DeliberationRoles:
        return DeliberationRoles(call=model, price=price)

    return _make
