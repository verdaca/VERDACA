"""No-13th-gate negative tests — mac/test-strategy.md v0.3 §11.1.

Covers MAC-T-NEG-GATE13-01 and MAC-T-NEG-GATE13-02. R13 Evidence
Sourcing is deferred per arch §3.5 / SQ-3; Stage 5 builds MUST NOT
contain R13 anywhere.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from praxis.kernel.mac.gates.registry import GATE_CLASSES


_GATES_DIR = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "praxis"
    / "kernel"
    / "mac"
    / "gates"
)


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_neg_gate13_01_no_gate_module_r13() -> None:
    """MAC-T-NEG-GATE13-01 — ``praxis/kernel/mac/gates/`` contains exactly
    12 gate modules: r1.py through r12.py. No r13.py.
    """
    # Match only rN.py filenames where N is 1..99 digits — this excludes
    # ``registry.py`` which also starts with ``r`` but is not a gate module.
    gate_pattern = re.compile(r"^r(\d+)\.py$")
    gate_files = sorted(
        f.name
        for f in _GATES_DIR.iterdir()
        if f.is_file() and gate_pattern.match(f.name)
    )
    expected = sorted(f"r{n}.py" for n in range(1, 13))
    assert gate_files == expected

    # Registry backs this up.
    assert len(GATE_CLASSES) == 12
    assert "R13" not in {cls.gate_id for cls in GATE_CLASSES}


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_neg_gate13_02_no_reference_to_r13_in_code() -> None:
    """MAC-T-NEG-GATE13-02 — grep for literal ``R13`` / ``r13`` in
    ``praxis/kernel/mac/`` returns 0 results outside historical
    references (arch §3.5 deferral narrative).

    Step 4 allows ``R13`` to appear in docstring text that REFERENCES
    the deferral (e.g., "R13 deferred per SQ-3") but not as a
    functional gate definition. The check is narrower: look for
    identifiers like ``R13Gate``, ``r13.py``, or ``"R13"`` in code
    literals (string values that would represent a gate ID).
    """
    mac_src = _GATES_DIR.parent  # praxis/kernel/mac/
    forbidden_patterns = [
        re.compile(r"class\s+R13Gate"),
        re.compile(r'"R13"\s*:'),  # dict key
        re.compile(r"gate_id\s*=\s*['\"]R13['\"]"),
    ]
    violations: list[tuple[Path, int, str]] = []
    for py_file in mac_src.rglob("*.py"):
        if "test_" in py_file.name:
            continue
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat in forbidden_patterns:
                if pat.search(line):
                    violations.append((py_file, lineno, line.strip()))

    assert not violations, f"Found R13 code references: {violations}"
