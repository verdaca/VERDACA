"""No parallel ``MacTelemetryEvent`` negative tests — mac/test-strategy.md v0.3 §11.3.

Covers MAC-T-NEG-TELEMETRY-01 and MAC-T-NEG-TELEMETRY-02. There MUST
be exactly one :class:`TelemetryEvent` definition (the MAC-local mirror
of the Memory TelemetryEvent envelope per arch §11.3) in
``praxis/kernel/mac/``. No shadow definitions in tests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_MAC_SRC = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "praxis"
    / "kernel"
    / "mac"
)
_MAC_TESTS = Path(__file__).resolve().parents[2]


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_neg_telemetry_01_exactly_one_telemetry_event_definition() -> None:
    """MAC-T-NEG-TELEMETRY-01 — exactly one ``class TelemetryEvent`` in
    ``praxis/kernel/mac/``. Step 4 lands the MAC-local mirror at
    ``observability/emitter.py``; any other definition is a shadow.
    """
    pattern = re.compile(r"^class\s+TelemetryEvent\b")
    hits: list[Path] = []
    for py_file in _MAC_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            if pattern.search(line.strip()):
                hits.append(py_file)
                break

    assert len(hits) == 1, (
        f"Expected exactly one TelemetryEvent class definition in "
        f"praxis/kernel/mac/; found {len(hits)}: {hits}"
    )


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_neg_telemetry_02_no_shadow_event_class_in_tests() -> None:
    """MAC-T-NEG-TELEMETRY-02 — no ``class TelemetryEvent`` or
    ``class MacTelemetryEvent`` definition anywhere in ``tests/mac/``.

    Tests must consume the production class via import, not shadow
    it. Shadow classes mask production bugs by definition.
    """
    pattern = re.compile(r"^class\s+(TelemetryEvent|MacTelemetryEvent)\b")
    hits: list[tuple[Path, int]] = []
    for py_file in _MAC_TESTS.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line.strip()):
                hits.append((py_file, lineno))

    assert not hits, f"Shadow TelemetryEvent definitions in tests: {hits}"
