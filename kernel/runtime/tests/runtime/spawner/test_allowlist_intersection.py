"""tests/runtime/spawner/test_allowlist_intersection.py — RED commit.

Parent-child allowlist intersection (architecture §9.7).
Q5 metric: runtime.agent.allowlist.stripped.count.
"""

from __future__ import annotations


def test_compute_child_allowlist_importable() -> None:
    from praxis.kernel.runtime.spawner.spawner import compute_child_allowlist  # noqa: F401


def test_child_allowlist_is_parent_intersection() -> None:
    """Child allowlist = parent ∩ child_baseline (architecture §9.7)."""
    from praxis.kernel.runtime.spawner.spawner import compute_child_allowlist

    parent = frozenset({"fs-mcp:read", "github-mcp:read"})
    child_baseline = frozenset({"fs-mcp:read", "github-mcp:read", "subprocess-mcp", "tavily-mcp"})

    effective = compute_child_allowlist(parent_allowlist=parent, child_baseline=child_baseline)
    assert effective == frozenset({"fs-mcp:read", "github-mcp:read"})


def test_child_broader_than_parent_stripped() -> None:
    from praxis.kernel.runtime.spawner.spawner import compute_child_allowlist

    parent = frozenset({"fs-mcp:read"})
    child_baseline = frozenset({"fs-mcp:read", "fs-mcp:write", "subprocess-mcp"})

    effective = compute_child_allowlist(parent_allowlist=parent, child_baseline=child_baseline)
    # Only fs-mcp:read is in both
    assert effective == frozenset({"fs-mcp:read"})
    assert "fs-mcp:write" not in effective
    assert "subprocess-mcp" not in effective


def test_allowlist_intersection_returns_frozenset() -> None:
    from praxis.kernel.runtime.spawner.spawner import compute_child_allowlist

    result = compute_child_allowlist(
        parent_allowlist=frozenset({"fs-mcp:read"}),
        child_baseline=frozenset({"fs-mcp:read", "tavily-mcp"}),
    )
    assert isinstance(result, frozenset)


def test_compute_stripped_tools_returns_difference() -> None:
    from praxis.kernel.runtime.spawner.spawner import compute_stripped_tools

    parent = frozenset({"fs-mcp:read"})
    child_baseline = frozenset({"fs-mcp:read", "tavily-mcp", "subprocess-mcp"})

    stripped = compute_stripped_tools(parent_allowlist=parent, child_baseline=child_baseline)
    assert stripped == frozenset({"tavily-mcp", "subprocess-mcp"})
