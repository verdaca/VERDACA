"""In-memory pricing catalog with gap/overlap detection and point-in-time lookup."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from ..errors import PricingGapError, UnknownModelError
from ..models import CacheRetention, ModelPricing, ProviderName


class PricingCatalog:
    """Append-only, immutable pricing catalog.

    Loaded once from snapshots at startup. Lookups are pure functions of the
    request's (provider, model_id, cache_retention, started_at) tuple.
    """

    def __init__(self, rows: list[ModelPricing]) -> None:
        self._rows = list(rows)
        self._by_key: dict[
            tuple[ProviderName, str, CacheRetention], list[ModelPricing]
        ] = defaultdict(list)
        for row in self._rows:
            self._by_key[(row.provider, row.model_id, row.cache_retention_key)].append(row)

        for key, row_list in self._by_key.items():
            row_list.sort(key=lambda r: r.effective_from)
            self._validate_contiguous(key, row_list)

    @staticmethod
    def _validate_contiguous(
        key: tuple[ProviderName, str, CacheRetention],
        rows: list[ModelPricing],
    ) -> None:
        for prev, nxt in zip(rows, rows[1:]):
            if prev.effective_until is None:
                raise PricingGapError(
                    f"open-ended row followed by another row for {key}: "
                    f"{prev.effective_from}"
                )
            if prev.effective_until > nxt.effective_from:
                raise PricingGapError(
                    f"overlap in {key}: {prev.effective_until} > {nxt.effective_from}"
                )
            if prev.effective_until < nxt.effective_from:
                raise PricingGapError(
                    f"gap in {key}: [{prev.effective_until}, {nxt.effective_from})"
                )

    def lookup(
        self,
        provider: ProviderName,
        model_id: str,
        cache_retention: CacheRetention,
        started_at: datetime,
    ) -> ModelPricing:
        """Find the pricing row for this request. Exact half-open interval semantics."""
        key = (provider, model_id, cache_retention)
        rows = self._by_key.get(key)
        if not rows:
            if cache_retention != CacheRetention.NONE:
                rows = self._by_key.get((provider, model_id, CacheRetention.NONE))
                if not rows:
                    raise UnknownModelError(
                        f"no pricing for {provider}/{model_id} "
                        f"(retention={cache_retention})"
                    )
            else:
                raise UnknownModelError(f"no pricing for {provider}/{model_id}")

        for row in rows:
            if row.effective_from <= started_at and (
                row.effective_until is None or started_at < row.effective_until
            ):
                return row

        raise PricingGapError(
            f"no pricing row for {provider}/{model_id} at {started_at}"
        )

    def rows(self) -> list[ModelPricing]:
        return list(self._rows)

    def __len__(self) -> int:
        return len(self._rows)
