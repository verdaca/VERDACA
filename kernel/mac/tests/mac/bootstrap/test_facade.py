"""Bootstrap loader facade tests — mac/test-strategy.md v0.3 §8.5.

Covers MAC-T-BOOT-FACADE-01..02. Verifies the loader's public surface
shape is exactly what arch §8.1 ratified, with no surprise kwargs or
methods that would imply Option X re-emergence.
"""

from __future__ import annotations

import inspect

import pytest

from praxis.kernel.mac.bootstrap import (
    BootstrapLoader,
    GoldStandardRecord,
)


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.mac_bootstrap_loader
def test_mac_t_boot_facade_01_loader_has_load_gold_standards() -> None:
    """MAC-T-BOOT-FACADE-01 — ``BootstrapLoader.load_gold_standards`` exists
    and has the canonical (tenant_id, tenant_hash, path_b_emitter) signature.
    """
    sig = inspect.signature(BootstrapLoader.load_gold_standards)
    params = set(sig.parameters.keys())
    assert "self" in params
    assert "tenant_id" in params
    assert "tenant_hash" in params
    assert "path_b_emitter" in params

    # The method MUST NOT have a `metadata` or `bootstrap` kwarg
    # (those would imply Option X — passing arbitrary metadata
    # through the loader instead of via the sidecar).
    forbidden = {"metadata", "bootstrap_metadata", "bootstrap"}
    overlap = forbidden & params
    assert not overlap, (
        f"BootstrapLoader.load_gold_standards has Option-X kwargs: {overlap}"
    )


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.mac_bootstrap_loader
def test_mac_t_boot_facade_02_loader_has_no_load_into_memory_schema_method() -> None:
    """MAC-T-BOOT-FACADE-02 — the loader does NOT expose any method
    that would inject directly into Memory schema.

    Per arch §13.2 Rejected Alternatives: Option X is rejected. The
    loader's only public method is ``load_gold_standards``; no
    ``load_into_memory_schema``, ``inject_into_memory_migrations``,
    or similar.
    """
    public_methods = {
        name
        for name, _ in inspect.getmembers(BootstrapLoader)
        if not name.startswith("_")
        and callable(getattr(BootstrapLoader, name))
    }

    forbidden_method_names = {
        "load_into_memory_schema",
        "inject_into_memory_migrations",
        "patch_experience_entries",
        "add_metadata_column",
    }
    overlap = forbidden_method_names & public_methods
    assert not overlap, (
        f"BootstrapLoader exposes rejected Option-X methods: {overlap}"
    )

    # Required public method present.
    assert "load_gold_standards" in public_methods
    # Helper property present.
    assert "corpus" in {
        name
        for name, _ in inspect.getmembers(
            BootstrapLoader, predicate=lambda v: isinstance(v, property)
        )
    }
