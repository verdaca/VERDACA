"""tests/runtime/test_models.py — GREEN commit.

Tests for runtime/models.py (AgentDefinition, AgentRole, AgentModule).
xfail markers removed; implementation in src/praxis/kernel/runtime/models.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from praxis.kernel.runtime.models import AgentDefinition, AgentModule, AgentRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_KWARGS = dict(
    name="bmad-agent-architect",
    display_name="Winston",
    title="Architect",
    icon="🏗️",
    capabilities="distributed systems, cloud infrastructure",
    role="System Architect",
    identity="Senior architect.",
    communication_style="Calm and pragmatic.",
    principles="Boring technology for stability.",
    module=AgentModule.BMM,
    path=Path("_bmad/bmm/3-solutioning/bmad-agent-architect"),
    canonical_id="",
)


# ---------------------------------------------------------------------------
# AgentRole
# ---------------------------------------------------------------------------


def test_agent_role_importable_from_models() -> None:
    assert AgentRole.PRODUCER.value == "producer"
    assert AgentRole.REVIEWER.value == "reviewer"


def test_agent_role_still_importable_from_proxies() -> None:
    """Backward-compat: existing Checkpoint 1 code imports from proxies."""
    from praxis.kernel.runtime.proxies import AgentRole as ProxiesRole

    assert ProxiesRole is AgentRole, (
        "AgentRole from proxies must be the exact same object as from models "
        "(re-export, not re-declaration)"
    )


def test_agent_role_from_proxies_base_still_works() -> None:
    """proxies._base backward compat re-export."""
    from praxis.kernel.runtime.proxies._base import AgentRole as BaseRole

    assert BaseRole is AgentRole


# ---------------------------------------------------------------------------
# AgentModule
# ---------------------------------------------------------------------------


def test_agent_module_enum_values() -> None:
    assert AgentModule.BMM.value == "bmm"
    assert AgentModule.CIS.value == "cis"
    assert AgentModule.TEA.value == "tea"


# ---------------------------------------------------------------------------
# AgentDefinition
# ---------------------------------------------------------------------------


def test_agent_definition_frozen() -> None:
    defn = AgentDefinition(**_BASE_KWARGS)  # type: ignore[arg-type]
    with pytest.raises((ValidationError, TypeError)):
        defn.name = "tampered"  # type: ignore[misc]


def test_agent_definition_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        AgentDefinition(**{**_BASE_KWARGS, "unknown_field": "should_fail"})  # type: ignore[arg-type]


def test_capabilities_normalized_to_lowercase_tuple() -> None:
    defn = AgentDefinition(
        **{
            **_BASE_KWARGS,
            "capabilities": "Story Execution, Test-Driven Development, Code Implementation",
        },  # type: ignore[arg-type]
    )
    assert isinstance(defn.capabilities, tuple)
    assert all(t == t.lower() for t in defn.capabilities)
    assert "story execution" in defn.capabilities
    assert "test-driven development" in defn.capabilities


def test_capabilities_accepts_list_input() -> None:
    defn = AgentDefinition(**{**_BASE_KWARGS, "capabilities": ["story execution", "TDD"]})  # type: ignore[arg-type]
    assert isinstance(defn.capabilities, tuple)
    assert "story execution" in defn.capabilities


def test_capabilities_accepts_tuple_input() -> None:
    defn = AgentDefinition(**{**_BASE_KWARGS, "capabilities": ("story execution",)})  # type: ignore[arg-type]
    assert isinstance(defn.capabilities, tuple)


def test_capabilities_empty_string_raises() -> None:
    with pytest.raises(ValidationError):
        AgentDefinition(**{**_BASE_KWARGS, "capabilities": ""})  # type: ignore[arg-type]


def test_capabilities_empty_list_raises() -> None:
    with pytest.raises(ValidationError):
        AgentDefinition(**{**_BASE_KWARGS, "capabilities": []})  # type: ignore[arg-type]


def test_name_invalid_characters_rejected() -> None:
    with pytest.raises(ValidationError, match="name"):
        AgentDefinition(**{**_BASE_KWARGS, "name": "invalid name with spaces!"})  # type: ignore[arg-type]


def test_path_must_be_relative() -> None:
    with pytest.raises(ValidationError, match="path"):
        AgentDefinition(**{**_BASE_KWARGS, "path": Path("/absolute/path/not/allowed")})  # type: ignore[arg-type]


def test_module_invalid_value_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentDefinition(**{**_BASE_KWARGS, "module": "invalid_module"})  # type: ignore[arg-type]


def test_all_public_exports_present() -> None:
    import praxis.kernel.runtime.models as m

    assert hasattr(m, "AgentDefinition")
    assert hasattr(m, "AgentRole")
    assert hasattr(m, "AgentModule")
    assert "AgentDefinition" in m.__all__
    assert "AgentRole" in m.__all__
    assert "AgentModule" in m.__all__


def test_agent_definition_hashable_via_frozen() -> None:
    """Frozen Pydantic models are hashable — agents can be used in sets."""
    defn1 = AgentDefinition(**_BASE_KWARGS)  # type: ignore[arg-type]
    defn2 = AgentDefinition(**_BASE_KWARGS)  # type: ignore[arg-type]
    s = {defn1, defn2}
    assert len(s) == 1  # same values → same hash
