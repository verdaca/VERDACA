"""Stage 4.6 Pre-Sales Checkpoint — Praxis Runtime Demo.

Demonstrates:
  1. All 16 BMAD agents loadable from manifest
  2. Cost model per workflow (based on ResourceBudget defaults + Claude Sonnet 4.6 pricing)

Run with: python pre_sales_demo.py  (from the runtime/ directory, with src/ on PYTHONPATH)
Or via:   pytest pre_sales_demo.py  (pyproject.toml sets pythonpath automatically)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# -----------------------------------------------------------------------
# Pricing constants (Claude Sonnet 4.6 as of 2026-04)
# Source: https://www.anthropic.com/pricing
# -----------------------------------------------------------------------

# Sonnet 4.6 — default model for all 16 agents
_SONNET_INPUT_PER_M = 3.00    # USD per 1M input tokens
_SONNET_OUTPUT_PER_M = 15.00  # USD per 1M output tokens

# Assumed utilisation ratios (conservative: agents rarely hit budget ceiling)
_PRODUCER_INPUT_RATIO = 0.60   # 60% of budget typically used for input
_PRODUCER_OUTPUT_RATIO = 0.20  # 20% of budget for output
_REVIEWER_INPUT_RATIO = 0.55
_REVIEWER_OUTPUT_RATIO = 0.18


def _cost_usd(tokens: int, input_ratio: float, output_ratio: float) -> float:
    """Estimate cost in USD given a token budget and utilisation ratios."""
    input_tokens = tokens * input_ratio
    output_tokens = tokens * output_ratio
    return (input_tokens / 1_000_000 * _SONNET_INPUT_PER_M +
            output_tokens / 1_000_000 * _SONNET_OUTPUT_PER_M)


def _assert_repo_root_pathwalk(repo_root: Path) -> None:
    try:
        git_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=Path(__file__).resolve().parent,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        ).resolve()
    except (OSError, subprocess.CalledProcessError):
        assert (repo_root / "pyproject.toml").is_file(), (
            f"Repo root pathwalk drift: {repo_root} lacks pyproject.toml"
        )
    else:
        assert repo_root == git_root, f"Repo root pathwalk drift: {repo_root} != {git_root}"


def run_demo() -> None:
    from uuid import uuid4

    from praxis.kernel.runtime.loader.manifest import AgentLoader
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ProducerMemoryProxy, ReviewerMemoryProxy
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    # pre_sales_demo.py lives at .../repo/kernel/runtime/; parents[2] = repo root.
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    _assert_repo_root_pathwalk(_REPO_ROOT)
    manifest_path = (
        _REPO_ROOT
        / "kernel"
        / "runtime"
        / "tests"
        / "runtime"
        / "fixtures"
        / "agent-manifest.csv"
    )

    # -----------------------------------------------------------------------
    # 1. Load all 16 agents
    # -----------------------------------------------------------------------
    loader = AgentLoader(manifest_path=manifest_path)
    catalog = loader.load()

    print("=" * 65)
    print("  PRAXIS RUNTIME — Pre-Sales Checkpoint (Stage 4.6)")
    print("=" * 65)
    print()
    print(f"  Agents loaded: {len(catalog)}")
    print()

    # -----------------------------------------------------------------------
    # 2. Spawn each agent (producer + reviewer proxy) and confirm success
    # -----------------------------------------------------------------------
    memory = make_fake_memory()
    manifest = make_test_manifest()
    spawn_errors: list[str] = []

    print("  Agent Catalog:")
    print(f"  {'#':<4} {'Display Name':<28} {'Module':<6} {'Producer':<12} {'Reviewer'}")
    print("  " + "-" * 62)

    for i, (agent_name, cfg) in enumerate(sorted(catalog.items()), 1):
        p_ok = r_ok = "OK"
        try:
            proxy = _construct_proxy_for_role(
                role=AgentRole.PRODUCER,
                memory=memory,
                tenant_id=manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=uuid4(),
            )
            assert isinstance(proxy, ProducerMemoryProxy)
        except Exception as e:
            p_ok = "FAIL"
            spawn_errors.append(f"{agent_name} (producer): {e}")

        try:
            proxy = _construct_proxy_for_role(
                role=AgentRole.REVIEWER,
                memory=memory,
                tenant_id=manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=uuid4(),
            )
            assert isinstance(proxy, ReviewerMemoryProxy)
        except Exception as e:
            r_ok = "FAIL"
            spawn_errors.append(f"{agent_name} (reviewer): {e}")

        print(
            f"  {i:<4} {cfg.agent.display_name:<28} {cfg.agent.module.value:<6} "
            f"{p_ok:<12} {r_ok}"
        )

    print()
    if spawn_errors:
        print(f"  SPAWN FAILURES ({len(spawn_errors)}):")
        for err in spawn_errors:
            print(f"    FAIL {err}")
    else:
        print(f"  All {len(catalog)} agents spawned successfully OK")

    # -----------------------------------------------------------------------
    # 3. Cost model
    # -----------------------------------------------------------------------
    p_budget = ResourceBudget.default_for_role(AgentRole.PRODUCER)
    r_budget = ResourceBudget.default_for_role(AgentRole.REVIEWER)

    p_cost = _cost_usd(p_budget.max_tokens, _PRODUCER_INPUT_RATIO, _PRODUCER_OUTPUT_RATIO)
    r_cost = _cost_usd(r_budget.max_tokens, _REVIEWER_INPUT_RATIO, _REVIEWER_OUTPUT_RATIO)

    # Typical Praxis workflow: 1 producer + 1 reviewer
    single_workflow_cost = p_cost + r_cost

    # Full 16-agent deliberation (all 16 active in one workflow)
    full_workflow_cost = len(catalog) * ((p_cost + r_cost) / 2)

    print()
    print("  Cost Model (Claude Sonnet 4.6, conservative utilisation):")
    print(f"  {'-' * 50}")
    print(
        f"  Producer agent budget : {p_budget.max_tokens:>9,} tokens  -> "
        f"est. ${p_cost:.4f}/spawn"
    )
    print(
        f"  Reviewer agent budget : {r_budget.max_tokens:>9,} tokens  -> "
        f"est. ${r_cost:.4f}/spawn"
    )
    print(f"  {'-' * 50}")
    print(f"  Minimal workflow (1P + 1R)          : ${single_workflow_cost:.4f}")
    print(f"  Medium workflow (4 agents, mixed)   : ${single_workflow_cost * 2:.4f}")
    print(f"  Full deliberation (16 agents)       : ${full_workflow_cost:.4f}")
    print(f"  {'-' * 50}")
    print("  At scale:")
    print(f"    100 workflows/day   = ${single_workflow_cost * 100:.2f}/day")
    print(f"    500 workflows/day   = ${single_workflow_cost * 500:.2f}/day")
    print(f"    2000 workflows/day  = ${single_workflow_cost * 2000:.2f}/day")
    print()
    print(
        f"  Pricing basis: Sonnet 4.6 @ ${_SONNET_INPUT_PER_M}/M input, "
        f"${_SONNET_OUTPUT_PER_M}/M output"
    )
    print(
        f"  Utilisation ratios: {int(_PRODUCER_INPUT_RATIO * 100)}% input / "
        f"{int(_PRODUCER_OUTPUT_RATIO * 100)}% output (conservative)"
    )
    print()
    print("=" * 65)
    print("  Stage 4.6 gate: PASS" if not spawn_errors else "  Stage 4.6 gate: FAIL (spawn errors)")
    print("=" * 65)

    assert not spawn_errors, f"Spawn failures: {spawn_errors}"
    assert len(catalog) == 16, f"Expected 16 agents, got {len(catalog)}"


# Run as a pytest test so pyproject.toml pythonpath is set automatically
def test_pre_sales_checkpoint() -> None:
    """Stage 4.6: demo all 16 agents loaded with cost model."""
    run_demo()


if __name__ == "__main__":
    # Allow running directly if src/ is on PYTHONPATH
    run_demo()
