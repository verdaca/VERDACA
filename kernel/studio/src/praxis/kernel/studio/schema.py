"""WorkflowTemplate schema — arch §2.

Defines the Pydantic model hierarchy that any Praxis product configuration
(Studio, Factory, Shield, Pipeline, Ops) can instantiate. The schema is
validated at load time; no template reaches the MAC without passing this check.

Binding anchors:
  - studio/architecture.md §2 Workflow Template Schema (all subsections)
  - studio/architecture.md §2.4 Schema Validation at Load Time
  - ADR-02: three rendering modes
  - ADR-08: MVP scope (markdown + html only; no PDF/pptx)
  - ADR-09: three provenance visibility modes
  - ADR-10: shareable-link model primitives
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums — arch §2.2
# ---------------------------------------------------------------------------


class RenderingMode(str, Enum):
    """ADR-02: three decision-shape rendering modes."""

    POSITION_TO_HOLD = "position_to_hold"
    """Founder-default — conditional position the founder can hold for two quarters."""

    DECISION_FRAMEWORK = "decision_framework"
    """COO-default — factor-weighted framework the team can execute against."""

    FIRM_VOICE = "firm_voice"
    """Consultancy-default — firm-voice deliverable at consultant-acceptable density."""


class ProvenanceMode(str, Enum):
    """ADR-09: three tool-provenance visibility modes."""

    FLEXIBLE = "flexible"
    """Small dismissible footer: 'Generated with Praxis'."""

    INSPECTABLE = "inspectable"
    """Expandable 'How this analysis was generated' section."""

    INVISIBLE = "invisible"
    """No Studio identifiers anywhere in rendered text, file metadata, or HTML comments."""


PROVENANCE_DEFAULTS: dict[RenderingMode, ProvenanceMode] = {
    RenderingMode.POSITION_TO_HOLD: ProvenanceMode.FLEXIBLE,
    RenderingMode.DECISION_FRAMEWORK: ProvenanceMode.INSPECTABLE,
    RenderingMode.FIRM_VOICE: ProvenanceMode.INVISIBLE,
}
"""Inferred provenance default per rendering mode (arch §2.2 PROVENANCE_DEFAULTS)."""


# ---------------------------------------------------------------------------
# Supporting models — arch §2.2
# ---------------------------------------------------------------------------


class AgentAssignment(BaseModel):
    """A single agent assigned to a cycle role."""

    model_config = ConfigDict(frozen=True)

    role: str
    """Human-readable role label, e.g. 'market_researcher'."""

    agent_id: str
    """Maps to BMAD agent-manifest.csv agent_id."""

    output_label: str
    """What this agent's output is called in the cycle — used by depends_on refs."""

    depends_on: tuple[str, ...] = ()
    """output_labels from prior agents this one needs. Empty = no dependency."""


class CycleSpec(BaseModel):
    """One deliberation cycle within the workflow."""

    model_config = ConfigDict(frozen=True)

    name: str
    """Cycle name, e.g. 'wide_survey', 'deep_analysis', 'red_team_synthesis'."""

    budget_pct: int
    """Percentage of total budget allocated to this cycle. Must sum to 100 across cycles."""

    agents: tuple[AgentAssignment, ...]
    """Ordered agent assignments within this cycle."""

    parallel: bool = True
    """If True, agents within this cycle run in parallel (default). Otherwise sequential."""

    asymmetry: bool = False
    """If True, agents do NOT see each other's outputs (information asymmetry)."""

    skip_in_quick_mode: bool = False
    """If True, this cycle is skipped when the template is run in quick mode."""

    reviewer_count: int = 1
    """MAC PhaseDAG reviewer_count override for this cycle."""


class QualityGateSpec(BaseModel):
    """Configuration for one MAC quality gate."""

    model_config = ConfigDict(frozen=True)

    gate_id: Literal["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12"]
    """Must match mac/quality-rubric.md gate identifiers. R13 deferred per arch §5.2."""

    min_score: int = 3
    """Minimum passing score on 1–5 scale."""

    weight_override: int | None = None
    """Override default weight from rubric. None = use rubric default."""

    section_routing: str | None = None
    """Req-B section to evaluate. None = use default routing."""


class OutputSpec(BaseModel):
    """One output format specification."""

    model_config = ConfigDict(frozen=True)

    format: Literal["markdown", "html"]
    """ADR-08 MVP scope: markdown and html only. PDF/pptx deferred to Stage 7."""

    template_path: str
    """Path to Jinja2 template relative to studio/templates/."""

    rendering_mode: RenderingMode
    """ADR-02: which decision-shape to render."""


class ShareableLinkSpec(BaseModel):
    """ADR-10: shareable-link model primitives."""

    model_config = ConfigDict(frozen=True)

    auth_gated: bool = True
    """Always True in 6.1 MVP."""

    default_expiry_days: int = 30
    """Configurable per-link at generation time."""

    owner_revocable: bool = True
    """Always True."""


class InputParamSpec(BaseModel):
    """One input parameter definition with type, constraints, and default."""

    model_config = ConfigDict(frozen=True)

    type: Literal["string", "int", "float", "bool", "enum"]
    """Python-style type identifier."""

    required: bool = True

    default: str | int | float | bool | None = None

    description: str

    enum_values: tuple[str, ...] | None = None
    """Required when type='enum'."""

    max_length: int | None = None
    """Applies to type='string' only."""

    @model_validator(mode="after")
    def _enum_values_required_for_enum_type(self) -> "InputParamSpec":
        if self.type == "enum" and not self.enum_values:
            raise ValueError("enum_values is required when type is 'enum'")
        return self


# ---------------------------------------------------------------------------
# Top-level template model — arch §2.2
# ---------------------------------------------------------------------------

class WorkflowTemplate(BaseModel):
    """Top-level workflow template. Validated at load time via model_validate()."""

    model_config = ConfigDict(frozen=True)

    name: str
    product: str
    """'studio', 'factory', 'shield', 'pipeline', or 'ops'."""

    description: str
    version: str
    """Semver string."""

    inputs: dict[str, InputParamSpec]
    """Parameter definitions — keys are parameter names."""

    rendering_mode: RenderingMode
    """ADR-02 — required."""

    provenance_mode: ProvenanceMode | None = None
    """ADR-09 — None = infer from rendering_mode via resolved_provenance_mode()."""

    cycles: tuple[CycleSpec, ...]
    """Ordered cycle definitions."""

    quality_gates: tuple[QualityGateSpec, ...]
    """Active gate specifications (subset of R1-R12 relevant to this workflow)."""

    outputs: tuple[OutputSpec, ...]
    """Output format specifications."""

    shareable_links: ShareableLinkSpec = Field(default_factory=ShareableLinkSpec)

    cost_budget_usd: float
    """Total budget ceiling for this workflow invocation."""

    timeout_seconds: float
    """Wall-clock timeout for the entire workflow."""

    # ------------------------------------------------------------------
    # Public method — arch §2.2
    # ------------------------------------------------------------------

    def resolved_provenance_mode(self) -> ProvenanceMode:
        """Return the effective provenance mode, inferring from rendering_mode if not set."""
        if self.provenance_mode is not None:
            return self.provenance_mode
        return PROVENANCE_DEFAULTS[self.rendering_mode]

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _cost_budget_positive(self) -> "WorkflowTemplate":
        if self.cost_budget_usd <= 0:
            raise ValueError(
                f"cost_budget_usd must be positive, got {self.cost_budget_usd}"
            )
        return self

    @model_validator(mode="after")
    def _timeout_positive(self) -> "WorkflowTemplate":
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )
        return self

    @model_validator(mode="after")
    def _no_duplicate_gate_ids(self) -> "WorkflowTemplate":
        seen: set[str] = set()
        for gate in self.quality_gates:
            if gate.gate_id in seen:
                raise ValueError(f"Duplicate gate_id in quality_gates: {gate.gate_id!r}")
            seen.add(gate.gate_id)
        return self

    @model_validator(mode="after")
    def _budget_pct_sums_to_100(self) -> "WorkflowTemplate":
        total = sum(c.budget_pct for c in self.cycles)
        if total != 100:
            raise ValueError(
                f"budget_pct across all cycles must sum to 100, got {total}"
            )
        return self

    @model_validator(mode="after")
    def _depends_on_references_valid(self) -> "WorkflowTemplate":
        """All depends_on refs must name an output_label defined by a prior agent."""
        defined: set[str] = set()
        for cycle in self.cycles:
            for agent in cycle.agents:
                for dep in agent.depends_on:
                    if dep not in defined:
                        raise ValueError(
                            f"Agent {agent.role!r} in cycle {cycle.name!r} depends_on "
                            f"{dep!r} which has not been defined by any preceding agent"
                        )
                defined.add(agent.output_label)
        return self

    @model_validator(mode="after")
    def _no_circular_depends_on(self) -> "WorkflowTemplate":
        """Detect circular depends_on using DFS coloring across the full DAG."""
        # Build adjacency: output_label → set of output_labels it depends on
        graph: dict[str, set[str]] = {}
        for cycle in self.cycles:
            for agent in cycle.agents:
                graph[agent.output_label] = set(agent.depends_on)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {label: WHITE for label in graph}

        def _dfs(node: str) -> bool:
            color[node] = GRAY
            for dep in graph.get(node, set()):
                if dep not in color:
                    continue
                if color[dep] == GRAY:
                    return True  # back-edge → cycle
                if color[dep] == WHITE and _dfs(dep):
                    return True
            color[node] = BLACK
            return False

        for label in graph:
            if color[label] == WHITE:
                if _dfs(label):
                    raise ValueError(
                        "Circular depends_on reference detected in cycles — "
                        "the agent dependency graph must be a DAG"
                    )
        return self


__all__: tuple[str, ...] = (
    "AgentAssignment",
    "CycleSpec",
    "InputParamSpec",
    "OutputSpec",
    "ProvenanceMode",
    "PROVENANCE_DEFAULTS",
    "QualityGateSpec",
    "RenderingMode",
    "ShareableLinkSpec",
    "WorkflowTemplate",
)
