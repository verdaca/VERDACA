"""tests/runtime/tools/test_subprocess_mcp_contract.py — RED commit.

Contract tests for subprocess-mcp. Architecture §6.1.7b. Class D.
Narrow per-binary allowlist. Tight agent allowlist (Amelia/Barry/Quinn only).
"""

from __future__ import annotations


def test_subprocess_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.subprocess_mcp import SubprocessMcpAdapter  # noqa: F401


def test_subprocess_mcp_descriptor_blast_class_d() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.subprocess_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.D


def test_subprocess_allowed_binaries() -> None:
    """Only pytest/ruff/mypy/python/pip/npm/node are admitted."""
    from praxis.kernel.runtime.tools.subprocess_mcp import is_binary_allowed

    assert is_binary_allowed("pytest")
    assert is_binary_allowed("ruff")
    assert is_binary_allowed("mypy")
    assert is_binary_allowed("python")
    assert is_binary_allowed("pip")
    assert is_binary_allowed("node")


def test_subprocess_denied_binaries() -> None:
    from praxis.kernel.runtime.tools.subprocess_mcp import is_binary_allowed

    assert not is_binary_allowed("curl")
    assert not is_binary_allowed("ssh")
    assert not is_binary_allowed("nc")
    assert not is_binary_allowed("sh")
    assert not is_binary_allowed("bash")
    assert not is_binary_allowed("cat")


def test_subprocess_agent_allowlist() -> None:
    """Only Amelia, Barry, Quinn may invoke subprocess."""
    from praxis.kernel.runtime.tools.subprocess_mcp import SUBPROCESS_AGENT_ALLOWLIST

    assert "bmad-agent-dev" in SUBPROCESS_AGENT_ALLOWLIST
    assert "bmad-agent-quick-flow-solo-dev" in SUBPROCESS_AGENT_ALLOWLIST
    assert "bmad-agent-qa" in SUBPROCESS_AGENT_ALLOWLIST
    # Other agents must not be in the allowlist
    assert "bmad-agent-analyst" not in SUBPROCESS_AGENT_ALLOWLIST
    assert "bmad-agent-architect" not in SUBPROCESS_AGENT_ALLOWLIST


def test_subprocess_agent_allowlist_is_frozen() -> None:
    from praxis.kernel.runtime.tools.subprocess_mcp import SUBPROCESS_AGENT_ALLOWLIST

    assert isinstance(SUBPROCESS_AGENT_ALLOWLIST, frozenset)


def test_check_binary_allowed_passes_for_allowed_binary() -> None:
    """check_binary_allowed() does not raise for permitted binaries."""
    from praxis.kernel.runtime.tools.subprocess_mcp import SubprocessMcpAdapter

    adapter = SubprocessMcpAdapter()
    adapter.check_binary_allowed("pytest")  # must not raise
    adapter.check_binary_allowed("ruff")
    adapter.check_binary_allowed("mypy")


def test_check_binary_allowed_raises_for_denied_binary() -> None:
    """check_binary_allowed() raises ToolNotAllowedError for unlisted binaries."""
    import pytest

    from praxis.kernel.runtime.tools._base import ToolNotAllowedError
    from praxis.kernel.runtime.tools.subprocess_mcp import SubprocessMcpAdapter

    adapter = SubprocessMcpAdapter()
    with pytest.raises(ToolNotAllowedError, match="not in allowlist"):
        adapter.check_binary_allowed("curl")


def test_check_agent_allowed_passes_for_allowed_agent() -> None:
    """check_agent_allowed() does not raise for Amelia/Barry/Quinn."""
    from praxis.kernel.runtime.tools.subprocess_mcp import SubprocessMcpAdapter

    adapter = SubprocessMcpAdapter()
    adapter.check_agent_allowed("bmad-agent-dev")  # Amelia
    adapter.check_agent_allowed("bmad-agent-qa")   # Quinn
    adapter.check_agent_allowed("bmad-agent-quick-flow-solo-dev")  # Barry


def test_check_agent_allowed_raises_for_disallowed_agent() -> None:
    """check_agent_allowed() raises ToolNotAllowedError for other agents."""
    import pytest

    from praxis.kernel.runtime.tools._base import ToolNotAllowedError
    from praxis.kernel.runtime.tools.subprocess_mcp import SubprocessMcpAdapter

    adapter = SubprocessMcpAdapter()
    with pytest.raises(ToolNotAllowedError, match="not in agent allowlist"):
        adapter.check_agent_allowed("bmad-agent-architect")
