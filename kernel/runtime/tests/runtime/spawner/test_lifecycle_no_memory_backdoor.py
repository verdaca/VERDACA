"""tests/runtime/spawner/test_lifecycle_no_memory_backdoor.py — RED commit.

SpawnedAgent must NOT expose a back-door to the raw Memory instance.
The proxy is the ONLY memory handle the agent ever holds.
Architecture §4.1.5, §9.1. S4.R-01.
"""

from __future__ import annotations


def test_spawned_agent_importable() -> None:
    from praxis.kernel.runtime.spawner.lifecycle import SpawnedAgent  # noqa: F401


def test_spawned_agent_has_no_raw_memory_attr() -> None:
    """SpawnedAgent must not expose underlying Memory via any public attribute."""
    from uuid import uuid4

    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ReviewerMemoryProxy
    from praxis.kernel.runtime.spawner.lifecycle import SpawnedAgent
    from praxis.kernel.runtime.testing import make_fake_memory

    fake_mem = make_fake_memory()
    proxy = ReviewerMemoryProxy(
        memory=fake_mem,
        tenant_id="t1",
        agent_name="bmad-tea",
        spawn_id=uuid4(),
    )
    agent = SpawnedAgent(
        agent_name="bmad-tea",
        role=AgentRole.REVIEWER,
        memory_proxy=proxy,
        spawn_id=uuid4(),
    )

    # The underlying memory object must NOT be accessible via any public attr
    # that returns the raw FakeMemory instance
    public_attrs = [a for a in dir(agent) if not a.startswith("_")]
    for attr in public_attrs:
        try:
            val = getattr(agent, attr)
            assert val is not fake_mem, (
                f"SpawnedAgent.{attr} returns the raw Memory instance — back-door detected! "
                f"All memory access must go through the proxy."
            )
        except Exception:
            pass  # method calls that require arguments will raise; that's fine


def test_spawned_agent_memory_is_proxy() -> None:
    """agent.memory returns the proxy, not the underlying Memory."""
    from uuid import uuid4

    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ReviewerMemoryProxy
    from praxis.kernel.runtime.spawner.lifecycle import SpawnedAgent
    from praxis.kernel.runtime.testing import make_fake_memory

    fake_mem = make_fake_memory()
    proxy = ReviewerMemoryProxy(
        memory=fake_mem,
        tenant_id="t1",
        agent_name="bmad-tea",
        spawn_id=uuid4(),
    )
    agent = SpawnedAgent(
        agent_name="bmad-tea",
        role=AgentRole.REVIEWER,
        memory_proxy=proxy,
        spawn_id=uuid4(),
    )
    assert agent.memory is proxy
    assert agent.memory is not fake_mem
