"""tests/runtime/loader/test_catalog_anchoring.py — GREEN commit.

Tests that TOOL_CATALOG is anchored exclusively on architecture §6 P0+P1.
No P2 tools at launch. 8 P0 + 15 P1 = 23 tools total.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass, ToolPriority

_P0_TOOL_NAMES = {
    "fs-mcp",
    "tavily-mcp",
    "github-mcp",
    "context7-mcp",
    "playwright-mcp",
    "postgres-mcp",
    "python-sandbox-mcp",
    "subprocess-mcp",
    "otel-exporter-mcp",
}

_P1_TOOL_NAMES = {
    "jira-mcp",
    "confluence-mcp",
    "slack-mcp",
    "k8s-mcp",
    "observability-mcp",
    "docker-mcp",
    "stripe-mcp",
    "notion-mcp",
    "gitlab-mcp",
    "pagerduty-mcp",
    "security-scanner-mcp",
    "vault-mcp",
    "sec-edgar-mcp",
    "google-workspace-mcp",
    "otel-collector-mcp",
}

_P2_TOOL_SAMPLE = {"terraform-mcp", "aws-cli-mcp", "salesforce-mcp"}

_EXPECTED_P0_COUNT = 9  # P0-7 was split into 7a (python-sandbox) + 7b (subprocess)
_EXPECTED_P1_COUNT = 15


def test_catalog_importable() -> None:
    assert isinstance(TOOL_CATALOG, tuple)
    assert len(TOOL_CATALOG) > 0


def test_p0_tool_count() -> None:
    p0 = [t for t in TOOL_CATALOG if t.priority == ToolPriority.P0]
    assert len(p0) == _EXPECTED_P0_COUNT, (
        f"Expected {_EXPECTED_P0_COUNT} P0 tools, got {len(p0)}: {[t.name for t in p0]}"
    )


def test_p1_tool_count() -> None:
    p1 = [t for t in TOOL_CATALOG if t.priority == ToolPriority.P1]
    assert len(p1) == _EXPECTED_P1_COUNT, (
        f"Expected {_EXPECTED_P1_COUNT} P1 tools, got {len(p1)}: {[t.name for t in p1]}"
    )


def test_no_p2_tools_registered() -> None:
    p2 = [t for t in TOOL_CATALOG if t.priority == ToolPriority.P2]
    assert not p2, f"P2 tools must not be registered at launch: {[t.name for t in p2]}"


def test_all_p0_tools_present() -> None:
    catalog_p0_names = {t.name for t in TOOL_CATALOG if t.priority == ToolPriority.P0}
    missing = _P0_TOOL_NAMES - catalog_p0_names
    assert not missing, f"Missing P0 tools: {missing}"


def test_all_p1_tools_present() -> None:
    catalog_p1_names = {t.name for t in TOOL_CATALOG if t.priority == ToolPriority.P1}
    missing = _P1_TOOL_NAMES - catalog_p1_names
    assert not missing, f"Missing P1 tools: {missing}"


def test_no_known_p2_tools_in_catalog() -> None:
    catalog_names = {t.name for t in TOOL_CATALOG}
    unexpected = _P2_TOOL_SAMPLE & catalog_names
    assert not unexpected, f"P2 tools found in catalog (scope creep): {unexpected}"


def test_each_tool_has_required_intake_fields() -> None:
    """Each tool descriptor carries Carson §5.4 intake protocol fields."""
    for tool in TOOL_CATALOG:
        assert tool.name, "Tool missing name"
        assert tool.mcp_server_id, f"{tool.name}: missing mcp_server_id"
        assert tool.blast_class, f"{tool.name}: missing blast_class"
        # otel-exporter-mcp intentionally has no primary_caller_agents (framework-level)
        if tool.name != "otel-exporter-mcp":
            assert tool.primary_caller_agents, f"{tool.name}: missing primary_caller_agents"


def test_no_class_e_tools_admitted() -> None:
    """Class E (unbounded) tools are never admitted per architecture §9.5."""
    class_e = [t for t in TOOL_CATALOG if t.blast_class == ToolBlastRadiusClass.E]
    assert not class_e, f"Class E tools must never be admitted: {[t.name for t in class_e]}"


def test_total_catalog_size() -> None:
    assert len(TOOL_CATALOG) == _EXPECTED_P0_COUNT + _EXPECTED_P1_COUNT, (
        f"Expected {_EXPECTED_P0_COUNT + _EXPECTED_P1_COUNT} total, got {len(TOOL_CATALOG)}"
    )
