"""MAC telemetry label registry — arch §11.1 SQ-2 binding.

Defines every label key MAC events may carry + the bounded value set
for each. Adding a key requires editing this file — the grep lock at
:mod:`praxis.kernel.mac.observability.emitter` enforces hard-fail on
any unknown label key or value.

**SQ-2 hard reject (non-waivable):** unknown label keys/values raise
:class:`LabelRegistryError` (subclass of ``ValueError``) — no warn, no
fallback, no allowlist exception.

Binding anchors:
  - mac/architecture.md §11.1 Telemetry Label Cardinality Registry
  - mac/architecture.md §12.2 item 1 (no_waiver SQ-2 discipline)
  - mac/test-strategy.md v0.3 §9.1 LABEL-REG-01..04
"""

from __future__ import annotations

from typing import Mapping


ALLOWED_MAC_LABEL_KEYS: frozenset[str] = frozenset({
    "cycle_id",
    "cycle_phase",
    "gate_id",
    "domain_class",
    "outcome",
    "backtrack_count",
    "bootstrap_hit",
    "forge_degraded",
    "tenant_hash",
    "praxis_version",
    "reviewer_count",
})
"""Arch §11.1 frozen key set. Adding a key requires architectural
revision; the emitter hard-rejects anything else."""


ALLOWED_LABEL_VALUES: Mapping[str, frozenset[str]] = {
    "cycle_phase": frozenset(
        {"interpret", "decompose", "produce", "review", "gate_eval", "publish"}
    ),
    "gate_id": frozenset({f"R{i}" for i in range(1, 13)}),  # R1..R12 only
    "domain_class": frozenset(
        {"contested", "consensus", "deterministic", "binary", "diagnostic"}
    ),
    "outcome": frozenset({"pass", "fail", "suspended"}),
    "backtrack_count": frozenset({"0", "1"}),
    "bootstrap_hit": frozenset({"true", "false"}),
    "forge_degraded": frozenset({"true", "false"}),
    "reviewer_count": frozenset({"1", "2", "3"}),
}
"""Per-key bounded value sets. Keys not in this map are unbounded."""


UNBOUNDED_KEYS: frozenset[str] = frozenset(
    {"cycle_id", "tenant_hash", "praxis_version"}
)
"""Keys with unbounded value sets (high-cardinality, but allowed).
Bounded at deployment-level retention, not at the registry."""


__all__ = (
    "ALLOWED_LABEL_VALUES",
    "ALLOWED_MAC_LABEL_KEYS",
    "UNBOUNDED_KEYS",
)
