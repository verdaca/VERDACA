"""Unit tests for PricingCatalog and snapshot loader."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from praxis.kernel.cost import (
    CacheRetention,
    Currency,
    ModelPricing,
    PricingGapError,
    ProviderName,
    UnknownModelError,
)
from praxis.kernel.cost.pricing.catalog import PricingCatalog
from praxis.kernel.cost.pricing.loader import load_snapshot_dir, load_snapshot_file


def _row(
    provider: ProviderName,
    model_id: str,
    effective_from: datetime,
    effective_until: datetime | None = None,
    retention: CacheRetention = CacheRetention.NONE,
    input_rate: str = "3.0",
) -> ModelPricing:
    return ModelPricing(
        provider=provider,
        model_id=model_id,
        cache_retention_key=retention,
        currency=Currency.USD,
        input_rate=Decimal(input_rate),
        output_rate=Decimal("15.0"),
        cache_read_rate=Decimal("0.3"),
        cache_write_rate=Decimal("3.75"),
        effective_from=effective_from,
        effective_until=effective_until,
    )


class TestCatalogLookup:
    def test_lookup_current_row(self) -> None:
        row = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        )
        cat = PricingCatalog([row])
        found = cat.lookup(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            CacheRetention.NONE,
            datetime(2026, 4, 12, tzinfo=UTC),
        )
        assert found is row

    def test_lookup_exact_from_boundary_inclusive(self) -> None:
        row = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        )
        cat = PricingCatalog([row])
        found = cat.lookup(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            CacheRetention.NONE,
            datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert found is row

    def test_lookup_unknown_model_raises(self) -> None:
        cat = PricingCatalog([])
        with pytest.raises(UnknownModelError):
            cat.lookup(
                ProviderName.ANTHROPIC,
                "claude-nonexistent",
                CacheRetention.NONE,
                datetime(2026, 4, 12, tzinfo=UTC),
            )

    def test_gap_raises_on_lookup(self) -> None:
        r1 = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            effective_until=datetime(2026, 2, 1, tzinfo=UTC),
        )
        r2 = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 3, 1, tzinfo=UTC),
            effective_until=None,
        )
        with pytest.raises(PricingGapError):
            PricingCatalog([r1, r2])

    def test_overlap_raises(self) -> None:
        r1 = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            effective_until=datetime(2026, 3, 1, tzinfo=UTC),
        )
        r2 = _row(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            effective_from=datetime(2026, 2, 1, tzinfo=UTC),
            effective_until=None,
        )
        with pytest.raises(PricingGapError):
            PricingCatalog([r1, r2])

    def test_price_step_transition_strict(self) -> None:
        t1 = datetime(2026, 3, 1, tzinfo=UTC)
        r1 = _row(
            ProviderName.ANTHROPIC,
            "m",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            effective_until=t1,
            input_rate="3.0",
        )
        r2 = _row(
            ProviderName.ANTHROPIC,
            "m",
            effective_from=t1,
            effective_until=None,
            input_rate="4.0",
        )
        cat = PricingCatalog([r1, r2])
        before = cat.lookup(
            ProviderName.ANTHROPIC,
            "m",
            CacheRetention.NONE,
            datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC),
        )
        after = cat.lookup(
            ProviderName.ANTHROPIC,
            "m",
            CacheRetention.NONE,
            datetime(2026, 3, 1, 0, 0, 0, tzinfo=UTC),
        )
        assert before.input_rate == Decimal("3.0")
        assert after.input_rate == Decimal("4.0")

    def test_cache_retention_separate_rows(self) -> None:
        r_short = _row(
            ProviderName.ANTHROPIC,
            "m",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            retention=CacheRetention.SHORT,
            input_rate="3.0",
        )
        r_long = _row(
            ProviderName.ANTHROPIC,
            "m",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            retention=CacheRetention.LONG,
            input_rate="3.0",
        )
        cat = PricingCatalog([r_short, r_long])
        assert (
            cat.lookup(
                ProviderName.ANTHROPIC,
                "m",
                CacheRetention.SHORT,
                datetime(2026, 4, 12, tzinfo=UTC),
            )
            is r_short
        )
        assert (
            cat.lookup(
                ProviderName.ANTHROPIC,
                "m",
                CacheRetention.LONG,
                datetime(2026, 4, 12, tzinfo=UTC),
            )
            is r_long
        )


class TestLoader:
    def test_load_seed_snapshot(self, snapshot_dir: Path) -> None:
        rows = load_snapshot_dir(snapshot_dir)
        assert len(rows) >= 10
        providers = {r.provider for r in rows}
        assert ProviderName.ANTHROPIC in providers
        assert ProviderName.OPENAI in providers
        assert ProviderName.GOOGLE in providers

    def test_snapshot_creates_valid_catalog(self, snapshot_dir: Path) -> None:
        rows = load_snapshot_dir(snapshot_dir)
        cat = PricingCatalog(rows)
        row = cat.lookup(
            ProviderName.ANTHROPIC,
            "claude-opus-4-6",
            CacheRetention.NONE,
            datetime(2026, 4, 12, tzinfo=UTC),
        )
        assert row.input_rate == Decimal("15.0000000000")

    def test_rejects_numeric_rate(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text(
            json.dumps(
                {
                    "rows": [
                        {
                            "provider": "anthropic",
                            "model_id": "x",
                            "cache_retention_key": "none",
                            "currency": "USD",
                            "input_rate": 3.0,
                            "output_rate": "15.0",
                            "cache_read_rate": "0.3",
                            "cache_write_rate": "3.75",
                            "effective_from": "2026-01-01T00:00:00+00:00",
                            "effective_until": None,
                        }
                    ]
                }
            )
        )
        with pytest.raises(ValueError, match="string-encoded"):
            load_snapshot_file(bad)
