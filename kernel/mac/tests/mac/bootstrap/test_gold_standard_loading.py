"""Gold standard loading tests — mac/test-strategy.md v0.3 §8.2.

Covers MAC-T-BOOT-LOAD-01..03.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.bootstrap import (
    BootstrapLoader,
    GoldStandardRecord,
    default_gold_standard_corpus,
)
from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.testing.fakes.fake_memory_facade import (
    FakeMemoryFacade,
)
from praxis.kernel.mac.testing.fakes.fake_metadata_store import (
    InMemoryMacBootstrapMetadataStore,
)


@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
def test_mac_t_boot_load_01_corpus_size_is_ten() -> None:
    """MAC-T-BOOT-LOAD-01 — gold-standard corpus size is exactly 10
    per benchmark-questions.md §8 OQ-6 (10 questions, 1 record each).
    """
    corpus = default_gold_standard_corpus()
    assert len(corpus) == 10
    q_ids = {r.benchmark_question_id for r in corpus}
    assert q_ids == {f"Q{n}" for n in range(1, 11)}
    # Each record has the canonical 4.2 anchor score.
    assert all(r.calibration_anchor_score == 4.2 for r in corpus)
    assert all(r.quality_score == 4.2 for r in corpus)


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_load_02_records_inserted_into_memory_and_sidecar() -> None:
    """MAC-T-BOOT-LOAD-02 — first call inserts all 10 records via
    Memory facade AND the sidecar at the same logical write boundary.
    """
    memory = FakeMemoryFacade()
    sidecar = InMemoryMacBootstrapMetadataStore()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    loader = BootstrapLoader(memory_adapter=adapter, metadata_store=sidecar)

    inserted = await loader.load_gold_standards(tenant_id="tenant-a")

    assert inserted == 10
    # Memory facade received 10 store_task_outcome calls.
    assert len(memory.stored_outcomes) == 10
    # Sidecar table has 10 rows for tenant-a.
    assert sidecar.count_for_tenant("tenant-a") == 10
    # Sidecar marks tenant as loaded.
    assert sidecar.is_loaded("tenant-a")


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
async def test_mac_t_boot_load_03_sidecar_rows_have_correct_metadata() -> None:
    """MAC-T-BOOT-LOAD-03 — each sidecar row carries the correct
    benchmark_question_id, source, and calibration_anchor_score.
    """
    memory = FakeMemoryFacade()
    sidecar = InMemoryMacBootstrapMetadataStore()
    adapter = MacMemoryAdapter(memory=memory, sidecar=sidecar)
    loader = BootstrapLoader(memory_adapter=adapter, metadata_store=sidecar)

    await loader.load_gold_standards(tenant_id="tenant-b")

    # Every sidecar row references a benchmark question and the
    # canonical bootstrap source string.
    q_ids = {row.benchmark_question_id for row in sidecar.rows}
    assert q_ids == {f"Q{n}" for n in range(1, 11)}

    for row in sidecar.rows:
        assert row.tenant_hash == "tenant-b"
        assert row.source == "benchmark_gold_standard"
        assert row.calibration_anchor_score == 4.2
        assert row.bootstrap is True
        # Each entry_id matches a Memory facade call.
        memory_entry_ids = {
            outcome["entry_id"] for outcome in memory.stored_outcomes
        }
        assert row.experience_entry_id in memory_entry_ids
