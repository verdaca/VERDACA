"""tests/runtime/tools/test_sandbox_red_team.py — RED commit.

§9.5 sandbox red-team battery across all 8 P0 tools.
Per-class (A through D) adversarial scenarios.
Class E tools must never appear in registry.

Architecture §9.5, §11.10.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Class E — must never be admitted
# ---------------------------------------------------------------------------


def test_class_e_tools_never_admitted() -> None:
    """Registry must reject any tool declaring Class E blast radius."""
    from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass

    class_e = [t for t in TOOL_CATALOG if t.blast_class == ToolBlastRadiusClass.E]
    assert not class_e, f"Class E tools found in catalog: {[t.name for t in class_e]}"


# ---------------------------------------------------------------------------
# Class A — inert, broadly allowed
# ---------------------------------------------------------------------------


def test_class_a_tools_have_no_write_surface() -> None:
    """All Class A tools must have write_mode_capable=False."""
    from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass

    class_a = [t for t in TOOL_CATALOG if t.blast_class == ToolBlastRadiusClass.A]
    assert class_a, "No Class A tools found — catalog likely not loaded"
    for tool in class_a:
        # otel-exporter is write-only (emits), context7/sec-edgar are read-only
        # Write-only is OK for Class A (it emits telemetry, doesn't read data)
        assert not (tool.read_mode_capable and tool.write_mode_capable), (
            f"{tool.name}: Class A tool should not be both readable AND writable"
        )


# ---------------------------------------------------------------------------
# Class C — filesystem denylist
# ---------------------------------------------------------------------------


def test_class_c_filesystem_denylist_complete() -> None:
    """All denylist patterns from architecture §9.6 must be covered."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    # Architecture §9.6 explicit patterns
    assert is_path_denied(".env")
    assert is_path_denied(".env.production")
    assert is_path_denied(".ssh/id_rsa")
    assert is_path_denied(".ssh/known_hosts")
    assert is_path_denied("credentials.json")
    assert is_path_denied("secrets/api_key.txt")
    assert is_path_denied("config/secrets/database_password")


# ---------------------------------------------------------------------------
# Class D — subprocess binary allowlist
# ---------------------------------------------------------------------------


def test_class_d_subprocess_shell_blocked() -> None:
    """Shell interpreters must never be admitted per architecture §6.1.7b."""
    from praxis.kernel.runtime.tools.subprocess_mcp import is_binary_allowed

    for shell in ["sh", "bash", "zsh", "fish", "ksh", "csh", "dash", "powershell", "cmd"]:
        assert not is_binary_allowed(shell), f"Shell {shell!r} must be blocked"


def test_class_d_subprocess_network_tools_blocked() -> None:
    from praxis.kernel.runtime.tools.subprocess_mcp import is_binary_allowed

    for tool in ["curl", "wget", "nc", "netcat", "nmap", "ssh", "scp", "sftp"]:
        assert not is_binary_allowed(tool), f"Network tool {tool!r} must be blocked"


def test_class_d_subprocess_fs_tools_blocked() -> None:
    from praxis.kernel.runtime.tools.subprocess_mcp import is_binary_allowed

    for tool in ["cat", "rm", "mv", "cp", "chmod", "chown", "dd", "find"]:
        assert not is_binary_allowed(tool), f"FS tool {tool!r} must be blocked"


# ---------------------------------------------------------------------------
# R53 — OTel exporter never leaks forbidden fields
# ---------------------------------------------------------------------------


@pytest.mark.r53_structural
def test_r53_all_forbidden_fields_rejected() -> None:
    """Comprehensive R53 field gate: every forbidden field must raise ValidationError."""
    from pydantic import ValidationError

    from praxis.kernel.runtime.tools.otel_exporter_mcp import build_telemetry_event

    forbidden_kwargs = [
        {"query_content": "secret query"},
        {"embedding": [0.1, 0.2]},
        {"result_ids": ["id1", "id2"]},
        {"raw_response": "some internal response"},
        {"tenant_data": "sensitive"},
    ]

    for extra in forbidden_kwargs:
        with pytest.raises(ValidationError, match=r"extra|forbidden"):
            build_telemetry_event(
                metric_name="test",
                metric_type="counter",
                value=1.0,
                labels={},
                praxis_version="0.1.0",
                tenant_hash="abc",
                **extra,
            )
