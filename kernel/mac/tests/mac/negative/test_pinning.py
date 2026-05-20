"""Dependency pinning negative tests — mac/test-strategy.md v0.3 §11.5.

Covers ``MAC-T-NEG-MCP-PIN-01`` (citation repaired at v0.3 §11.5.1 from
``arch §10.4`` drift → ``arch §10.3 Runtime Integration``).

Also includes a step-3 supplementary static grep test per step-3 go
signal constraint 5: ``grep -r "from praxis.kernel.runtime.spawner
import.*MemoryProxy" praxis/kernel/mac/`` MUST return 0 matches. This
static grep is not a MAC-T catalog test but is flagged under the Q3
coverage-floor disposition.

Anchors:
  - mac/architecture.md §10.3 Runtime Integration (MCP pin >=1.9.0)
  - mac/architecture.md §7.2 Binding to Runtime §4.1 Proxies (single-point)
  - runtime/pyproject.toml line 35 (inherited no_waiver convention)
"""

from __future__ import annotations

import re
from pathlib import Path


_MAC_SRC_ROOT = (
    Path(__file__).resolve().parents[3] / "src" / "praxis" / "kernel" / "mac"
)
_MAC_PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"


def test_mac_t_neg_mcp_pin_01_mcp_package_pinned_at_or_above_1_9() -> None:
    """MAC-T-NEG-MCP-PIN-01 — ``mcp`` package pinned ``>=1.9.0``.

    MAC inherits the Runtime MCP pin verbatim per arch §10.3 / SQ-1. The
    pin lives at the Runtime level in production (``runtime/pyproject.toml``);
    at step 3 the MAC module does NOT declare its own ``mcp`` dependency
    — we enforce the absence of a conflicting local pin.

    Test strategy: parse the MAC ``pyproject.toml`` and assert that
    (a) no ``mcp<1.9.0`` pin appears, and (b) if ``mcp`` is listed as
    a dependency at all, its version constraint allows ``>=1.9.0``.

    Markers: ``static``, ``critical``.
    """
    pyproject_text = _MAC_PYPROJECT.read_text(encoding="utf-8")

    # MAC must not downgrade the mcp pin — no lines of the form `mcp<X.Y`.
    down_pin = re.compile(r"['\"]?mcp['\"]?\s*<\s*1\.(?:[0-8]|9\.0)")
    match = down_pin.search(pyproject_text)
    assert match is None, (
        f"MAC pyproject.toml contains a downgrade pin for mcp: {match.group(0)!r}. "
        f"Per arch §10.3 SQ-1, MAC inherits Runtime's mcp>=1.9.0 — do NOT re-pin."
    )

    # If MAC ever declares its own mcp pin (it shouldn't at step 3), ensure it
    # is at or above 1.9.0.
    mac_pin = re.compile(
        r"['\"]?mcp['\"]?\s*>=\s*(\d+)\.(\d+)", re.IGNORECASE
    )
    for major_str, minor_str in mac_pin.findall(pyproject_text):
        major, minor = int(major_str), int(minor_str)
        assert (major, minor) >= (1, 9), (
            f"MAC pyproject.toml pins mcp below 1.9.0 (found {major}.{minor}). "
            f"Arch §10.3 SQ-1 inheritance requires >=1.9.0."
        )


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_no_direct_memory_proxy_imports_in_mac() -> None:
    """Step-3 supplementary grep test per step-3 go signal constraint 5.

    ``grep -r "from praxis.kernel.runtime.spawner import.*MemoryProxy"
    praxis/kernel/mac/`` MUST return 0 matches. Enforces the arch §7.2
    single-point proxy construction invariant — MAC must never directly
    import ``ProducerMemoryProxy`` or ``ReviewerMemoryProxy``; the only
    legal dispatch is via :class:`AgentRole` through
    :meth:`AgentSpawnerProtocol.spawn`.

    This test is a coverage-floor check rather than a MAC-T catalog
    entry because v0.3 test-strategy §11 does not enumerate it; the
    closest catalog test is ``MAC-T-ASYM-PROXY-04`` (§5.2.4) which
    lands at step 5. Per team-lead step-3 go signal constraint 5,
    the grep enforcement is added here so the invariant is live
    before step 5.
    """
    forbidden = re.compile(
        r"from\s+praxis\.kernel\.runtime\.spawner\s+import\s+.*MemoryProxy",
        re.IGNORECASE,
    )

    violations: list[tuple[Path, int, str]] = []
    for py_file in _MAC_SRC_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if forbidden.search(line):
                violations.append((py_file, lineno, line.strip()))

    assert not violations, (
        "MAC code directly imports ProducerMemoryProxy / ReviewerMemoryProxy "
        "from runtime.spawner — violates arch §7.2 single-point dispatch. "
        f"Offenders: {violations}"
    )
