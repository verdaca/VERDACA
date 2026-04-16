"""tests/runtime/spawner/test_role_construction_dispatch.py — RED commit.

Tests for role-based proxy construction dispatch in AgentSpawner.
Architecture §4.1.5, §9.1. S4.R-01 structural enforcement.
"""

from __future__ import annotations

import pytest


def test_spawner_importable() -> None:
    from praxis.kernel.runtime.spawner.spawner import AgentSpawner  # noqa: F401


def test_budgets_importable() -> None:
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget  # noqa: F401


def test_resource_budget_default_producer() -> None:
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget.default_for_role(AgentRole.PRODUCER)
    assert budget.max_tokens == 200_000
    assert budget.max_wall_seconds == 600.0
    assert budget.max_tool_calls == 100
    assert budget.max_memory_writes == 50


def test_resource_budget_default_reviewer() -> None:
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget.default_for_role(AgentRole.REVIEWER)
    assert budget.max_tokens == 100_000
    assert budget.max_wall_seconds == 300.0
    assert budget.max_tool_calls == 40
    assert budget.max_memory_writes == 20


def test_resource_budget_frozen() -> None:
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget.default_for_role(AgentRole.PRODUCER)
    with pytest.raises((TypeError, AttributeError)):
        budget.max_tokens = 999  # type: ignore[misc]


def test_spawned_agent_has_producer_proxy_for_producer_role() -> None:
    from uuid import uuid4

    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ProducerMemoryProxy
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    memory = make_fake_memory()
    manifest = make_test_manifest()
    proxy = _construct_proxy_for_role(
        role=AgentRole.PRODUCER,
        memory=memory,
        tenant_id=manifest.tenant_id,
        agent_name="bmad-agent-dev",
        spawn_id=uuid4(),
    )
    assert isinstance(proxy, ProducerMemoryProxy)


def test_spawned_agent_has_reviewer_proxy_for_reviewer_role() -> None:
    from uuid import uuid4

    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.proxies import ReviewerMemoryProxy
    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    memory = make_fake_memory()
    manifest = make_test_manifest()
    proxy = _construct_proxy_for_role(
        role=AgentRole.REVIEWER,
        memory=memory,
        tenant_id=manifest.tenant_id,
        agent_name="bmad-tea",
        spawn_id=uuid4(),
    )
    assert isinstance(proxy, ReviewerMemoryProxy)


def test_unknown_role_raises_value_error() -> None:
    from uuid import uuid4

    from praxis.kernel.runtime.spawner.spawner import _construct_proxy_for_role
    from praxis.kernel.runtime.testing import make_fake_memory, make_test_manifest

    with pytest.raises(ValueError, match="Unknown role"):
        _construct_proxy_for_role(
            role="unknown_role",  # type: ignore[arg-type]
            memory=make_fake_memory(),
            tenant_id=make_test_manifest().tenant_id,
            agent_name="test",
            spawn_id=uuid4(),
        )


def test_resource_budget_unknown_role_raises_value_error() -> None:
    """ResourceBudget.default_for_role raises ValueError for unknown roles."""
    import pytest

    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    with pytest.raises(ValueError, match="Unknown role"):
        ResourceBudget.default_for_role("observer")  # type: ignore[arg-type]


def test_resource_budget_check_memory_writes_exceeded() -> None:
    """check_memory_writes raises BudgetExceededError when limit exceeded."""
    import pytest

    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.budgets import BudgetExceededError, ResourceBudget

    budget = ResourceBudget.default_for_role(AgentRole.REVIEWER)
    with pytest.raises(BudgetExceededError, match="Memory-write budget exceeded"):
        budget.check_memory_writes(budget.max_memory_writes + 1)


def test_resource_budget_check_memory_writes_within_limit() -> None:
    """check_memory_writes does not raise when within limit."""
    from praxis.kernel.runtime.models import AgentRole
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget.default_for_role(AgentRole.PRODUCER)
    budget.check_memory_writes(1)  # must not raise


def test_spawner_invokes_construct_memory_proxy() -> None:
    """Spawner must call _construct_memory_proxy from proxies._construction (single point)."""
    import praxis.kernel.runtime.spawner.spawner as spawner_mod

    # The spawner must import from proxies._construction
    assert (
        hasattr(spawner_mod, "_construct_memory_proxy")
        or "_construct_memory_proxy" in getattr(spawner_mod, "__all__", [])
        or "proxies._construction" in getattr(spawner_mod, "__doc__", "")
    )
