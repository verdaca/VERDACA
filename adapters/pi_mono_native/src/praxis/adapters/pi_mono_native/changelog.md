# praxis-adapter-pi_mono_native changelog

Per `ports-architecture.md` v0.2 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-08)

Initial in-tree-native Pi-Mono adapter implementing `CostMeterPort` per ADR-9.2-V4
(`ports-architecture.md` v0.3 §3). FIRST in-tree-native adapter in the repo (no
upstream package; no submodule; no TS bridge per Stage 9.2 ratification).
Sibling structural precedent: Beads in-tree-greenfield adapter (`adapters/beads/`).

Upstream: derivation-origin from Pi-Mono TS source dump-file fragment
`8a5edab282632443` (per `_bmad-output/planning-artifacts/src/badlogic-pi-mono-*.txt`
local reference dump). NOT a binding pin — the dump-file is informational
reference. Upgrade workflow skips this adapter (no upstream to bump). Monthly
drift check is parity-snapshot regeneration (manual, Andrey-approved per S12
disposition).

### ADR rationale (per Q-9.4.4-3 (β) adapter-side disposition)

Choice **NOT to bridge TS** documented inline in `adapter.py` module docstring
+ this changelog. No separate ADR file (Q-9.4.4-3 = (β); matches Beads
in-tree-native sibling precedent). Three reasons NOT to bridge:

1. **Process boundary cost.** Node↔Python bridge adds a process boundary for
   what is pure math (4 multiplications + 1 sum per record). Cost-meter is on
   hot path (every LLM call → one record() per Murat §4 stakeholder); sub-10ms
   target incompatible with cross-process IPC.
2. **Pricing table cadence.** Pricing tables drift at a pace a monthly workflow
   catches; in-tree ownership lets us update tables on first signal (e.g., new
   model release) rather than waiting on upstream release cadence.
3. **Surface size.** ~200 LOC of pricing math is small enough to own fully.
   Forking risk is bounded by snapshot parity test (M-T-COST-PARITY-01).

### Substance

- 3 `CostMeterPort` methods (`record`, `query`, `budget_check`) + lifecycle
  (`on_init` isinstance self-check; `on_shutdown` no-op per in-tree posture)
- Hardcoded `PRICING_TABLE` dict (8 representative models: 4 Anthropic, 2
  OpenAI, 2 Google) per S5 disposition. `pricing_table_version =
  sha256(canonical JSON)[:12]` per S6 — auto-derived; updates when table
  changes.
- Decimal arithmetic throughout per Q-9.4.4-5 amended (Decimal exact,
  formula-parity). Formula matches TS `models.ts:9692`
  `(model.cost.input / 1000000) * usage.input` re-expressed as
  `Decimal(price_per_M) / Decimal(1_000_000) * Decimal(tokens)`.
- 2 error specializations (per ADR-9.1.2-5 §3.4):
    - `PricingTableMismatch` raised by `record()` when (provider, model) not
      in pricing table; carries (provider, model, pricing_table_version)
    - `ParityDrift` raised by parity test (M-T-COST-PARITY-01); not normal
      operation
- In-process `dict[str, list[CostLedgerEntry]]` ledger keyed by
  `f"{scope_kind}:{scope_id}"` per S8.
- In-process `dict[str, CostLedgerEntry]` idempotency cache per S11.
  Durability across restart N/A per in-tree posture (no persistent state;
  caller-retry with same idempotency_key after restart produces fresh
  CostLedgerEntry — accepted at v0.1.0 since pricing math is deterministic
  and idempotency uniqueness is caller's discipline).

### v0.1.0 scope restrictions (deferred to Stage 10)

- **Cache cost components** (cacheRead / cacheWrite) deferred per S3. Pi-Mono
  TS source models 4 cost components; this adapter ships 2 (input + output).
  Port contract (CostBreakdown.input_cost_usd + output_cost_usd) matches
  v0.1.0 scope; cache fields would require a port-contracts.md corrigendum
  (Stage 10 territory).
- **Service-tier multipliers** (flex / priority) deferred per S4. Pi-Mono TS
  has service tier discrimination (flex=0.5, normal=1.0, priority=2.0);
  CostEvent does not model service_tier; v0.1.0 defaults to 1.0 (normal).

### Snapshot regeneration gate (per S12 disposition)

Per `test-strategy.md` v0.2 §2.2.5 M-T-COST-PARITY-01 wording: snapshot
regeneration is "Andrey-approved manual act". Concretely:

1. Pricing table changes (model added / removed / price update) → engineer
   drafts updated `PRICING_TABLE` in `adapter.py`.
2. Engineer regenerates parity fixture (`tests/fixtures/pi_mono_parity_vectors.json`)
   by computing expected costs under updated table using same Decimal formula.
3. Andrey reviews both the table change AND the regenerated fixture before
   merge.
4. M-T-COST-PARITY-01 in `test_cost_meter_contract.py` validates fixture↔adapter
   parity at every test run; any drift surfaces as test failure (NOT auto-correct).

### Stage 9.6 housekeeping items (per S10 disposition)

- `vendor/pi_mono_ts_reference/` archive directory NOT created at v0.1.0.
  ADR-9.2-V4 envisions archiving the TS source as read-only reference; the
  `_bmad-output/planning-artifacts/src/badlogic-pi-mono-*.txt` dump
  (gitignored) serves the same role at v0.1.0. Stage 9.6 / 9.4.7
  housekeeping should decide whether to formalize a tracked archive.

### Pre-Cleo invocation (per Q-9.4.4-6 = Option α)

```
PYTHONPATH='adapters/pi_mono_native/src' uv run --package praxis-contract-tests \
    pytest tests/src/praxis/contract_tests/ports/test_cost_meter_contract.py -v
```

Workspace registration of `adapters/pi_mono_native/` in repo-root
`pyproject.toml` + `uv.lock` is Cleo 9.6 territory. Pre-Cleo, the
`--package praxis-contract-tests` + `PYTHONPATH` override mirrors B.1/B.2/B.3
sibling precedent at 34a4eca / b14285b / ae1c806.
