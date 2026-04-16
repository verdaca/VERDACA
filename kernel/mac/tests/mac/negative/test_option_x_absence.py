"""Option X absence negative tests — mac/test-strategy.md v0.3 §11.2.

Three-layer enforcement of arch §13.2 Option X rejection. Option X
was the rejected alternative of adding a ``metadata`` JSONB column to
``experience_entries``; arch §8.1 ratifies Option Y (sidecar table)
instead. These tests verify Option X never silently reappears.

Anchors:
  - mac/architecture.md §13.2 Rejected Alternatives (Option X)
  - mac/architecture.md §8.1 Option Y Ratification
  - mac/test-strategy.md v0.3 §11.2 MAC-T-NEG-OPTION-X-01..03
"""

from __future__ import annotations

import inspect
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


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.mac_bootstrap_loader
def test_mac_t_neg_option_x_01_layer_1_grep_no_memory_schema_injection() -> None:
    """MAC-T-NEG-OPTION-X-01 — Layer 1: grep MAC source for Option X patterns.

    No file in ``praxis/kernel/mac/`` references any pattern that
    would add a column to ``experience_entries`` or modify Stage 3
    Memory schema. Forbidden patterns:

      - ``experience_entries.*ADD COLUMN``
      - ``ALTER TABLE experience_entries``
      - ``store_task_outcome(...metadata=...)``  (kwarg injection)
      - ``memory.migrations`` (importing or modifying Memory migrations)
    """
    forbidden_patterns = [
        re.compile(r"experience_entries.*ADD\s+COLUMN", re.IGNORECASE),
        re.compile(r"ALTER\s+TABLE\s+experience_entries", re.IGNORECASE),
        re.compile(r"store_task_outcome\(.*metadata\s*=", re.IGNORECASE),
        re.compile(
            r"from\s+praxis\.kernel\.memory\.migrations", re.IGNORECASE
        ),
        re.compile(r"import\s+praxis\.kernel\.memory\.migrations", re.IGNORECASE),
    ]

    violations: list[tuple[Path, int, str]] = []
    for py_file in _MAC_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat in forbidden_patterns:
                if pat.search(line):
                    violations.append((py_file, lineno, line.strip()))

    assert not violations, (
        f"Option X (rejected per arch §13.2) reappeared in MAC source: "
        f"{violations}"
    )


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.mac_bootstrap_loader
def test_mac_t_neg_option_x_02_layer_2_fake_memory_facade_has_no_bootstrap_fields() -> None:
    """MAC-T-NEG-OPTION-X-02 — Layer 2: schema introspection on the
    FakeMemoryFacade.

    The MAC-local fake of the Memory facade must NOT carry any
    bootstrap-related fields or kwargs. Any such addition would
    indicate Option X (extending Memory's API surface) silently
    appearing. Real Memory introspection (Stage 7) extends this to
    the production Memory model.
    """
    from praxis.kernel.mac.testing.fakes.fake_memory_facade import (
        FakeMemoryFacade,
    )

    # store_task_outcome MUST NOT have bootstrap-related kwargs.
    sig = inspect.signature(FakeMemoryFacade.store_task_outcome)
    forbidden_kwargs = {
        "metadata",
        "bootstrap",
        "bootstrap_metadata",
        "bootstrap_source",
        "is_bootstrap_entry",
    }
    actual_kwargs = set(sig.parameters.keys())
    overlap = forbidden_kwargs & actual_kwargs
    assert not overlap, (
        f"FakeMemoryFacade.store_task_outcome carries Option-X kwargs: {overlap}. "
        f"Per arch §13.2 + §8.1, Stage 3 Memory schema is FROZEN; bootstrap "
        f"metadata lives in the MAC-owned sidecar table, not in Memory."
    )

    # Same for retrieve_similar_tasks.
    sig_r = inspect.signature(FakeMemoryFacade.retrieve_similar_tasks)
    overlap_r = forbidden_kwargs & set(sig_r.parameters.keys())
    assert not overlap_r, (
        f"FakeMemoryFacade.retrieve_similar_tasks carries Option-X kwargs: {overlap_r}"
    )


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.mac_bootstrap_loader
def test_mac_t_neg_option_x_03_layer_3_mac_memory_adapter_signature_check() -> None:
    """MAC-T-NEG-OPTION-X-03 — Layer 3: ``MacMemoryAdapter`` does not
    extend Memory's surface.

    The named MAC contract methods (``publish_outcome``,
    ``reuse_successful``) are MAC-side wrappers — they call into the
    Memory facade with the EXISTING parameter set. They must NOT
    introduce new kwargs that would imply Memory schema extension.
    """
    from praxis.kernel.mac.integrations.memory import MacMemoryAdapter

    publish_sig = inspect.signature(MacMemoryAdapter.publish_outcome)
    publish_params = set(publish_sig.parameters.keys())
    # Allowed kwargs are exactly: self, tenant_id, task_signature, outcome
    allowed_publish = {"self", "tenant_id", "task_signature", "outcome"}
    extra = publish_params - allowed_publish
    assert not extra, (
        f"MacMemoryAdapter.publish_outcome introduces Option-X kwargs: {extra}. "
        f"Allowed: {allowed_publish}"
    )

    reuse_sig = inspect.signature(MacMemoryAdapter.reuse_successful)
    reuse_params = set(reuse_sig.parameters.keys())
    allowed_reuse = {
        "self",
        "tenant_id",
        "signature",
        "top_k",
        "min_similarity",
    }
    extra_reuse = reuse_params - allowed_reuse
    assert not extra_reuse, (
        f"MacMemoryAdapter.reuse_successful introduces Option-X kwargs: {extra_reuse}. "
        f"Allowed: {allowed_reuse}"
    )
