"""Praxis Studio — workflow template layer over the MAC (Stage 6).

Studio is **configuration over the MAC**, not a new runtime. Public API:

- :mod:`schema` — ``WorkflowTemplate`` Pydantic model and supporting types
- :mod:`models` — domain objects for rendered output (ReasoningTrace, etc.)
- :mod:`invoker` — ``template_to_task_input()`` and ``StudioSession``
- :mod:`renderer` — ``TemplateRenderer`` (Jinja2 rendering + provenance strip)
- :mod:`register_check` — ``RegisterChecker`` (ADR-11 muted register enforcement)
- :mod:`harness` — ``ABHarness`` (A/B comparison harness)

Binding: studio/architecture.md v0.1 (RATIFIED 2026-04-16).
"""

from praxis.kernel.studio.schema import (
    AgentAssignment,
    CycleSpec,
    InputParamSpec,
    OutputSpec,
    ProvenanceMode,
    QualityGateSpec,
    RenderingMode,
    ShareableLinkSpec,
    WorkflowTemplate,
    PROVENANCE_DEFAULTS,
)
from praxis.kernel.studio.models import (
    DissentFrame,
    GateScores,
    ReasoningTrace,
    Recommendation,
    RenderedOutput,
    Scenario,
    ScopeLimits,
    SessionResult,
    TradeOff,
)
from praxis.kernel.studio.invoker import (
    TaskInput,
    StudioSession,
    template_to_task_input,
)
from praxis.kernel.studio.register_check import RegisterChecker, RegisterViolation
from praxis.kernel.studio.renderer import TemplateRenderer
from praxis.kernel.studio.harness import ABHarness, ComparisonReport, RunResult

__all__: tuple[str, ...] = (
    # schema
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
    # models
    "DissentFrame",
    "GateScores",
    "ReasoningTrace",
    "Recommendation",
    "RenderedOutput",
    "Scenario",
    "ScopeLimits",
    "SessionResult",
    "TradeOff",
    # invoker
    "StudioSession",
    "TaskInput",
    "template_to_task_input",
    # utilities
    "ABHarness",
    "ComparisonReport",
    "RegisterChecker",
    "RegisterViolation",
    "RunResult",
    "TemplateRenderer",
)
