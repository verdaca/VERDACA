"""Domain guard mapping — arch §6.5 Req-E + SQ-5.

Per arch §6.5, the Quality Gate Engine applies task-type guards BEFORE
evaluating R5 and R11:

  - ``DomainClass.CONSENSUS`` → R5 suspended (no minority view to preserve)
  - ``DomainClass.DETERMINISTIC`` → R11 suspended (single-scenario domain)
  - ``DomainClass.BINARY`` → R11 suspended (same reason)
  - ``DomainClass.CONTESTED`` → no suspensions
  - ``DomainClass.DIAGNOSTIC`` → no suspensions

The mapping is keyed on the frozen :class:`DomainClass` enum (arch §3.4
SQ-5) — workflow templates (Stage 6) may override which guards activate
per value but CANNOT introduce new enum values.

Binding anchors:
  - mac/architecture.md §6.5 Domain Guard Conditions (Req-E + SQ-5)
  - mac/architecture.md §3.4 DomainClass frozen enum
  - mac/test-strategy.md v0.3 §11.4 DomainClass Singular Definition
"""

from __future__ import annotations

from praxis.kernel.mac.task import DomainClass


DEFAULT_GUARD_MAP: dict[DomainClass, frozenset[str]] = {
    DomainClass.CONTESTED: frozenset(),
    DomainClass.CONSENSUS: frozenset({"R5"}),
    DomainClass.DETERMINISTIC: frozenset({"R11"}),
    DomainClass.BINARY: frozenset({"R11"}),
    DomainClass.DIAGNOSTIC: frozenset(),
}
"""Arch §6.5 default guard mapping. Workflow templates may override at
Stage 6 but cannot extend the :class:`DomainClass` enum."""


def gates_suspended_for(
    domain_class: DomainClass,
    workflow_override: dict[DomainClass, frozenset[str]] | None = None,
) -> frozenset[str]:
    """Return the set of gate IDs suspended for ``domain_class``.

    ``workflow_override`` takes precedence over :data:`DEFAULT_GUARD_MAP`
    when provided for the given :class:`DomainClass`. Absent override
    falls back to the default.
    """
    if workflow_override and domain_class in workflow_override:
        return workflow_override[domain_class]
    return DEFAULT_GUARD_MAP[domain_class]


__all__ = ("DEFAULT_GUARD_MAP", "gates_suspended_for")
