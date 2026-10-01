"""Acceptance checks for wiring deliberation to model calls, MCP and CI.

No network: ``litellm.completion`` is patched. The live run itself is a
separate, key-gated script (``scripts/live/deliberate_live.py``) whose output is
committed under ``docs/receipts/``.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from praxis.adapters.litellm import LiteLLMAdapter
from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.adapters.pi_mono_native import PiMonoNativeAdapter
from praxis.composition.live_deliberation import (
    DEFAULT_PROVIDER,
    LiteLLMModelCaller,
    MissingApiKeyError,
    build_deliberator,
    load_anthropic_key,
    make_price_fn,
)
from praxis.kernel.mac.deliberation import Receipt, verify_receipt_hash, verify_receipt_json

REPO = Path(__file__).resolve().parents[5]

EVIDENCE = [
    {"id": "E1", "source": "soc2.pdf p3", "text": "SOC 2 Type II issued 2026-03."},
    {"id": "E2", "source": "dpa.pdf p1", "text": "Sub-processors listed in Annex 2."},
]


def _completion(
    content: str, prompt: int = 1000, completion: int = 500, finish: str = "stop"
) -> MagicMock:
    usage = MagicMock()
    usage.model_dump.return_value = {"prompt_tokens": prompt, "completion_tokens": completion}
    choice = MagicMock()
    choice.finish_reason = finish
    choice.message.content = content
    resp = MagicMock()
    resp.id = "resp-x"
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _script():
    replies = iter(
        [
            "DRAFT: fine [E1]",
            "COUNTER: check Annex 2",
            json.dumps({"blocking": False, "issues": ["annex"], "summary": "ok"}),
            json.dumps(
                {
                    "outcome": "answer",
                    "answer": "Yes, conditionally [E1].",
                    "cited_evidence_ids": ["E1"],
                    "rationale": "SOC 2 present.",
                }
            ),
        ]
    )
    return lambda **kw: _completion(next(replies))


# AC11 -- MCP tool ---------------------------------------------------------
def test_ac11_default_server_still_has_exactly_the_five_original_tools():
    names = {t.name for t in create_verdaca_mcp_server()._tool_manager.list_tools()}
    assert "verdaca_deliberate" not in names and len(names) == 5


def test_ac11b_deliberate_tool_registered_only_with_a_deliberator_and_returns_it():
    seen = {}

    async def deliberator(question, evidence):
        seen.update(question=question, evidence=evidence)
        return {"receipt": {"outcome": "answer"}, "receipt_path": "x.json"}

    server = create_verdaca_mcp_server(deliberator=deliberator)
    tools = {t.name: t for t in server._tool_manager.list_tools()}
    assert "verdaca_deliberate" in tools and len(tools) == 6
    out = asyncio.run(tools["verdaca_deliberate"].run({"question": "Q?", "evidence": EVIDENCE}))
    assert seen == {"question": "Q?", "evidence": EVIDENCE}
    assert out["receipt"]["outcome"] == "answer"


# AC12 -- LiteLLM caller + cost ------------------------------------------
def test_ac12_end_to_end_with_patched_litellm_writes_a_priced_verified_receipt(tmp_path):
    adapter = LiteLLMAdapter(api_keys={"anthropic": "test-key"})
    caller = LiteLLMModelCaller(adapter=adapter, default_model="claude-haiku-4-5")
    price = make_price_fn(PiMonoNativeAdapter())
    deliberator = build_deliberator(caller=caller, price=price, receipts_dir=tmp_path)

    with patch("praxis.adapters.litellm.adapter.litellm.completion") as comp:
        comp.side_effect = _script()
        out = asyncio.run(deliberator("Can we onboard Acme?", EVIDENCE))

    assert comp.call_count == 4
    for call in comp.call_args_list:
        assert call.kwargs["model"] == f"{DEFAULT_PROVIDER}/claude-haiku-4-5"
        assert call.kwargs["api_base"] is None
        assert call.kwargs["api_key"] == "test-key"

    saved = Path(out["receipt_path"])
    assert saved.parent == tmp_path and saved.suffix == ".json"
    receipt = Receipt.model_validate_json(saved.read_text())
    assert verify_receipt_hash(receipt)
    assert receipt.outcome.value == "answer"
    # haiku-4-5, verified list price: $1 in / $5 out per MTok
    per_call = Decimal("1000") * 1 / 1_000_000 + Decimal("500") * 5 / 1_000_000
    assert [c.cost_usd for c in receipt.calls] == [per_call] * 4
    assert receipt.total_cost_usd == per_call * 4 == Decimal("0.014")
    assert out["receipt"]["content_sha256"] == receipt.content_sha256


def test_ac12b_reviewer_can_be_routed_to_a_different_model():
    adapter = LiteLLMAdapter(api_keys={"anthropic": "k"})
    caller = LiteLLMModelCaller(
        adapter=adapter,
        default_model="claude-haiku-4-5",
        role_models={"reviewer_counter": "claude-sonnet-5-5", "reviewer_critique": "claude-sonnet-5-5"},
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as comp:
        comp.return_value = _completion("x")
        r1 = asyncio.run(caller(role="producer", system="s", user="u"))
        r2 = asyncio.run(caller(role="reviewer_counter", system="s", user="u"))
    assert (r1.model, r2.model) == ("claude-haiku-4-5", "claude-sonnet-5-5")


def test_ac12c_unpriced_model_gives_none_not_zero():
    price = make_price_fn(PiMonoNativeAdapter())
    from praxis.kernel.mac.deliberation import ModelReply

    reply = ModelReply("x", 10, 10, model="claude-fable-5-1", provider="anthropic", response_id="r")
    assert price(reply) is None


def test_ac12d_missing_key_is_a_clear_error_and_never_falls_back(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SOMETHING_ELSE=1\n")
    with pytest.raises(MissingApiKeyError):
        load_anthropic_key(env)
    env.write_text("ANTHROPIC_API_KEY=abc\n")
    assert load_anthropic_key(env) == "abc"


# AC13 -- CI runs the kernel suites ---------------------------------------
def test_ac13_ci_runs_every_kernel_suite_and_installs_pytest_mock():
    wf = yaml.safe_load((REPO / ".github/workflows/contract-tests.yml").read_text())
    steps = wf["jobs"]["contract-tests"]["steps"]
    text = "\n".join(str(s.get("run", "")) for s in steps)
    tracked = subprocess.run(
        ["git", "ls-files", "kernel"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    suites = {m.group(1) for f in tracked if (m := re.match(r"(kernel/.+?)/tests/", f))}
    assert suites, "no kernel suites found"
    for suite in suites:
        assert suite in text, f"CI does not run {suite}"
    assert "pytest-mock" in (REPO / "tests/pyproject.toml").read_text()


# AC14 -- no key can be committed ----------------------------------------
def test_ac14_dotenv_is_gitignored():
    r = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=REPO)
    assert r.returncode == 0


def test_ac14b_no_tracked_file_contains_an_api_key():
    pattern = re.compile("sk-" + r"ant-[A-Za-z0-9_-]{10,}|" + r"\bsk-[A-Za-z0-9]{32,}")
    files = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    hits = []
    for rel in files:
        p = REPO / rel
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        try:
            if pattern.search(p.read_text(errors="ignore")):
                hits.append(rel)
        except OSError:
            continue
    assert hits == []


# AC15 -- live scripts and example input ---------------------------------
def test_ac15_example_evidence_is_verbatim_from_the_repo():
    data = json.loads((REPO / "scripts/live/deliberation_example.json").read_text())
    assert data["question"] and len(data["evidence"]) >= 3
    for span in data["evidence"]:
        path, line = span["source"].rsplit(":", 1)
        lines = (REPO / path).read_text(encoding="utf-8").splitlines()
        assert span["text"] in lines[int(line) - 1], span["id"]


def test_ac15b_mcp_server_script_builds_with_deliberate_tool_and_needs_a_key(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "deliberate_mcp_server", REPO / "scripts/live/deliberate_mcp_server.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    no_key = tmp_path / ".env"
    no_key.write_text("")
    with pytest.raises(MissingApiKeyError):
        mod.build_server(env_path=no_key, receipts_dir=tmp_path)

    no_key.write_text("ANTHROPIC_API_KEY=dummy\n")
    names = {t.name for t in mod.build_server(env_path=no_key, receipts_dir=tmp_path)._tool_manager.list_tools()}
    assert "verdaca_deliberate" in names


# AC16 -- verified prices ----------------------------------------------------
def test_ac16_run_models_are_priced_at_verified_list_prices_with_a_source():
    from praxis.adapters.pi_mono_native import adapter as mod

    assert mod.PRICING_TABLE[("anthropic", "claude-haiku-4-5")] == {
        "input": Decimal("1"), "output": Decimal("5")
    }
    assert mod.PRICING_TABLE[("anthropic", "claude-sonnet-5-5")] == {
        "input": Decimal("2"), "output": Decimal("10")
    }
    assert mod.PRICING_TABLE[("anthropic", "claude-opus-4-7")] == {
        "input": Decimal("5"), "output": Decimal("25")
    }
    src = Path(mod.__file__).read_text()
    assert "platform.claude.com/docs/en/about-claude/pricing" in src and "2026-10-01" in src


# AC17 -- models that reject `temperature` ------------------------------------
def test_ac17_temperature_is_omitted_only_for_configured_models():
    adapter = LiteLLMAdapter(
        api_keys={"anthropic": "k"}, omit_temperature_models=frozenset({"claude-sonnet-5-5"})
    )
    caller = LiteLLMModelCaller(adapter=adapter, default_model="claude-haiku-4-5",
                                role_models={"reviewer_counter": "claude-sonnet-5-5"})
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as comp:
        comp.return_value = _completion("x")
        asyncio.run(caller(role="producer", system="s", user="u"))
        asyncio.run(caller(role="reviewer_counter", system="s", user="u"))
    haiku_kw, sonnet_kw = (c.kwargs for c in comp.call_args_list)
    assert haiku_kw["temperature"] == 0.0
    assert "temperature" not in sonnet_kw


def test_ac17b_builder_sends_no_temperature_to_a_sonnet_5_5_reviewer(tmp_path):
    from praxis.composition.live_deliberation import build_live_deliberator

    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=dummy\n")
    deliberate = build_live_deliberator(
        env_path=env, receipts_dir=tmp_path / "r", reviewer_model="claude-sonnet-5-5"
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as comp:
        comp.side_effect = _script()
        out = asyncio.run(deliberate("Q?", EVIDENCE))
    models = [c.kwargs["model"] for c in comp.call_args_list]
    assert models == [
        "anthropic/claude-haiku-4-5", "anthropic/claude-sonnet-5-5",
        "anthropic/claude-sonnet-5-5", "anthropic/claude-haiku-4-5",
    ]
    assert ["temperature" in c.kwargs for c in comp.call_args_list] == [True, False, False, True]
    assert out["receipt"]["outcome"] == "answer"



# AC18 -- output headroom and stop reasons -----------------------------------
def test_ac18_every_role_gets_4096_output_tokens_by_default(tmp_path):
    from praxis.composition.live_deliberation import build_live_deliberator

    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=dummy\n")
    deliberate = build_live_deliberator(
        env_path=env, receipts_dir=tmp_path / "r", reviewer_model="claude-sonnet-5-5"
    )
    with patch("praxis.adapters.litellm.adapter.litellm.completion") as comp:
        comp.side_effect = _script()
        asyncio.run(deliberate("Q?", EVIDENCE))
    assert [c.kwargs["max_tokens"] for c in comp.call_args_list] == [4096] * 4


def test_ac18b_provider_length_stop_reaches_the_receipt_as_a_flag(tmp_path):
    adapter = LiteLLMAdapter(api_keys={"anthropic": "k"})
    caller = LiteLLMModelCaller(adapter=adapter, default_model="claude-haiku-4-5")
    deliberator = build_deliberator(caller=caller, price=None, receipts_dir=tmp_path)
    replies = iter(_script_contents())
    finishes = iter(["stop", "length", "stop", "stop"])

    def fake(**kw):
        return _completion(next(replies), finish=next(finishes))

    with patch("praxis.adapters.litellm.adapter.litellm.completion", side_effect=fake):
        out = asyncio.run(deliberator("Q?", EVIDENCE))
    r = out["receipt"]
    assert [c["stop_reason"] for c in r["calls"]] == ["stop", "length", "stop", "stop"]
    assert r["truncated_calls"] == [2]


def test_ac18c_every_committed_receipt_verifies_as_written():
    paths = sorted((REPO / "docs/receipts").glob("receipt-*.json"))
    assert paths, "no committed receipts"
    for p in paths:
        assert verify_receipt_json(p.read_text(encoding="utf-8")), p.name


def _script_contents() -> list[str]:
    return [
        "DRAFT: fine [E1]",
        "COUNTER: check Annex 2",
        json.dumps({"blocking": False, "issues": ["annex"], "summary": "ok"}),
        json.dumps(
            {
                "outcome": "answer",
                "answer": "Yes, conditionally [E1].",
                "cited_evidence_ids": ["E1"],
                "rationale": "SOC 2 present.",
            }
        ),
    ]
