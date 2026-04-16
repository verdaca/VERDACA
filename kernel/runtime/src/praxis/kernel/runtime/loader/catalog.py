"""Praxis Runtime loader — tool library catalog.

ANCHORED on architecture §6 Carson P0 (8 tools) + P1 (15 tools) = 23 total.
NO P2 tools registered at launch (architecture §6.3, §6.5 hard constraint).

Every entry reflects Carson's §5.4 intake protocol fields:
  name, mcp_server_id, blast_class, priority,
  primary_caller_agents, compliance_flags.

Architecture references:
  architecture.md §6.1 (P0 cards)
  architecture.md §6.2 (P1 summary)
  architecture.md §6.3 (P2 — reference only, NOT here)
  architecture.md §9.5 (sandbox policy per class)
"""

from __future__ import annotations

from praxis.kernel.runtime.tools._base import (
    ToolBlastRadiusClass,
    ToolDescriptor,
    ToolPriority,
)

# ---------------------------------------------------------------------------
# P0 — Launch-Binding Tools (8)
# ---------------------------------------------------------------------------

_P0_TOOLS: list[ToolDescriptor] = [
    # §6.1.1 Filesystem
    ToolDescriptor(
        name="fs-mcp",
        mcp_server_id="mcp-server-filesystem",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=True,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-tech-writer",
            "bmad-agent-qa",
            "bmad-cis-agent-presentation-master",
        ),
        compliance_flags=("R11", "R36"),
        description="Official Anthropic mcp-server-filesystem. Workspace-bounded.",
    ),
    # §6.1.2 Tavily
    ToolDescriptor(
        name="tavily-mcp",
        mcp_server_id="tavily-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-analyst",
            "bmad-cis-agent-innovation-strategist",
            "bmad-agent-pm",
            "bmad-cis-agent-creative-problem-solver",
            "bmad-cis-agent-storyteller",
        ),
        compliance_flags=("R31", "R57"),
        description="Official Tavily search MCP. CostEvent emission mandatory per R57.",
    ),
    # §6.1.3 GitHub
    ToolDescriptor(
        name="github-mcp",
        mcp_server_id="github-mcp-server",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=True,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-qa",
            "bmad-tea",
            "bmad-agent-architect",
            "bmad-agent-sm",
            "bmad-agent-tech-writer",
        ),
        compliance_flags=("R11", "R31"),
        description="Official GitHub MCP. Secret-scanning redaction on file contents.",
    ),
    # §6.1.4 Context7
    ToolDescriptor(
        name="context7-mcp",
        mcp_server_id="context7-mcp",
        blast_class=ToolBlastRadiusClass.A,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-architect",
            "bmad-agent-dev",
            "bmad-agent-qa",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-tech-writer",
        ),
        compliance_flags=("R31", "R57"),
        description="Official Upstash Context7 library-docs MCP. Class A inert.",
    ),
    # §6.1.5 Playwright
    ToolDescriptor(
        name="playwright-mcp",
        mcp_server_id="@playwright/mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=False,  # write mode P2-capped per §9.3
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-qa",
            "bmad-agent-ux-designer",
            "bmad-agent-analyst",
            "bmad-tea",
            "bmad-agent-quick-flow-solo-dev",
        ),
        compliance_flags=("R31", "R36"),
        description="Microsoft Playwright MCP. Read-only at launch; write P2-capped.",
    ),
    # §6.1.6 PostgreSQL
    ToolDescriptor(
        name="postgres-mcp",
        mcp_server_id="postgres-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=True,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-qa",
            "bmad-agent-analyst",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-tea",
        ),
        compliance_flags=("R11", "R31"),
        description="Crystal DBA postgres-mcp. Typed query builder; no raw SQL.",
    ),
    # §6.1.7a Python Sandbox (Class C, broad allowlist)
    ToolDescriptor(
        name="python-sandbox-mcp",
        mcp_server_id="python-sandbox-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-qa",
            "bmad-tea",
            "bmad-agent-analyst",
            "bmad-agent-tech-writer",
            "bmad-cis-agent-creative-problem-solver",
            "bmad-cis-agent-innovation-strategist",
        ),
        compliance_flags=("R11", "R31", "R57"),
        description=(
            "Containerized Python execution (E2B/Daytona). "
            "No network by default. CPU/memory/wall-time bounded by ResourceBudget. "
            "Class C — containerized, not host-accessible."
        ),
    ),
    # §6.1.7b Subprocess (Class D, only admitted Class D at launch)
    ToolDescriptor(
        name="subprocess-mcp",
        mcp_server_id="subprocess-mcp",
        blast_class=ToolBlastRadiusClass.D,
        priority=ToolPriority.P0,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-qa",
        ),
        compliance_flags=("R11", "R31", "R57"),
        description=(
            "Bounded binary execution. Per-binary allowlist: "
            "pytest/ruff/mypy/python/pip/npm/node only. "
            "Amelia/Barry/Quinn agents only. Class D sole admission exception."
        ),
    ),
    # §6.1.8 OpenTelemetry Exporter (R53 enforcement point)
    ToolDescriptor(
        name="otel-exporter-mcp",
        mcp_server_id="otel-exporter-mcp",
        blast_class=ToolBlastRadiusClass.A,
        priority=ToolPriority.P0,
        read_mode_capable=False,
        write_mode_capable=True,
        default_mode="write-only",
        primary_caller_agents=tuple(),  # all 16 agents via framework integration
        compliance_flags=("R51", "R53", "R54"),
        description=(
            "OTel exporter. THIS IS THE R53 ENFORCEMENT POINT. "
            "Frozen+extra=forbid at emit() boundary. "
            "Only allowlisted fields (7) accepted."
        ),
    ),
]

# ---------------------------------------------------------------------------
# P1 — Strong Candidates (15)
# ---------------------------------------------------------------------------

_P1_TOOLS: list[ToolDescriptor] = [
    ToolDescriptor(
        name="jira-mcp",
        mcp_server_id="jira-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-agent-sm", "bmad-tea", "bmad-agent-tech-writer"),
        compliance_flags=("R31",),
        description="Jira MCP. Read-only at launch.",
    ),
    ToolDescriptor(
        name="confluence-mcp",
        mcp_server_id="confluence-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-tech-writer",
            "bmad-agent-analyst",
            "bmad-cis-agent-creative-problem-solver",
        ),
        compliance_flags=("R31",),
        description="Confluence MCP. R53 at tool boundary (large content).",
    ),
    ToolDescriptor(
        name="slack-mcp",
        mcp_server_id="slack-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-sm",
            "bmad-agent-analyst",
            "bmad-agent-pm",
        ),
        compliance_flags=("R31",),
        description="Slack MCP (read + write, NOT webhook-only). Per-channel allowlist critical.",
    ),
    ToolDescriptor(
        name="k8s-mcp",
        mcp_server_id="k8s-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,  # write P2-capped per §9.3
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-tea",
            "bmad-agent-architect",
        ),
        compliance_flags=("R11", "R31"),
        description="Kubernetes MCP. Destructive ops P2-capped.",
    ),
    ToolDescriptor(
        name="observability-mcp",
        mcp_server_id="observability-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-tea", "bmad-cis-agent-creative-problem-solver"),
        compliance_flags=("R53",),
        description="Datadog/Grafana/Prometheus MCP. Dashboards may contain PII → R53.",
    ),
    ToolDescriptor(
        name="docker-mcp",
        mcp_server_id="docker-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-qa",
            "bmad-agent-quick-flow-solo-dev",
        ),
        compliance_flags=("R11",),
        description="Docker MCP. Read-only. Image pull from untrusted registries guarded.",
    ),
    ToolDescriptor(
        name="stripe-mcp",
        mcp_server_id="stripe-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-agent-analyst", "bmad-cis-agent-innovation-strategist"),
        compliance_flags=("R31",),
        description="Stripe MCP. PCI-adjacent. Customer PII.",
    ),
    ToolDescriptor(
        name="notion-mcp",
        mcp_server_id="notion-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-tech-writer",
            "bmad-agent-analyst",
            "bmad-agent-ux-designer",
        ),
        compliance_flags=("R31",),
        description="Notion MCP. Broad workspace access guard.",
    ),
    ToolDescriptor(
        name="gitlab-mcp",
        mcp_server_id="gitlab-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
            "bmad-agent-qa",
        ),
        compliance_flags=("R11", "R31"),
        description="GitLab MCP (alternative to GitHub).",
    ),
    ToolDescriptor(
        name="pagerduty-mcp",
        mcp_server_id="pagerduty-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-tea", "bmad-cis-agent-creative-problem-solver"),
        compliance_flags=("R31",),
        description="PagerDuty MCP. Incident data sensitivity.",
    ),
    ToolDescriptor(
        name="security-scanner-mcp",
        mcp_server_id="security-scanner-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-tea", "bmad-agent-dev"),
        compliance_flags=("R11",),
        description="Semgrep/Trivy/Snyk security scanner MCP.",
    ),
    ToolDescriptor(
        name="vault-mcp",
        mcp_server_id="vault-mcp",
        blast_class=ToolBlastRadiusClass.C,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,  # write P2-capped per §9.3
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-dev",
            "bmad-agent-quick-flow-solo-dev",
        ),
        compliance_flags=("R31",),
        description="Vault MCP (read-only). Mis-config = total compromise.",
    ),
    ToolDescriptor(
        name="sec-edgar-mcp",
        mcp_server_id="sec-edgar-mcp",
        blast_class=ToolBlastRadiusClass.A,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=("bmad-agent-analyst", "bmad-cis-agent-innovation-strategist"),
        compliance_flags=(),
        description="SEC EDGAR MCP. Public data only — Class A inert.",
    ),
    ToolDescriptor(
        name="google-workspace-mcp",
        mcp_server_id="google-workspace-mcp",
        blast_class=ToolBlastRadiusClass.B,
        priority=ToolPriority.P1,
        read_mode_capable=True,
        write_mode_capable=False,
        default_mode="read-only",
        primary_caller_agents=(
            "bmad-agent-analyst",
            "bmad-agent-pm",
            "bmad-agent-tech-writer",
        ),
        compliance_flags=("R31",),
        description="Google Workspace MCP. OAuth scope sprawl risk.",
    ),
    ToolDescriptor(
        name="otel-collector-mcp",
        mcp_server_id="otel-collector-mcp",
        blast_class=ToolBlastRadiusClass.A,
        priority=ToolPriority.P1,
        read_mode_capable=False,
        write_mode_capable=True,
        default_mode="write-only",
        primary_caller_agents=("bmad-tea",),
        compliance_flags=("R53",),
        description="OTel Collector MCP write-side. Same R53 discipline as P0-8.",
    ),
]

# ---------------------------------------------------------------------------
# Combined catalog — 8 P0 + 15 P1 = 23 tools
# ---------------------------------------------------------------------------

TOOL_CATALOG: tuple[ToolDescriptor, ...] = tuple(_P0_TOOLS + _P1_TOOLS)

__all__ = ["TOOL_CATALOG"]
