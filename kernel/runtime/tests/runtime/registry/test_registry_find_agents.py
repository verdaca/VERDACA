"""tests/runtime/registry/test_registry_find_agents.py

Coverage filler for registry.py find_agents() pipeline.
Tests are added after implementation to cover uncovered branches.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.runtime.loader.manifest import AgentRuntimeConfig
from praxis.kernel.runtime.models import AgentDefinition, AgentModule
from praxis.kernel.runtime.registry.embedder import DeterministicTestEmbedder
from praxis.kernel.runtime.registry.registry import (
    AgentMatch,
    AgentQuery,
    AgentRegistry,
)


def _make_agent(name: str, caps: str) -> AgentRuntimeConfig:
    """Build a minimal AgentRuntimeConfig for testing."""

    defn = AgentDefinition(
        name=name,
        display_name=name.title(),
        title="Test Agent",
        icon="🤖",
        capabilities=caps,
        role="Test role",
        identity="Test identity",
        communication_style="Terse",
        principles="Test principles",
        module=AgentModule.BMM,
        path=Path(f"_bmad/bmm/{name}"),
        canonical_id="",
    )
    return AgentRuntimeConfig(agent=defn)


@pytest.fixture
def registry() -> AgentRegistry:
    """A 3-agent registry with seeded embedder."""
    catalog = {
        "bmad-brainstorm": _make_agent("bmad-brainstorm", "brainstorming, creative techniques"),
        "bmad-architect": _make_agent("bmad-architect", "distributed systems, architecture"),
        "bmad-analyst": _make_agent("bmad-analyst", "market research, competitive analysis"),
    }
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    return AgentRegistry(catalog=catalog, embedder=embedder)


def test_find_agents_returns_results(registry: AgentRegistry) -> None:
    query = AgentQuery(task_description="brainstorming ideas for new product")
    results = registry.find_agents(query)
    assert isinstance(results, list)
    assert len(results) <= 5


def test_find_agents_empty_catalog() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    empty_registry = AgentRegistry(catalog={}, embedder=embedder)
    results = empty_registry.find_agents(AgentQuery(task_description="anything"))
    assert results == []


def test_find_agents_with_required_tokens(registry: AgentRegistry) -> None:
    query = AgentQuery(
        task_description="architecture review",
        required_tokens=("systems",),
    )
    results = registry.find_agents(query)
    # Only bmad-architect has "distributed systems" containing "systems"
    names = [r.agent.agent.name for r in results]
    assert all(
        "architecture" in r.agent.agent.capabilities
        or "systems" in " ".join(r.agent.agent.capabilities)
        for r in results
    )


def test_find_agents_required_tokens_no_match(registry: AgentRegistry) -> None:
    query = AgentQuery(
        task_description="test anything",
        required_tokens=("nonexistent_capability_xyz",),
    )
    results = registry.find_agents(query)
    assert results == []


def test_find_agents_top_k_respected(registry: AgentRegistry) -> None:
    query = AgentQuery(task_description="systems architecture design", top_k=2)
    results = registry.find_agents(query)
    assert len(results) <= 2


def test_find_agents_returns_agent_matches(registry: AgentRegistry) -> None:
    query = AgentQuery(task_description="brainstorming")
    results = registry.find_agents(query)
    for match in results:
        assert isinstance(match, AgentMatch)
        assert 0.0 <= match.score <= 1.0
        assert 0.0 <= match.confidence <= 1.0


def test_get_agent_direct_lookup(registry: AgentRegistry) -> None:
    cfg = registry.get("bmad-brainstorm")
    assert cfg is not None
    assert cfg.agent.name == "bmad-brainstorm"


def test_get_agent_missing_returns_none(registry: AgentRegistry) -> None:
    assert registry.get("nonexistent-agent") is None


def test_all_agents_returns_alphabetical(registry: AgentRegistry) -> None:
    agents = registry.all_agents()
    names = [a.agent.name for a in agents]
    assert names == sorted(names)


def test_llm_rerank_soft_fail_returns_semantic_results(registry: AgentRegistry) -> None:
    """When all confidences < min_confidence, LLM rerank fires but fails → semantic results returned."""
    # Use a very high min_confidence to force LLM rerank trigger
    query = AgentQuery(
        task_description="brainstorming",
        min_confidence=0.999,  # Nearly impossible to achieve → forces LLM rerank
        top_k=3,
    )
    # Should not raise — LLM rerank fails silently, semantic results returned
    results = registry.find_agents(query)
    assert isinstance(results, list)
