"""Bootstrap idempotency tests — mac/test-strategy.md v0.3 §8.4 (S-Q1 bake-in).

Covers MAC-T-BOOT-IDEMPOTENT-01..04. Per arch §8.1 + S-Q1 ratified
semantics: ``BootstrapLoader.load_gold_standards()`` on second call
returns 0, logs ``mac.bootstrap.already_loaded`` telemetry, does NOT
raise.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.bootstrap import BootstrapLoader
from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.integrations.runtime import (
    FakeOutbox,
    MacPathBEmitter,
)
from praxis.kernel.mac.testing.fakes.fake_memory_facade import (
    FakeMemoryFacade,
)
from praxis.kernel.mac.testing.fakes.fake_metadata_store import (
    InMemoryMacBootstrapMetadataStore,
)


def _build_loader() -> tuple[
    BootstrapLoader, FakeMemoryFacade, InMemoryMacBootstrapMetadataStore
]:
    memory = FakeMemoryFacade()
    sidecar = InMemoryMacBootstrapMetadataStore()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    loader = BootstrapLoader(memory_adapter=adapter, metadata_store=sidecar)
    return loader, memory, sidecar


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_idempotent_01_second_call_returns_zero_and_logs() -> None:
    """MAC-T-BOOT-IDEMPOTENT-01 — S-Q1 ratified: second call returns 0
    and logs ``mac.bootstrap.already_loaded``.
    """
    loader, memory, sidecar = _build_loader()
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)

    first = await loader.load_gold_standards(
        tenant_id="t1", path_b_emitter=emitter
    )
    second = await loader.load_gold_standards(
        tenant_id="t1", path_b_emitter=emitter
    )

    assert first == 10
    assert second == 0

    # Telemetry: the second call emits mac.bootstrap.already_loaded.
    event_types = [key.split(":")[2] for key in outbox.dedup_keys]
    assert "mac.bootstrap.already_loaded" in event_types


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_idempotent_02_no_duplicate_rows() -> None:
    """MAC-T-BOOT-IDEMPOTENT-02 — second call does NOT insert duplicate
    rows into Memory facade or sidecar.
    """
    loader, memory, sidecar = _build_loader()

    await loader.load_gold_standards(tenant_id="t2")
    await loader.load_gold_standards(tenant_id="t2")
    await loader.load_gold_standards(tenant_id="t2")  # third call also no-op

    # Memory facade still has exactly 10 stored outcomes (from the first call).
    assert len(memory.stored_outcomes) == 10
    # Sidecar still has exactly 10 rows for tenant t2.
    assert sidecar.count_for_tenant("t2") == 10


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_idempotent_03_no_raise_semantics() -> None:
    """MAC-T-BOOT-IDEMPOTENT-03 — second call does NOT raise.

    Per S-Q1: idempotency is a return-value contract, not an
    exception contract. Callers can safely re-invoke without
    try/except.
    """
    loader, memory, sidecar = _build_loader()

    await loader.load_gold_standards(tenant_id="t3")
    # No exception on second call.
    result = await loader.load_gold_standards(tenant_id="t3")
    assert result == 0
    # No exception on third call.
    result2 = await loader.load_gold_standards(tenant_id="t3")
    assert result2 == 0


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_idempotent_04_per_tenant_isolation() -> None:
    """MAC-T-BOOT-IDEMPOTENT-04 — idempotency is per-tenant.

    Loading for tenant A does not block loading for tenant B. Each
    tenant gets its own ``is_loaded`` flag in the sidecar.
    """
    loader, memory, sidecar = _build_loader()

    a = await loader.load_gold_standards(tenant_id="alpha")
    b = await loader.load_gold_standards(tenant_id="beta")

    assert a == 10
    assert b == 10
    assert sidecar.is_loaded("alpha")
    assert sidecar.is_loaded("beta")
    assert sidecar.count_for_tenant("alpha") == 10
    assert sidecar.count_for_tenant("beta") == 10
    # Memory has 20 stored outcomes total.
    assert len(memory.stored_outcomes) == 20

    # Re-loading alpha is a no-op; beta remains loaded.
    a_second = await loader.load_gold_standards(tenant_id="alpha")
    assert a_second == 0
