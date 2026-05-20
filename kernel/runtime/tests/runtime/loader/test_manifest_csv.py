"""tests/runtime/loader/test_manifest_csv.py — GREEN commit.

Tests that AgentLoader parses the committed runtime manifest fixture correctly.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest


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


# test_manifest_csv.py lives at:
#   .../repo/kernel/runtime/tests/runtime/loader/
# parents[5] = repo root at the current kernel/runtime depth.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_assert_repo_root_pathwalk(_REPO_ROOT)
_MANIFEST_PATH = (
    _REPO_ROOT / "kernel" / "runtime" / "tests" / "runtime" / "fixtures" / "agent-manifest.csv"
)

# Import after the sentinel so repo-root drift fails before manifest loading.
from praxis.kernel.runtime.loader.manifest import (  # noqa: E402
    AgentLoader,
    AgentLoaderError,
    AgentRuntimeConfig,
)

_EXPECTED_AGENT_COUNT = 16


def test_manifest_file_exists() -> None:
    assert _MANIFEST_PATH.exists(), f"Manifest not found at {_MANIFEST_PATH}"


def test_load_returns_16_agents() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    assert len(catalog) == _EXPECTED_AGENT_COUNT, (
        f"Expected {_EXPECTED_AGENT_COUNT} agents, got {len(catalog)}"
    )


def test_all_required_fields_populated() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    for agent_name, cfg in catalog.items():
        defn = cfg.agent
        assert defn.name, f"{agent_name}: name empty"
        assert defn.display_name, f"{agent_name}: display_name empty"
        assert defn.title, f"{agent_name}: title empty"
        assert defn.capabilities, f"{agent_name}: capabilities empty"
        assert defn.role, f"{agent_name}: role empty"
        assert defn.identity, f"{agent_name}: identity empty"
        assert str(defn.module) in ("bmm", "cis", "tea"), (
            f"{agent_name}: bad module {defn.module!r}"
        )


def test_all_known_agent_names_present() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    expected_names = {
        "bmad-agent-analyst",
        "bmad-agent-tech-writer",
        "bmad-agent-pm",
        "bmad-agent-ux-designer",
        "bmad-agent-architect",
        "bmad-agent-dev",
        "bmad-agent-qa",
        "bmad-agent-quick-flow-solo-dev",
        "bmad-agent-sm",
        "bmad-cis-agent-brainstorming-coach",
        "bmad-cis-agent-creative-problem-solver",
        "bmad-cis-agent-design-thinking-coach",
        "bmad-cis-agent-innovation-strategist",
        "bmad-cis-agent-presentation-master",
        "bmad-cis-agent-storyteller",
        "bmad-tea",
    }
    loaded_names = set(catalog.keys())
    missing = expected_names - loaded_names
    extra = loaded_names - expected_names
    assert not missing, f"Missing agents: {missing}"
    assert not extra, f"Unexpected agents: {extra}"


def test_capabilities_are_lowercase_tuples() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    for agent_name, cfg in catalog.items():
        caps = cfg.agent.capabilities
        assert isinstance(caps, tuple), f"{agent_name}: capabilities not tuple"
        assert all(t == t.lower() for t in caps), (
            f"{agent_name}: capabilities not lowercase: {caps}"
        )


def test_malformed_row_raises_agent_loader_error(tmp_path: Path) -> None:
    """Malformed CSV rows raise AgentLoaderError with row index."""
    bad_csv = textwrap.dedent("""\
        name,displayName,title,icon,capabilities,role,identity,communicationStyle,principles,module,path,canonicalId
        incomplete-agent,,,,,,,,,,
    """)
    tmp_manifest = tmp_path / "bad.csv"
    tmp_manifest.write_text(bad_csv, encoding="utf-8")

    with pytest.raises(AgentLoaderError, match="row"):
        AgentLoader(manifest_path=tmp_manifest).load()


def test_duplicate_name_raises_agent_loader_error(tmp_path: Path) -> None:
    """Duplicate agent names raise AgentLoaderError."""
    header = (
        "name,displayName,title,icon,capabilities,role,identity,"
        "communicationStyle,principles,module,path,canonicalId"
    )
    row = ",".join(
        [
            "bmad-agent-dev",
            "Amelia",
            "Developer",
            "💻",
            "story execution",
            "Senior SW Engineer",
            "Executes stories.",
            "Terse.",
            "Tests first.",
            "bmm",
            "_bmad/bmm/4-implementation/bmad-agent-dev",
            "",
        ]
    )
    dup_csv = f"{header}\n{row}\n{row}\n"
    tmp_manifest = tmp_path / "dup.csv"
    tmp_manifest.write_text(dup_csv, encoding="utf-8")

    with pytest.raises(AgentLoaderError, match="duplicate"):
        AgentLoader(manifest_path=tmp_manifest).load()


def test_reload_clears_cache() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    first = loader.load()
    second = loader.load()
    assert first is second, "Second load() must return cached result"

    reloaded = loader.reload()
    assert len(reloaded) == len(first), "reload() must produce the same count"


def test_loader_returns_agent_runtime_config() -> None:
    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    for cfg in catalog.values():
        assert isinstance(cfg, AgentRuntimeConfig), (
            f"Expected AgentRuntimeConfig, got {type(cfg).__name__}"
        )
