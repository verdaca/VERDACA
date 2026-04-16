# Pricing snapshots

Monthly snapshots of provider pricing, loaded at `CostTracker.initialize()` time.

## Adding a snapshot

1. Copy the latest file, rename to `YYYY-MM-DD.json` (UTC date).
2. Update `effective_from` to the new effective instant and close the previous row's `effective_until`.
3. Rates are **string-encoded** — never bare JSON numbers. The loader rejects float-typed rates to avoid IEEE-754 parsing at boundary.
4. Run `pytest tests/unit/test_pricing_catalog.py` — gap/overlap detection will fail if windows are not contiguous.

## Row schema

```json
{
  "provider": "anthropic",
  "model_id": "claude-opus-4-6",
  "cache_retention_key": "none | short | long",
  "currency": "USD",
  "input_rate": "15.0000000000",
  "output_rate": "75.0000000000",
  "cache_read_rate": "1.5000000000",
  "cache_write_rate": "18.7500000000",
  "effective_from": "2026-01-01T00:00:00+00:00",
  "effective_until": null,
  "source_url": "https://..."
}
```

All rates are **USD per 1,000,000 tokens** (USD/MTok).
