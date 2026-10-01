"""Acceptance checks for the real (model-backed) deliberation path.

Everything here runs against a scripted model double — no network. These
checks define "done" for review §8 step 1: producer, isolated reviewer and
synthesizer driven by the existing IterationController, emitting a typed
JSON receipt with per-call cost.
"""

from __future__ import annotations

import difflib
import json
from decimal import Decimal

import pytest

from praxis.kernel.mac.budget import ResourceBudget
from praxis.kernel.mac.cycle import IterationController, State
from praxis.kernel.mac.deliberation import Outcome, Receipt, verify_receipt_hash

from .conftest import (
    QUESTION,
    ScriptedModel,
    critique_json,
    happy_script,
    synth_json,
)

pytestmark = pytest.mark.asyncio


# AC1 -------------------------------------------------------------------
async def test_ac1_roles_run_in_order_through_the_state_machine(request_, make_roles):
    model = ScriptedModel(happy_script())
    receipt = await IterationController().run_deliberation(request_, make_roles(model))

    assert model.roles_called() == [
        "producer",
        "reviewer_counter",
        "reviewer_critique",
        "synthesizer",
    ]
    assert receipt.state_log == [
        "interpret", "decompose", "cycle_1_produce", "cycle_2_review",
        "cycle_3_verify", "publish", "complete",
    ]  # fmt: skip
    assert receipt.outcome is Outcome.ANSWER
    assert receipt.terminal_reason is None


# AC2 -------------------------------------------------------------------
async def test_ac2_reviewer_never_sees_producer_reasoning(request_, make_roles):
    model = ScriptedModel(happy_script())
    await IterationController().run_deliberation(request_, make_roles(model))
    by_role = {c["role"]: c for c in model.calls}
    draft = "DRAFT: Acme looks fine"

    blind = by_role["reviewer_counter"]
    assert QUESTION in blind["user"] and "SOC 2 Type II" in blind["user"]
    assert draft not in blind["user"] and draft not in blind["system"]
    assert by_role["producer"]["system"] not in blind["system"] + blind["user"]

    critique = by_role["reviewer_critique"]
    assert draft in critique["user"]  # sees the draft artefact
    assert "COUNTER: sub-processors" in critique["user"]  # and its own counterargument
    assert by_role["producer"]["system"] not in critique["system"] + critique["user"]


# AC3 -------------------------------------------------------------------
async def test_ac3_receipt_is_real_json_with_all_parts(request_, make_roles):
    model = ScriptedModel(happy_script())
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    doc = json.loads(receipt.model_dump_json())

    assert doc["question"] == QUESTION
    assert [e["id"] for e in doc["evidence"]] == ["E1", "E2"]
    assert doc["draft"].startswith("DRAFT:")
    assert doc["critique"]["counterargument"].startswith("COUNTER:")
    assert doc["critique"]["blocking"] is False
    assert doc["final"]["cited_evidence_ids"] == ["E1"]
    assert doc["outcome"] == "answer"
    assert len(doc["calls"]) == 4
    for c in doc["calls"]:
        assert {"role", "model", "input_tokens", "output_tokens", "cost_usd",
                "cost_status", "latency_seconds", "prompt_sha256"} <= set(c)  # fmt: skip
        assert c["cost_status"] == "priced"
    per_call = sum(Decimal(c["cost_usd"]) for c in doc["calls"])
    assert Decimal(doc["total_cost_usd"]) == per_call > 0
    assert doc["total_input_tokens"] == 400 and doc["total_output_tokens"] == 200
    Receipt.model_validate_json(receipt.model_dump_json())  # round-trips


async def test_ac3b_receipt_hash_detects_tampering(request_, make_roles):
    receipt = await IterationController().run_deliberation(
        request_, make_roles(ScriptedModel(happy_script()))
    )
    assert verify_receipt_hash(receipt)
    tampered = receipt.model_copy(update={"draft": "something else"})
    assert not verify_receipt_hash(tampered)


# AC4 -------------------------------------------------------------------
async def test_ac4_diff_is_the_real_unified_diff_draft_to_final(request_, make_roles):
    receipt = await IterationController().run_deliberation(
        request_, make_roles(ScriptedModel(happy_script()))
    )
    expected = "".join(
        difflib.unified_diff(
            receipt.draft.splitlines(keepends=True),
            receipt.final.answer.splitlines(keepends=True),
            fromfile="draft",
            tofile="final",
        )
    )
    assert receipt.diff == expected != ""


# AC5 -------------------------------------------------------------------
@pytest.mark.parametrize("name", ["answer", "clarify", "abstain", "escalate"])
async def test_ac5_every_typed_outcome_round_trips(name, request_, make_roles):
    model = ScriptedModel(happy_script(synthesizer=[synth_json(name)]))
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome(name)
    assert receipt.final.outcome is Outcome(name)


async def test_ac5b_untyped_outcome_fails_closed_to_escalate(request_, make_roles):
    model = ScriptedModel(happy_script(synthesizer=[synth_json("maybe")]))
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "synthesizer_output_invalid"
    assert receipt.state_log[-1] == State.FAILED.value
    assert receipt.final is None


async def test_ac5c_non_json_synthesizer_fails_closed(request_, make_roles):
    model = ScriptedModel(happy_script(synthesizer=["Sure! I think yes."]))
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert (receipt.outcome, receipt.terminal_reason) == (
        Outcome.ESCALATE, "synthesizer_output_invalid",
    )  # fmt: skip


# AC6 -------------------------------------------------------------------
async def test_ac6_citing_nonexistent_evidence_fails_closed(request_, make_roles):
    model = ScriptedModel(happy_script(synthesizer=[synth_json("answer", ("E1", "E9"))]))
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "unknown_evidence_cited"


async def test_ac6b_answer_without_any_citation_is_rejected(request_, make_roles):
    model = ScriptedModel(happy_script(synthesizer=[synth_json("answer", ())]))
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "answer_without_citation"


# AC7 -------------------------------------------------------------------
async def test_ac7_blocking_critique_backtracks_once_then_republishes(request_, make_roles):
    model = ScriptedModel(
        happy_script(
            producer=["DRAFT v1 [E1]", "DRAFT v2 fixed [E1]"],
            reviewer_counter=["COUNTER 1", "COUNTER 2"],
            reviewer_critique=[critique_json(True), critique_json(False)],
        )
    )
    receipt = await IterationController().run_deliberation(request_, make_roles(model))

    assert receipt.backtrack_count == 1
    assert State.BACKTRACK_SET.value in receipt.state_log
    assert model.roles_called().count("producer") == 2
    retry = model.calls[3]  # 2nd producer call
    assert retry["role"] == "producer"
    assert "DRAFT v1" in retry["user"] and "sub-processor list not checked" in retry["user"]
    assert receipt.draft == "DRAFT v2 fixed [E1]"
    assert [r.draft for r in receipt.superseded_rounds] == ["DRAFT v1 [E1]"]
    assert receipt.outcome is Outcome.ANSWER
    assert len(receipt.calls) == 7  # 2x(producer, counter, critique) + synthesizer


async def test_ac7b_second_blocking_critique_fails_and_escalates(request_, make_roles):
    model = ScriptedModel(
        happy_script(
            producer=["v1", "v2"],
            reviewer_counter=["c1", "c2"],
            reviewer_critique=[critique_json(True), critique_json(True)],
        )
    )
    receipt = await IterationController().run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "second_consecutive_blocking_critique"
    assert receipt.state_log[-1] == "failed"
    assert "synthesizer" not in model.roles_called()


# AC8 -------------------------------------------------------------------
async def test_ac8_budget_exhaustion_fails_with_partial_receipt(request_, make_roles):
    model = ScriptedModel(happy_script(), tokens=(100, 50))
    ctrl = IterationController(budget=ResourceBudget(max_tokens=200))
    receipt = await ctrl.run_deliberation(request_, make_roles(model))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "budget_exceeded"
    assert receipt.state_log[-1] == "failed"
    assert [c.role for c in receipt.calls] == ["producer", "reviewer_counter"]
    assert verify_receipt_hash(receipt)


# AC9 -------------------------------------------------------------------
async def test_ac9_unpriced_model_is_null_not_zero(request_, make_roles):
    model = ScriptedModel(happy_script())
    receipt = await IterationController().run_deliberation(
        request_, make_roles(model, price=lambda reply: None)
    )
    assert all(c.cost_usd is None and c.cost_status == "unpriced" for c in receipt.calls)
    assert receipt.total_cost_usd is None
    assert receipt.total_input_tokens == 400  # tokens still recorded


# AC11 ------------------------------------------------------------------
async def test_ac11_provider_error_fails_closed_with_partial_receipt(request_, make_roles):
    model = ScriptedModel(happy_script())

    async def boom(*, role, system, user):
        if role == "reviewer_counter":
            raise ConnectionError("provider down")
        return await model(role=role, system=system, user=user)

    receipt = await IterationController().run_deliberation(request_, make_roles(boom))
    assert receipt.outcome is Outcome.ESCALATE
    assert receipt.terminal_reason == "model_call_failed"
    assert [c.role for c in receipt.calls] == ["producer"]
    assert receipt.state_log[-1] == "failed" and verify_receipt_hash(receipt)
