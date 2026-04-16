"""Stage 4.4 Quinn checkpoint — All 16 agents spawn successfully.

Verifies that every agent in _bmad/_config/agent-manifest.csv can be loaded
and that a memory proxy (ProducerMemoryProxy or ReviewerMemoryProxy) is
constructable for each agent without error.

Architecture §4.1.5, §9.1.1. Stage 4 Pipeline.md checkpoint: "All 16 agents
spawn successfully."
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[7]  # .../Anthropic/
_MANIFEST_PATH = _REPO_ROOT / "_bmad" / "_config" / "agent-manifest.csv"

_EXPECTED_AGENT_COUNT = 16


@pytest.mark.critical
def test_manifest_loads_16_agents() -> None:
    """All 16 agents are present in the manifest before spawn attempt."""
    from praxis.kernel.runtime.loader.manifest import AgentLoader

    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    assert len(catalog) == _EXPECTED_AGENT_COUNT, (
        f"Expected {_EXPECTED_AGENT_COUNT} agents in manifest, got {len(catalog)}: "
        f"{sorted(catalog.keys())}"
    )


@pytest.mark.critical
def test_all_16_agents_spawn_with_producer_proxy() -> None:
    """Each of the 16 agents can be spawned with a ProducerMemoryProxy.

    Stage 4 Pipeline.md § 4.4 checkpoint: 'All 16 agents spawn successfully.'
    """
    from praxis.kernel.runtime.loader.manifest import AgentLoader
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ProducerMemoryProxy
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    manifest = make_test_manifest()
    memory = make_fake_memory()

    failed: list[str] = []
    for agent_name in sorted(catalog.keys()):
        try:
            proxy = _construct_proxy_for_role(
                role=AgentRole.PRODUCER,
                memory=memory,
                tenant_id=manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=uuid4(),
            )
            assert isinstance(proxy, ProducerMemoryProxy), (
                f"{agent_name}: expected ProducerMemoryProxy, got {type(proxy).__name__}"
            )
        except Exception as exc:
            failed.append(f"{agent_name}: {exc}")

    assert not failed, (
        f"The following agents failed to spawn:\n" + "\n".join(f"  - {f}" for f in failed)
    )


@pytest.mark.critical
def test_all_16_agents_spawn_with_reviewer_proxy() -> None:
    """Each of the 16 agents can be spawned with a ReviewerMemoryProxy.

    Reviewer spawn is the information-asymmetry path. Every agent must be
    spawnable as a reviewer so that the orchestrator can assign either role
    without agent-specific restrictions.
    """
    from praxis.kernel.runtime.loader.manifest import AgentLoader
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ReviewerMemoryProxy
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    manifest = make_test_manifest()
    memory = make_fake_memory()

    failed: list[str] = []
    for agent_name in sorted(catalog.keys()):
        try:
            proxy = _construct_proxy_for_role(
                role=AgentRole.REVIEWER,
                memory=memory,
                tenant_id=manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=uuid4(),
            )
            assert isinstance(proxy, ReviewerMemoryProxy), (
                f"{agent_name}: expected ReviewerMemoryProxy, got {type(proxy).__name__}"
            )
        except Exception as exc:
            failed.append(f"{agent_name}: {exc}")

    assert not failed, (
        f"The following agents failed reviewer spawn:\n" + "\n".join(f"  - {f}" for f in failed)
    )


@pytest.mark.critical
def test_spawn_count_equals_16() -> None:
    """Exactly 16 successful spawns — no more, no fewer.

    Guards against manifest growing or shrinking without an explicit
    _EXPECTED_AGENT_COUNT update.
    """
    from praxis.kernel.runtime.loader.manifest import AgentLoader
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    loader = AgentLoader(manifest_path=_MANIFEST_PATH)
    catalog = loader.load()
    manifest = make_test_manifest()
    memory = make_fake_memory()

    success_count = 0
    for agent_name in catalog:
        proxy = _construct_proxy_for_role(
            role=AgentRole.PRODUCER,
            memory=memory,
            tenant_id=manifest.tenant_id,
            agent_name=agent_name,
            spawn_id=uuid4(),
        )
        if proxy is not None:
            success_count += 1

    assert success_count == _EXPECTED_AGENT_COUNT, (
        f"Expected {_EXPECTED_AGENT_COUNT} successful spawns, got {success_count}"
    )
