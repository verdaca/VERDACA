"""Shared pytest fixtures for Studio tests.

All fixtures are session-scoped where safe (templates_dir, deep/quick templates)
or function-scoped for mutable fakes (cost tracker, fake MAC).

Binding: studio/test-strategy.md §14 Fixture Architecture.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from praxis.kernel.studio.schema import WorkflowTemplate, RenderingMode, ProvenanceMode
from praxis.kernel.studio.models import ReasoningTrace
from praxis.kernel.studio.renderer import TemplateRenderer

from tests.studio.fixtures.fake_mac import FakeMAC, make_minimal_trace, make_rich_trace
from tests.studio.fixtures.fake_cost_tracker import FakeCostTracker
from tests.studio.fixtures.fake_llm_judge import FakeLLMJudge


# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------

_STUDIO_ROOT = Path(__file__).parent.parent.parent  # studio/
_TEMPLATES_DIR = _STUDIO_ROOT / "templates"
_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_YAML_DIR = _STUDIO_ROOT  # strategic_session*.yaml live here


# ---------------------------------------------------------------------------
# Template fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def templates_dir() -> Path:
    return _TEMPLATES_DIR


@pytest.fixture(scope="session")
def renderer(templates_dir: Path) -> TemplateRenderer:
    return TemplateRenderer(templates_dir)


@pytest.fixture(scope="session")
def deep_template() -> WorkflowTemplate:
    yaml_path = _YAML_DIR / "strategic_session.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return WorkflowTemplate.model_validate(raw)


@pytest.fixture(scope="session")
def quick_template() -> WorkflowTemplate:
    yaml_path = _YAML_DIR / "strategic_session_quick.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return WorkflowTemplate.model_validate(raw)


# ---------------------------------------------------------------------------
# Trace fixtures (test-strategy §14.3)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def minimal_trace() -> ReasoningTrace:
    return make_minimal_trace()


@pytest.fixture(scope="session")
def rich_trace() -> ReasoningTrace:
    return make_rich_trace()


@pytest.fixture(scope="session")
def minimal_trace_flexible() -> ReasoningTrace:
    return make_minimal_trace(
        rendering_mode=RenderingMode.POSITION_TO_HOLD,
        provenance_mode=ProvenanceMode.FLEXIBLE,
    )


@pytest.fixture(scope="session")
def minimal_trace_inspectable() -> ReasoningTrace:
    return make_minimal_trace(
        rendering_mode=RenderingMode.DECISION_FRAMEWORK,
        provenance_mode=ProvenanceMode.INSPECTABLE,
    )


@pytest.fixture(scope="session")
def minimal_trace_invisible() -> ReasoningTrace:
    return make_minimal_trace(
        rendering_mode=RenderingMode.FIRM_VOICE,
        provenance_mode=ProvenanceMode.INVISIBLE,
    )


# ---------------------------------------------------------------------------
# Fakes (function-scoped — mutable)
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_mac() -> FakeMAC:
    return FakeMAC()


@pytest.fixture
def fake_cost_tracker() -> FakeCostTracker:
    return FakeCostTracker()


@pytest.fixture
def fake_llm_judge() -> FakeLLMJudge:
    return FakeLLMJudge()


# ---------------------------------------------------------------------------
# Fixture file paths
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def invalid_templates_dir() -> Path:
    return _FIXTURES_DIR / "invalid_templates"


@pytest.fixture(scope="session")
def register_corpus_dir() -> Path:
    return _FIXTURES_DIR / "register_corpus"


@pytest.fixture(scope="session")
def benchmark_scores_dir() -> Path:
    return _FIXTURES_DIR / "benchmark_scores"
