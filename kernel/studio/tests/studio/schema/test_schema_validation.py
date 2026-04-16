"""Schema validation tests — studio/test-strategy.md §3.

20 tests: 7 positive + 10 negative + 3 property-based.
All Tier 1 (deterministic, no LLM, no real MAC).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from praxis.kernel.studio.schema import (
    InputParamSpec,
    ProvenanceMode,
    RenderingMode,
    ShareableLinkSpec,
    WorkflowTemplate,
    PROVENANCE_DEFAULTS,
)

_STUDIO_ROOT = Path(__file__).parent.parent.parent.parent  # tests/ → studio root
_YAML_DIR = _STUDIO_ROOT


def _load_yaml(name: str) -> dict:
    path = _YAML_DIR / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_invalid(name: str) -> dict:
    path = Path(__file__).parent.parent / "fixtures" / "invalid_templates" / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# §3.1 Positive validation (7 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_schema
@pytest.mark.critical
def test_schema_01_deep_yaml_validates():
    """STUDIO-T-SCHEMA-01: strategic_session.yaml validates successfully."""
    raw = _load_yaml("strategic_session.yaml")
    template = WorkflowTemplate.model_validate(raw)
    assert template.name == "strategic_session"


@pytest.mark.studio_schema
@pytest.mark.critical
def test_schema_02_quick_yaml_validates():
    """STUDIO-T-SCHEMA-02: strategic_session_quick.yaml validates successfully."""
    raw = _load_yaml("strategic_session_quick.yaml")
    template = WorkflowTemplate.model_validate(raw)
    assert template.name == "strategic_session_quick"


@pytest.mark.studio_schema
def test_schema_03_resolved_provenance_mode_inferred():
    """STUDIO-T-SCHEMA-03: resolved_provenance_mode() returns correct inferred default."""
    raw = _load_yaml("strategic_session.yaml")
    template = WorkflowTemplate.model_validate(raw)
    # position_to_hold → FLEXIBLE per PROVENANCE_DEFAULTS
    assert template.resolved_provenance_mode() == ProvenanceMode.FLEXIBLE


@pytest.mark.studio_schema
def test_schema_04_explicit_provenance_mode_overrides():
    """STUDIO-T-SCHEMA-04: explicit provenance_mode override takes precedence."""
    raw = _load_yaml("strategic_session.yaml")
    raw["provenance_mode"] = "invisible"
    template = WorkflowTemplate.model_validate(raw)
    assert template.resolved_provenance_mode() == ProvenanceMode.INVISIBLE


@pytest.mark.studio_schema
def test_schema_05_input_param_spec_all_types():
    """STUDIO-T-SCHEMA-05: InputParamSpec validates all 5 types."""
    for type_val, extra in [
        ("string", {}),
        ("int", {}),
        ("float", {}),
        ("bool", {}),
        ("enum", {"enum_values": ("a", "b")}),
    ]:
        spec = InputParamSpec(type=type_val, description="test", **extra)
        assert spec.type == type_val


@pytest.mark.studio_schema
def test_schema_06_output_format_restricted_to_markdown_html():
    """STUDIO-T-SCHEMA-06: OutputSpec.format restricted to markdown/html (ADR-08)."""
    raw = _load_yaml("strategic_session.yaml")
    template = WorkflowTemplate.model_validate(raw)
    for output in template.outputs:
        assert output.format in ("markdown", "html")


@pytest.mark.studio_schema
def test_schema_07_shareable_link_defaults():
    """STUDIO-T-SCHEMA-07: ShareableLinkSpec defaults match ADR-10."""
    spec = ShareableLinkSpec()
    assert spec.auth_gated is True
    assert spec.default_expiry_days == 30
    assert spec.owner_revocable is True


# ---------------------------------------------------------------------------
# §3.2 Negative validation (10 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_schema
@pytest.mark.critical
def test_schema_neg_01_missing_name_raises():
    """STUDIO-T-SCHEMA-NEG-01: Missing required field 'name' raises ValidationError."""
    raw = _load_invalid("missing_name.yaml")
    with pytest.raises(ValidationError) as exc_info:
        WorkflowTemplate.model_validate(raw)
    assert "name" in str(exc_info.value).lower()


@pytest.mark.studio_schema
def test_schema_neg_02_wrong_type_cost_budget():
    """STUDIO-T-SCHEMA-NEG-02: Wrong type for cost_budget_usd raises ValidationError."""
    raw = _load_yaml("strategic_session.yaml")
    raw["cost_budget_usd"] = "not_a_float"
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
def test_schema_neg_03_invalid_rendering_mode():
    """STUDIO-T-SCHEMA-NEG-03: Invalid rendering_mode raises ValidationError."""
    raw = _load_yaml("strategic_session.yaml")
    raw["rendering_mode"] = "invalid_mode"
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
@pytest.mark.critical
def test_schema_neg_04_invalid_gate_id():
    """STUDIO-T-SCHEMA-NEG-04: Invalid gate_id (not R1–R12) raises ValidationError."""
    raw = _load_invalid("invalid_gate_id.yaml")
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
def test_schema_neg_05_negative_cost_budget():
    """STUDIO-T-SCHEMA-NEG-05: cost_budget_usd <= 0 is rejected."""
    raw = _load_invalid("negative_budget.yaml")
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
def test_schema_neg_06_zero_timeout():
    """STUDIO-T-SCHEMA-NEG-06: timeout_seconds <= 0 is rejected."""
    raw = _load_invalid("zero_timeout.yaml")
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
@pytest.mark.critical
def test_schema_neg_07_circular_depends_on():
    """STUDIO-T-SCHEMA-NEG-07: Circular depends_on references raise ValidationError."""
    raw = _load_invalid("circular_depends_on.yaml")
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
def test_schema_neg_08_nonexistent_output_label_in_depends_on():
    """STUDIO-T-SCHEMA-NEG-08: depends_on referencing non-existent output_label is rejected."""
    raw = _load_yaml("strategic_session.yaml")
    # Inject a depends_on ref that doesn't exist
    raw["cycles"][0]["agents"][0]["depends_on"] = ["nonexistent_label_xyz"]
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


@pytest.mark.studio_schema
def test_schema_neg_09_enum_type_without_enum_values():
    """STUDIO-T-SCHEMA-NEG-09: enum type without enum_values raises ValidationError."""
    with pytest.raises(ValidationError):
        InputParamSpec(type="enum", description="test")


@pytest.mark.studio_schema
def test_schema_neg_10_duplicate_gate_id():
    """STUDIO-T-SCHEMA-NEG-10: Duplicate gate_id in quality_gates raises ValidationError."""
    raw = _load_invalid("duplicate_gate_id.yaml")
    with pytest.raises(ValidationError):
        WorkflowTemplate.model_validate(raw)


# ---------------------------------------------------------------------------
# §3.3 Property-based validation (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_schema
@given(
    rendering_mode=st.sampled_from(list(RenderingMode)),
    provenance_override=st.one_of(st.none(), st.sampled_from(list(ProvenanceMode))),
)
@settings(max_examples=30)
def test_schema_prop_01_resolved_provenance_mode_consistent(
    rendering_mode: RenderingMode,
    provenance_override: ProvenanceMode | None,
) -> None:
    """STUDIO-T-SCHEMA-PROP-01: resolved_provenance_mode() returns ProvenanceMode consistent with PROVENANCE_DEFAULTS."""
    raw = _load_yaml("strategic_session.yaml")
    raw["rendering_mode"] = rendering_mode.value
    raw["provenance_mode"] = provenance_override.value if provenance_override else None
    template = WorkflowTemplate.model_validate(raw)
    result = template.resolved_provenance_mode()
    assert isinstance(result, ProvenanceMode)
    if provenance_override is not None:
        assert result == provenance_override
    else:
        assert result == PROVENANCE_DEFAULTS[rendering_mode]


@pytest.mark.studio_schema
def test_schema_prop_02_round_trip_model_dump():
    """STUDIO-T-SCHEMA-PROP-02: WorkflowTemplate round-trips through model_dump() → model_validate()."""
    raw = _load_yaml("strategic_session.yaml")
    template = WorkflowTemplate.model_validate(raw)
    dumped = template.model_dump(mode="python")
    restored = WorkflowTemplate.model_validate(dumped)
    assert restored.name == template.name
    assert restored.version == template.version
    assert len(restored.cycles) == len(template.cycles)
    assert len(restored.quality_gates) == len(template.quality_gates)


@pytest.mark.studio_schema
def test_schema_prop_03_budget_pct_sums_to_100():
    """STUDIO-T-SCHEMA-PROP-03: budget_pct across all cycles sums to 100 for both templates."""
    for name in ("strategic_session.yaml", "strategic_session_quick.yaml"):
        raw = _load_yaml(name)
        template = WorkflowTemplate.model_validate(raw)
        total = sum(c.budget_pct for c in template.cycles)
        assert total == 100, f"{name}: budget_pct sum is {total}, expected 100"
