# Pi-Mono Cost Tracker — Test Strategy

**Module:** `praxis.kernel.cost` (Pi-Mono)
**Stage:** Praxis Stage 1, Step 1.2 (Measurement Foundation)
**Author:** Murat (Test Architect)
**Date:** 2026-04-12
**Status:** Approved for Amelia implementation + Quinn execution
**Version:** 1.0
**Risk class:** RPN 20 — highest in the Praxis architecture
**Depends on:** `pi-mono-cost-tracker-architecture.md` (Winston, Stage 1.1)

---

## 0. EXECUTIVE SUMMARY

Winston has designed Pi-Mono so that the top-five Murat risks — float contamination, rounding drift, async race conditions, price drift, and sub-cent precision — are structurally impossible. My job is not to prove they are *unlikely*. My job is to prove they are *impossible* with tests that would fail in red if any structural guarantee slipped.

This strategy follows the Praxis risk-based pyramid:

```
            ┌──────────────────────────────┐
            │  Reconciliation (real data)  │   5%  — nightly, manual Stage 1
            ├──────────────────────────────┤
            │  E2E integration             │  10%  — CI per PR
            ├──────────────────────────────┤
            │  Contract + Golden fixtures  │  15%  — CI per PR
            ├──────────────────────────────┤
            │  Property-based (Hypothesis) │  25%  — CI per PR, fast
            ├──────────────────────────────┤
            │  Unit (pytest)               │  45%  — CI per commit
            └──────────────────────────────┘
```

Coverage targets are driven by risk, not by a flat percentage:

| Module | Coverage gate | Why this number |
|--------|---------------|-----------------|
| `math.py` | **100%** line + branch | Single point of cost math; any uncovered branch is an uncounted dollar |
| `models.py` | **100%** line | Pure Pydantic; validators are the model boundary |
| `providers/*.py` | **100%** line | Golden fixtures make this trivially achievable |
| `tracker.py` | **≥95%** line, **90%** branch | Idempotency + error paths must be exercised |
| `storage/*` | **≥95%** line | Round-trip on both SQLite and Postgres |
| `pricing/*` | **≥95%** line | Gap/overlap detection must fire |
| `reconciliation.py` | **≥95%** line | Drift math and tolerance bands |
| `aggregator.py` | **≥95%** line | Sum invariants |
| `events.py` | **≥90%** line | Outbox delivery + replay |
| `telemetry.py` | **≥85%** line | OTel covered where practical; justified gaps |

Aggregate target per R11: ≥95% for the module overall.

Any PR that drops below a gate fails the build. Test coverage is measured by `coverage.py` with branch coverage enabled; the gate runs in CI after the test suite.

---

## 1. RISK REGISTER (SOURCE OF PRIORITY)

Every test in this plan is anchored to a Murat risk or a Winston-recognised architectural invariant. If a test does not map to one, it is not worth writing.

| ID | Risk | RPN | Primary test layer | Secondary |
|----|------|-----|-------------------|-----------|
| M1 | Floating-point cost calculations | 20 | Property (Hypothesis) + static (mypy `--strict` + ruff) | Golden fixtures |
| M2 | Rounding drift on cache token pricing | 18 | Property + parametrized | Golden fixtures, reconciliation |
| M3 | Async race conditions in concurrent `track_cost` | 16 | Concurrent stress (asyncio.gather) | Property (P6, P9) |
| M4 | Cross-provider price drift | 16 | Real-invoice reconciliation (manual in Stage 1) | Unit with synthetic invoices |
| M5 | Sub-cent currency precision loss | 15 | Property with extreme ratios | Golden fixtures |
| M6 | Provider SDK field renames | 12 | Golden fixtures per provider | Contract |
| M7 | Pricing gap / overlap at catalog load | 12 | Unit + edge-case fixtures | Property |
| M8 | Retry storm writes duplicate records | 12 | Concurrent stress + integration | Property P6 |
| M9 | Event outbox loses a record_created | 10 | Transactional integration test | Stress |
| M10 | Snapshot JSON parsed as float | 10 | Parametrized unit with adversarial JSON | Static (ruff) |

**M1 and M2 dominate.** They get the most test budget. Everything else is handled but not over-invested.

---

## 2. TEST ORGANIZATION

### 2.1 Directory layout (mirrors Winston's module structure)

```
praxis/kernel/cost/
└── tests/
    ├── conftest.py                 # Shared fixtures (tracker, clock, snapshots)
    ├── unit/
    │   ├── test_math.py            # compute_cost properties and edge cases
    │   ├── test_models.py          # Pydantic validators
    │   ├── test_pricing_catalog.py # load, gap, overlap, lookup
    │   ├── test_providers_base.py  # Protocol conformance
    │   ├── test_provider_anthropic.py
    │   ├── test_provider_openai.py
    │   ├── test_provider_google.py
    │   └── test_provider_fake.py
    ├── property/
    │   ├── test_math_properties.py      # P1-P5, P10, P11
    │   ├── test_tracker_idempotency.py  # P6, P9
    │   ├── test_provider_purity.py      # P7
    │   └── test_reconcile_exact.py      # P8
    ├── golden/
    │   ├── fixtures/                    # JSON blobs — see §4
    │   ├── test_anthropic_golden.py
    │   ├── test_openai_golden.py
    │   ├── test_google_golden.py
    │   ├── test_cost_math_golden.py
    │   └── update_golden.py             # Regeneration tool
    ├── integration/
    │   ├── test_tracker_sqlite.py       # Full tracker against SQLite
    │   ├── test_tracker_postgres.py     # Full tracker against Postgres (Docker)
    │   ├── test_stream_events.py        # Outbox + stream_events
    │   ├── test_reconciliation.py       # Synthetic invoice path
    │   └── test_health.py
    ├── stress/
    │   ├── test_concurrent_track_cost.py   # asyncio.gather with shared request_id
    │   ├── test_high_volume.py             # 100K calls, mock storage
    │   └── test_perf_hot_path.py           # <1ms median target (R10)
    ├── reconciliation/
    │   ├── fixtures/                    # Synthetic and (later) real invoices
    │   ├── test_manual_reconciliation.py
    │   └── test_drift_math.py
    └── static/
        ├── test_no_float_imports.py     # AST scan: no `float(` in cost math paths
        └── test_type_safety.py          # Run mypy --strict and fail on errors
```

### 2.2 Test markers

```
@pytest.mark.unit
@pytest.mark.property
@pytest.mark.golden
@pytest.mark.integration
@pytest.mark.stress          # slow; excluded from default run
@pytest.mark.reconciliation  # requires invoice fixtures; opt-in
@pytest.mark.static          # ast / mypy / ruff
@pytest.mark.postgres        # requires Docker; skipped if unavailable
```

Default CI job runs `unit + property + golden + integration + static`. Nightly job adds `stress + reconciliation`.

### 2.3 Fixture hierarchy

```
conftest.py
├── pricing_snapshot_dir() → Path          # Points to seed fixtures
├── frozen_clock() → Callable              # Deterministic time
├── tmp_sqlite_tracker() → CostTracker     # Fresh in-mem DB per test
├── seeded_sqlite_tracker() → CostTracker  # Pre-loaded with sample records
├── postgres_tracker() → CostTracker       # Docker-backed; skip if not avail
├── mock_provider() → FakeProvider         # Deterministic token extractor
├── sample_llm_request() → LLMRequest      # Canonical request
├── sample_llm_response() → LLMResponse    # Canonical response
└── decimal_strategies()                   # Hypothesis strategies factory
```

---

## 3. PROPERTY-BASED TESTS (Hypothesis)

The architecture sections §9.1 and §9.2 enumerate eleven properties (P1–P11). This section turns them into concrete Hypothesis strategies and expected shapes. Amelia implements them; Quinn runs them.

### 3.1 Strategies (shared in `conftest.py`)

```
# Token counts: int, non-negative, bounded to prevent Hypothesis explosion
token_count_strategy = st.integers(min_value=0, max_value=10_000_000)

# Rates: Decimal, stringified, 0 to $1000/MTok, 10 decimal places
rate_strategy = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1000"),
    places=10,
    allow_nan=False,
    allow_infinity=False,
)

# Timestamps: UTC only, reasonable range
timestamp_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1, tzinfo=UTC),
    max_value=datetime(2030, 1, 1, tzinfo=UTC),
    timezones=st.just(UTC),
)

# ULIDs: valid Crockford base32, 26 chars
ulid_strategy = st.from_regex(r"^[0-9A-HJKMNP-TV-Z]{26}$", fullmatch=True)

# Scope IDs: None or short string
scope_id_strategy = st.one_of(
    st.none(),
    st.text(alphabet="abcdefg0123456789", min_size=1, max_size=26),
)
```

All strategies explicitly exclude `float` because Hypothesis's default `st.decimals()` returns `Decimal` — we verify via `assert isinstance(x, Decimal)` in the body of each test that uses it.

### 3.2 P1 — Zero tokens → zero cost

**File:** `tests/property/test_math_properties.py::test_zero_tokens_zero_cost`

```
@given(pricing=pricing_strategy())
def test_zero_tokens_zero_cost(pricing):
    resp = llm_response_with_zeros()
    cost = compute_cost(resp, pricing)
    assert cost.total == Decimal("0")
    assert cost.input == Decimal("0")
    assert cost.output == Decimal("0")
    assert cost.cache_read == Decimal("0")
    assert cost.cache_write == Decimal("0")
```

**Expected failures:** Any non-Decimal returned type; any non-zero component.

### 3.3 P2 — Cost is non-negative

```
@given(resp=llm_response_strategy(), pricing=pricing_strategy())
def test_cost_non_negative(resp, pricing):
    cost = compute_cost(resp, pricing)
    assert cost.input >= Decimal("0")
    assert cost.output >= Decimal("0")
    assert cost.cache_read >= Decimal("0")
    assert cost.cache_write >= Decimal("0")
    assert cost.total >= Decimal("0")
```

### 3.4 P3 — Total equals sum of components (exact Decimal equality)

**Most load-bearing property in the suite.** If this fails, the architecture is wrong, not the test.

```
@given(resp=llm_response_strategy(), pricing=pricing_strategy())
@settings(max_examples=10_000, deadline=None)
def test_total_equals_sum_exact(resp, pricing):
    cost = compute_cost(resp, pricing)
    assert cost.total == cost.input + cost.output + cost.cache_read + cost.cache_write
    assert isinstance(cost.total, Decimal)
```

Bumped to 10,000 examples because M1 is RPN 20 and we want wide coverage.

### 3.5 P4 — Linearity in tokens (up to rounding tolerance)

```
@given(
    resp=llm_response_strategy(),
    pricing=pricing_strategy(),
    k=st.integers(min_value=1, max_value=1000),
)
def test_cost_linear_in_tokens(resp, pricing, k):
    scaled_resp = scale_tokens(resp, k)
    single = compute_cost(resp, pricing)
    scaled = compute_cost(scaled_resp, pricing)
    # Up to 4 * QUANTUM tolerance — each of 4 components may round once
    assert abs(scaled.total - k * single.total) <= Decimal("4e-10")
```

**Note:** Linear equality would fail because of quantization per component. The tolerance is exactly `4 * QUANTUM` per §9.2 P4.

### 3.6 P5 — Aggregation associativity

```
@given(st.lists(llm_response_strategy(), min_size=3, max_size=10), pricing_strategy())
def test_aggregation_associative(responses, pricing):
    totals = [compute_cost(r, pricing).total for r in responses]
    assert sum(totals) == sum(reversed(totals))
```

Trivially true for Decimal addition; the test *pins* it so a future refactor to `numpy.sum` fails loudly.

### 3.7 P6 — Idempotency on `request_id`

**File:** `tests/property/test_tracker_idempotency.py`

```
@given(req_resp_pair_strategy())
async def test_track_cost_idempotent(tracker, req_resp_pair):
    req, resp = req_resp_pair
    r1 = await tracker.track_cost(req, resp)
    r2 = await tracker.track_cost(req, resp)
    assert r1.record_id == r2.record_id
    assert r1.cost == r2.cost
    assert count_rows(tracker, "cost_records", request_id=req.request_id) == 1
```

### 3.8 P7 — Provider extraction is pure

```
@given(raw_response_strategy())
def test_extract_tokens_pure(raw_response):
    r1 = AnthropicProvider.extract_tokens(request, raw_response)
    r2 = AnthropicProvider.extract_tokens(request, raw_response)
    assert r1 == r2
```

Run for each provider.

### 3.9 P8 — Reconciliation exact on synthetic invoices

```
@given(st.lists(cost_record_strategy(), min_size=1, max_size=100))
async def test_reconciliation_clean_on_synthetic(tracker, records):
    for r in records:
        await tracker._raw_insert_record(r)  # test helper
    invoice = synthesize_invoice_from(records)
    report = await tracker.reconcile(invoice)
    assert report.status == "clean"
    assert report.total_delta == Decimal("0")
```

### 3.10 P9 — Concurrent track_cost with same request_id is safe

**File:** `tests/stress/test_concurrent_track_cost.py` (stress, not property, because it needs a real event loop)

```
async def test_concurrent_same_request_id(tracker):
    req, resp = canonical_pair()
    results = await asyncio.gather(*[
        tracker.track_cost(req, resp) for _ in range(100)
    ])
    assert all(r.record_id == results[0].record_id for r in results)
    assert count_rows(tracker, "cost_records", request_id=req.request_id) == 1
    assert count_rows(tracker, "events_outbox", record_id=results[0].record_id) == 1
```

### 3.11 P10 — Pricing gap detection

```
def test_pricing_gap_raises():
    catalog = load_catalog([
        make_row(effective_from=t0, effective_until=t1, rate="3"),
        make_row(effective_from=t2, effective_until=None, rate="4"),  # t2 > t1, gap
    ])
    with pytest.raises(PricingGapError):
        catalog.lookup("anthropic", "claude-opus-4-6", started_at=t1_5)  # in the gap
```

### 3.12 P11 — Price step transition is strict

```
def test_price_step_transition_strict():
    catalog = load_catalog([
        make_row(effective_from=t0, effective_until=t1, rate="3"),
        make_row(effective_from=t1, effective_until=None, rate="4"),
    ])
    before = catalog.lookup("anthropic", "model", started_at=t1 - timedelta(milliseconds=1))
    after = catalog.lookup("anthropic", "model", started_at=t1 + timedelta(milliseconds=1))
    assert before.input_rate == Decimal("3")
    assert after.input_rate == Decimal("4")
```

### 3.13 Additional properties Murat adds beyond Winston's list

**P12 — Pydantic rejects float at model boundary.**

```
@given(st.floats(min_value=0, max_value=1000, allow_nan=False))
def test_pydantic_rejects_float_rate(float_rate):
    with pytest.raises(ValidationError):
        ModelPricing(
            ...,
            input_rate=float_rate,  # must be Decimal or str
        )
```

**P13 — JSON snapshots must be string-encoded, not numeric.**

```
def test_snapshot_loader_rejects_numeric_rate(tmp_path):
    snapshot = tmp_path / "bad.json"
    snapshot.write_text('{"rows": [{"input_rate": 3.0}]}')  # numeric, not "3.0"
    with pytest.raises(ValueError, match="must be string-encoded"):
        load_snapshot(snapshot)
```

**P14 — `Decimal(float)` is explicitly forbidden in cost path.**

Static test, not a Hypothesis property. See §7.2.

**P15 — Total_tokens equals sum of class tokens (CostRecord invariant).**

```
@given(cost_record_strategy())
def test_total_tokens_invariant(record):
    assert record.total_tokens == (
        record.input_tokens + record.output_tokens
        + record.cache_read_tokens + record.cache_write_tokens
    )
```

---

## 4. GOLDEN FILE FIXTURES

Goldens catch provider SDK drift. They do not catch logic errors (properties do that). They are the lock on the door — if Anthropic renames `cache_creation_input_tokens` in SDK v3, the golden file breaks immediately.

### 4.1 Fixture layout (matches Winston §9.3)

```
tests/golden/fixtures/
├── providers/
│   ├── anthropic/
│   │   ├── opus_4_6_simple.raw.json
│   │   ├── opus_4_6_simple.expected.json
│   │   ├── opus_4_6_with_short_cache.raw.json
│   │   ├── opus_4_6_with_short_cache.expected.json
│   │   ├── opus_4_6_with_long_cache.raw.json
│   │   ├── opus_4_6_with_long_cache.expected.json
│   │   ├── sonnet_4_6_tool_use.raw.json
│   │   ├── sonnet_4_6_tool_use.expected.json
│   │   ├── sonnet_4_6_error_stop.raw.json
│   │   ├── sonnet_4_6_error_stop.expected.json
│   │   ├── haiku_4_5_zero_tokens.raw.json           # edge case §9.5.1
│   │   └── haiku_4_5_zero_tokens.expected.json
│   ├── openai/
│   │   ├── gpt_5_simple.raw.json
│   │   ├── gpt_5_simple.expected.json
│   │   ├── gpt_5_cached_subtraction.raw.json        # M2 trap — input_tokens = fresh+cached
│   │   ├── gpt_5_cached_subtraction.expected.json
│   │   ├── gpt_5_stop_length.raw.json
│   │   └── gpt_5_stop_length.expected.json
│   └── google/
│       ├── gemini_3_1_simple.raw.json
│       ├── gemini_3_1_simple.expected.json
│       ├── gemini_3_1_camel_case.raw.json           # inputTokens variant
│       ├── gemini_3_1_camel_case.expected.json
│       ├── gemini_3_1_snake_case.raw.json           # input_tokens variant
│       ├── gemini_3_1_snake_case.expected.json
│       ├── gemini_3_1_with_cache.raw.json
│       └── gemini_3_1_with_cache.expected.json
├── cost_math/
│   ├── zero_tokens.case.json
│   ├── extreme_cache_write_long_retention.case.json
│   ├── cache_read_only_haiku.case.json              # edge case §9.5.15
│   ├── rounding_halfway_banker.case.json            # banker's rounding tie-break
│   ├── rounding_halfway_round_up.case.json          # non-tie, rounds up
│   ├── rounding_halfway_round_down.case.json        # non-tie, rounds down
│   ├── one_billion_tokens.case.json                 # edge case §9.5.5
│   ├── zero_rate_input.case.json                    # edge case §9.5.4
│   └── all_rates_zero.case.json
└── pricing/
    ├── anthropic_2026_04.json
    ├── openai_2026_04.json
    ├── google_2026_04.json
    ├── anthropic_2026_04_with_long_cache.json       # separate row for long retention
    └── gap_test.json                                 # pricing with deliberate gap (for P10)
```

### 4.2 Golden file format — provider

`*.raw.json` captures the provider SDK's native response, unmodified. `*.expected.json` captures the expected `LLMResponse` as a JSON-serialized Pydantic model.

```
# opus_4_6_with_short_cache.raw.json
{
  "id": "msg_01A9...",
  "type": "message",
  "role": "assistant",
  "model": "claude-opus-4-6",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "cache_creation_input_tokens": 8910,
    "cache_read_input_tokens": 1112
  }
}

# opus_4_6_with_short_cache.expected.json
{
  "request_id": "01JAAAAAAAAAAAAAAAAAAAAAAA",
  "input_tokens": 1234,
  "output_tokens": 567,
  "cache_read_tokens": 1112,
  "cache_write_tokens": 8910,
  "finished_at": "2026-04-12T14:22:19.204000+00:00",
  "stop_reason": "stop",
  "error_message": null
}
```

### 4.3 Golden file format — cost math

```
# extreme_cache_write_long_retention.case.json
{
  "description": "Anthropic long cache write is 2x input rate; M2 regression.",
  "risk": "M2",
  "response": {
    "request_id": "01JAAAAAAAAAAAAAAAAAAAAAAA",
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_tokens": 0,
    "cache_write_tokens": 1000000,
    "finished_at": "2026-04-12T14:22:19.204000+00:00",
    "stop_reason": "stop",
    "error_message": null
  },
  "pricing": {
    "provider": "anthropic",
    "model_id": "claude-opus-4-6",
    "cache_retention_key": "long",
    "currency": "USD",
    "input_rate": "15.0000000000",
    "output_rate": "75.0000000000",
    "cache_read_rate": "1.5000000000",
    "cache_write_rate": "30.0000000000",
    "effective_from": "2026-04-01T00:00:00+00:00",
    "effective_until": null,
    "source_url": "https://anthropic.com/pricing",
    "snapshot_sha256": "abc123..."
  },
  "expected_cost": {
    "input": "0.0000000000",
    "output": "0.0000000000",
    "cache_read": "0.0000000000",
    "cache_write": "30.0000000000",
    "total": "30.0000000000",
    "currency": "USD"
  }
}
```

### 4.4 Golden tests — the loop

```
@pytest.mark.parametrize(
    "case_file",
    sorted((FIXTURE_DIR / "cost_math").glob("*.case.json"))
)
def test_cost_math_golden(case_file):
    case = json.loads(case_file.read_text())
    resp = LLMResponse.model_validate(case["response"])
    pricing = ModelPricing.model_validate(case["pricing"])
    expected = CostAmount.model_validate(case["expected_cost"])

    actual = compute_cost(resp, pricing)

    assert actual == expected, f"Golden mismatch in {case_file.name}"
```

**Regeneration:** Golden files are regenerated only by running `python -m praxis.kernel.cost.tests.update_golden --confirm`. Any PR that modifies a golden file without running the script is rejected by a pre-commit hook (see §7.3).

### 4.5 Provider golden tests

```
@pytest.mark.parametrize(
    "raw_file",
    sorted((FIXTURE_DIR / "providers" / "anthropic").glob("*.raw.json"))
)
def test_anthropic_golden(raw_file):
    raw = json.loads(raw_file.read_text())
    expected_file = raw_file.with_suffix(".expected.json").with_name(
        raw_file.name.replace(".raw.json", ".expected.json")
    )
    expected = json.loads(expected_file.read_text())
    request = synthesize_request_from_expected(expected)
    actual = AnthropicProvider.extract_tokens(request, raw)
    assert actual.model_dump(mode="json") == expected
```

One test function per provider; parametrized over every `*.raw.json` in its directory.

---

## 5. UNIT TESTS

### 5.1 `tests/unit/test_math.py`

Covers `compute_cost` edge cases that Hypothesis may not hit with the default `max_examples`.

- `test_compute_cost_zero_tokens` — all four token classes zero, all components zero.
- `test_compute_cost_input_only` — only input tokens non-zero.
- `test_compute_cost_output_only` — only output tokens non-zero.
- `test_compute_cost_cache_read_only` — full cache hit (edge case §9.5.2).
- `test_compute_cost_cache_write_only` — fresh cache write, no output.
- `test_compute_cost_all_four_classes` — all non-zero, verify sum.
- `test_compute_cost_large_tokens_1B` — 10⁹ tokens, must not overflow (Python int is unbounded but verify anyway).
- `test_compute_cost_zero_rate` — input_rate=0 produces zero input cost without DivisionByZero.
- `test_compute_cost_banker_rounding` — cost ending in .5 rounds even-ward.
- `test_compute_cost_context_isolation` — global Decimal context untouched after call.
- `test_compute_cost_returns_decimal_components` — isinstance check on each field.

### 5.2 `tests/unit/test_models.py`

Pydantic validator enforcement.

- `test_llm_request_requires_tz_aware_datetime` — naive datetime rejected.
- `test_llm_request_rejects_bad_ulid` — non-ULID request_id rejected.
- `test_llm_request_tag_size_limit` — >32 keys rejected.
- `test_llm_request_tag_value_length_limit` — >128 char value rejected.
- `test_llm_response_negative_tokens_rejected` — each token class.
- `test_llm_response_error_requires_message` — stop_reason="error" without error_message rejected.
- `test_cost_amount_total_sum_invariant_rejected_if_violated` — manually-constructed CostAmount with bad total fails validation.
- `test_cost_record_total_tokens_invariant` — same for token sum.
- `test_pricing_rejects_negative_rate` — each of four rates.
- `test_pricing_effective_until_after_effective_from` — rejected if not.
- `test_frozen_models_immutable` — attempt to assign `.total = Decimal("1")` raises.

### 5.3 `tests/unit/test_pricing_catalog.py`

- `test_load_valid_snapshot` — happy path.
- `test_load_snapshot_with_gap_raises` — P10 repeated as unit.
- `test_load_snapshot_with_overlap_raises` — two rows sharing a time point.
- `test_load_snapshot_string_rate_parsed_to_decimal` — `"3.00"` → `Decimal("3.00")`.
- `test_load_snapshot_numeric_rate_rejected` — `3.00` (bare) → ValueError.
- `test_load_snapshot_computes_sha256` — snapshot hash populated.
- `test_lookup_current_row` — `effective_until=None` is "current".
- `test_lookup_historical_row` — request in the middle of a window.
- `test_lookup_boundary_inclusive_from` — exact `effective_from`.
- `test_lookup_boundary_exclusive_until` — exact `effective_until` uses the NEXT row, not this one.
- `test_lookup_unknown_model_raises` — `UnknownModelError`.
- `test_lookup_gap_raises` — `PricingGapError`.
- `test_cache_retention_dispatch` — correct row for short vs long.
- `test_cache_retention_none_fallback` — `cache_retention=none` uses the "none" row if present.

### 5.4 `tests/unit/test_providers_*.py`

Beyond golden fixtures:

- `test_anthropic_end_turn_to_stop` — stop_reason mapping.
- `test_anthropic_max_tokens_to_length` — stop_reason mapping.
- `test_anthropic_tool_use_preserved` — stop_reason mapping.
- `test_anthropic_missing_cache_fields_default_zero` — robust to older SDKs.
- `test_openai_cached_tokens_subtracted` — the subtraction trap.
- `test_openai_zero_cached_input_handled` — path where `cached_tokens` is absent.
- `test_google_camel_and_snake_case_both_parsed` — field name variants.
- `test_google_computes_own_total_ignoring_provider_sum` — cross-check.
- `test_fake_provider_deterministic` — same input, same output.
- `test_provider_registry_register_and_lookup` — round-trip.
- `test_provider_registry_duplicate_rejected` — re-registering same name.
- `test_unknown_provider_raises` — lookup miss.

### 5.5 `tests/unit/test_static_noflot.py`

AST scan of `praxis/kernel/cost/*.py` for disallowed constructs. See §7.2.

---

## 6. INTEGRATION TESTS

Integration tests exercise `CostTracker` end-to-end against a real DB backend.

### 6.1 `tests/integration/test_tracker_sqlite.py`

- `test_initialize_and_close_clean` — `async with` context manager works.
- `test_track_cost_happy_path` — one request, one record, one event.
- `test_track_cost_writes_record_and_event_in_same_tx` — kill the connection between record write and event write; verify atomicity (both or neither).
- `test_get_session_cost_happy_path` — N records in same session → summary.
- `test_get_session_cost_empty_session_returns_zero_summary` — never None (§4.3 post-condition).
- `test_get_workflow_cost_happy_path` — same, by workflow_id.
- `test_get_agent_cost_time_range_filter` — partial overlap tests.
- `test_get_cost_summary_with_complex_filter` — tags + time_range + provider.
- `test_stream_events_from_empty` — no events yet.
- `test_stream_events_receives_new_record_created` — subscribe, write, receive.
- `test_stream_events_replay_from_event_id` — resume from a specific id.
- `test_reconcile_clean_happy_path` — synthetic invoice exactly matches.
- `test_reconcile_drift_detected` — force a mismatch.
- `test_unknown_model_raises_and_nothing_written` — failure atomicity.
- `test_pricing_gap_raises_and_nothing_written` — same.
- `test_idempotent_double_tracking` — second call returns first record.
- `test_health_reports_status` — sanity of health endpoint.

### 6.2 `tests/integration/test_tracker_postgres.py`

Same suite, different engine. Marker: `@pytest.mark.postgres`. Skipped if `PRAXIS_TEST_POSTGRES_URL` is unset.

Additional tests specific to Postgres dialect:
- `test_tags_gin_index_used` — `EXPLAIN` verifies the GIN index is chosen for a `@>` query.
- `test_listen_notify_event_stream` — Postgres-specific event path.
- `test_concurrent_writer_row_mvcc` — two clients writing different `request_id` in parallel succeed; same `request_id` conflict returns the first.

### 6.3 Dialect divergence tests

- `test_dialect_upsert_sqlite_semantics` — BEGIN IMMEDIATE path.
- `test_dialect_upsert_postgres_semantics` — ON CONFLICT path.
- `test_outbox_poller_sqlite` — polling interval + new event pickup.
- `test_outbox_listener_postgres` — NOTIFY wake-up.

---

## 7. STATIC / STRUCTURAL TESTS

These are the "structural impossibility" guarantees. They run as part of the test suite but do not execute business logic.

### 7.1 `tests/static/test_type_safety.py`

```
def test_mypy_strict_clean():
    result = subprocess.run(
        ["mypy", "--strict", "praxis/kernel/cost"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"mypy errors:\n{result.stdout}"
```

### 7.2 `tests/static/test_no_float_imports.py`

AST scan of every `.py` file under `praxis/kernel/cost/` (excluding `telemetry.py` which has one allowed `float()` call for Prometheus).

```
FORBIDDEN_IN_COST_PATHS = {"float", "math.floor", "math.ceil", "numpy", "pandas"}
ALLOWED_FLOAT_FILES = {"telemetry.py"}  # Prometheus boundary

def test_no_float_in_cost_math():
    for path in cost_module_python_files():
        if path.name in ALLOWED_FLOAT_FILES:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "float":
                pytest.fail(f"{path}:{node.lineno} uses float()")
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in FORBIDDEN_IN_COST_PATHS:
                        pytest.fail(f"{path}:{node.lineno} imports {name.name}")
```

Covers **T1–T12** in Winston §6.4 structurally.

### 7.3 `tests/static/test_golden_not_hand_edited.py`

Every golden file has a `_generated_by` metadata block that is written by `update_golden.py`. If a hand-edit changes a file without touching `_generated_by`, the test fails.

```
def test_goldens_have_generator_signature():
    for f in all_golden_files():
        data = json.loads(f.read_text())
        assert "_generated_by" in data, f"{f} missing generator signature"
        assert data["_generated_by"].startswith("update_golden.py")
```

---

## 8. STRESS AND PERFORMANCE TESTS

Nightly, not per-PR.

### 8.1 `tests/stress/test_perf_hot_path.py`

```
async def test_track_cost_median_under_1ms():
    tracker = build_tracker_with_mock_storage()
    req, resp = canonical_pair()
    latencies = []
    for _ in range(100_000):
        t0 = time.perf_counter()
        await tracker.track_cost(req, resp)
        latencies.append(time.perf_counter() - t0)
    median = statistics.median(latencies)
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]
    assert median < 0.001, f"median {median*1000:.3f}ms exceeds 1ms target"
    assert p99 < 0.002, f"p99 {p99*1000:.3f}ms exceeds 2ms target"
```

`build_tracker_with_mock_storage` returns a tracker whose storage is a dict, not SQLite — the target is pure-compute overhead.

### 8.2 `tests/stress/test_high_volume.py`

- `test_100k_concurrent_different_request_ids` — all succeed, no data lost, no duplicates.
- `test_100k_concurrent_same_request_id` — one succeeds, 99,999 see the existing record.
- `test_outbox_grows_under_backpressure` — stream_events subscriber deliberately blocks; outbox depth monitored.
- `test_outbox_sweeper_cleans_delivered_events` — retention policy fires.

### 8.3 `tests/stress/test_reconciliation_large_invoice.py`

10,000 synthetic records, reconciled against a 10,000-line invoice. Target: <10 seconds wall clock.

---

## 9. RECONCILIATION TEST STRATEGY

### 9.1 Stage 1 — manual bootstrap

- Bring one historical invoice PDF (Anthropic billing export, October 2025 or earlier).
- Manually parse into `Invoice` JSON.
- Run `tracker.reconcile(invoice)` against synthetic `cost_records` reconstructed from Claude Max usage exports.
- Expected outcome: `within_tolerance` at worst (invoice granularity is per-day, our records are per-request; small timing mismatches are normal).
- Any `drift_detected` opens an issue and blocks Stage 2.

### 9.2 Stage 2+ — automated

- Nightly job downloads all provider invoices via billing APIs.
- Parses into `Invoice` objects.
- Runs reconciliation.
- Posts a Slack alert if any report is `drift_detected` or worse.
- Historical drift tracked in a `reconciliation_trend` dashboard.

### 9.3 Synthetic invoice property test (in-scope for Stage 1)

Covered by P8 in §3.9. Implementation is in `tests/property/test_reconcile_exact.py`.

---

## 10. EDGE CASE COVERAGE CHECKLIST

From Winston §9.5 — each edge case gets at least one named test. Mapping:

| Winston edge case | Test name |
|---|---|
| 9.5.1 zero-token response | `test_compute_cost_zero_tokens` + `haiku_4_5_zero_tokens` golden |
| 9.5.2 all cache reads | `test_compute_cost_cache_read_only` + `cache_read_only_haiku` golden |
| 9.5.3 negative token rejected | `test_llm_response_negative_tokens_rejected` |
| 9.5.4 zero rate | `test_compute_cost_zero_rate` + `zero_rate_input` golden |
| 9.5.5 extreme token count | `test_compute_cost_large_tokens_1B` + `one_billion_tokens` golden |
| 9.5.6 1ms pricing window | `test_lookup_one_ms_window` (unit) |
| 9.5.7 same effective_from | `test_load_snapshot_with_overlap_raises` |
| 9.5.8 gap between rows | `test_load_snapshot_with_gap_raises` + P10 |
| 9.5.9 concurrent snapshot reload | `test_snapshot_atomic_swap` (integration) |
| 9.5.10 UTC-naive datetime | `test_llm_request_requires_tz_aware_datetime` |
| 9.5.11 DST / leap second | Documented as non-issue; no test |
| 9.5.12 ULID collision | Not tested (astronomically improbable) |
| 9.5.13 unknown invoice model_id | `test_reconcile_unknown_model_in_invoice` (integration) |
| 9.5.14 partial-period invoice | `test_reconcile_partial_period_inclusive_exclusive` (integration) |
| 9.5.15 sub-quantum cost | `rounding_halfway_banker` + `cache_read_only_haiku` goldens |
| 9.5.16 cache_write with cache_retention=none | `test_provider_warns_on_inconsistent_cache` (unit) |
| 9.5.17 numeric rate in JSON | `test_load_snapshot_numeric_rate_rejected` |

All 17 covered.

---

## 11. CI PIPELINE INTEGRATION

### 11.1 Job layout (GitHub Actions, adaptable to GitLab CI)

```
jobs:
  lint:
    - ruff check praxis/kernel/cost
    - ruff format --check praxis/kernel/cost
    - mypy --strict praxis/kernel/cost

  unit:
    - pytest tests/unit -m "unit" --cov=praxis.kernel.cost --cov-branch
    - coverage report --fail-under=95

  property:
    - pytest tests/property -m "property" --hypothesis-profile=ci

  golden:
    - pytest tests/golden -m "golden"

  static:
    - pytest tests/static -m "static"

  integration-sqlite:
    - pytest tests/integration -m "integration and not postgres"

  integration-postgres:
    services:
      postgres: postgres:16
    - pytest tests/integration -m "postgres"

  nightly (cron):
    - pytest tests/stress -m "stress"
    - pytest tests/reconciliation -m "reconciliation"
```

### 11.2 Gates (per-PR blocking)

- Lint clean.
- All unit / property / golden / integration / static tests pass.
- Coverage ≥95% aggregate.
- `math.py` and `models.py` coverage = 100%.
- No new golden file modifications without `update_golden.py --confirm` in the commit.

### 11.3 Quality gates (graduation)

| Gate | Criteria | Owner |
|------|---------|-------|
| Q1 | Property test suite runs clean with 10k examples | Quinn |
| Q2 | Golden fixtures cover all 3 providers + all stop_reasons | Quinn |
| Q3 | `no_float` static test green | Quinn |
| Q4 | `mypy --strict` green | Amelia |
| Q5 | Integration tests green on SQLite + Postgres | Quinn |
| Q6 | Perf target <1ms median met | Quinn |
| Q7 | Manual reconciliation within tolerance | Murat (me) |

Stage 1 graduates only when Q1–Q7 are all green.

---

## 12. HYPOTHESIS CONFIGURATION

```
# pyproject.toml
[tool.hypothesis]
max_examples = 200            # default
deadline = 5000               # ms

[tool.hypothesis.profiles.ci]
max_examples = 1000
deadline = 10000

[tool.hypothesis.profiles.nightly]
max_examples = 50000
deadline = null
derandomize = false

[tool.hypothesis.profiles.dev]
max_examples = 50
deadline = 2000
```

**Shrinking:** Hypothesis default shrinker is enabled. Failing examples must be minimized before filing an issue.

**Flakiness policy:** Any Hypothesis test that is flaky on CI is quarantined immediately (marked `@pytest.mark.flaky`) and must be fixed within one sprint. Flaky property tests usually indicate a hidden non-determinism in production code — not a test problem.

---

## 13. WHAT THIS PLAN DELIBERATELY DOES NOT COVER

- **UI / Dashboard tests** — dashboard is Step 1.3, out of scope for this test strategy.
- **Real-provider API calls in CI** — expensive and flaky; integration tests use goldens and mocks.
- **Cross-stage integration** — Stage 2+ concerns. This plan is Stage 1 only.
- **Benchmarks against competitors** — pre-sales metric capture lives in Step 1.6, not here.
- **Security tests** — no secrets in this module; no input parsing from untrusted sources except provider SDK payloads, which are contained by Pydantic validation.

---

## 14. HANDOFF TO AMELIA

**Amelia:** Implement the module per Winston's architecture doc. Every public function Winston specified must be exercised by at least one test in this plan. Specifically:

1. Start with `math.py` + `models.py` (pure, testable, property-friendly).
2. Add `pricing/` catalog + snapshots.
3. Add `providers/` with at least `fake.py` + `anthropic.py` + enough goldens to make `test_anthropic_golden` green.
4. Add `storage/` with SQLAlchemy models and repository.
5. Add `tracker.py` tying everything together.
6. Add `events.py` + `reconciliation.py` + `telemetry.py` + `aggregator.py`.

**Constraint:** Amelia must not ship a public function without at least one test that calls it in both success and failure modes. If a function has no failure mode, that should be noted explicitly in a comment on the test.

**Amelia → Quinn handoff:** When all unit + property + golden tests are green in Amelia's sandbox, Quinn takes over for the full CI integration and the stress/reconciliation layers.

---

## 15. HANDOFF TO QUINN

**Quinn:** Your job is execution and coverage.

1. Wire the CI pipeline per §11.
2. Run the full stress + reconciliation suites nightly.
3. Maintain the golden fixtures as provider SDKs update.
4. Own the coverage dashboard for this module — enforce gates per §11.2.

Any uncovered branch that is not on the explicit "hard to cover" list in §9.6 must be justified or tested. Gaps are tracked as issues.

---

## 16. HANDOFF TO WINSTON

**Back to Winston:** If any test in §3–§8 turns red in a way that suggests a design flaw rather than a bug, return to §6 or §3 of the architecture doc and reconcile. Tests that fail because the architecture is wrong are a signal, not a nuisance.

**Open questions for Winston from this strategy:**
- §3.6 P4 — tolerance of `4 * QUANTUM` — is this exactly right or should we use a tighter bound like `max(1 quantum, k * single_precision)`? (My proposal: keep 4 * QUANTUM; a tighter bound risks false flakes at scale.)
- §9.1 manual reconciliation — do we have access to a real historical invoice? Andrey to confirm.

**Design is testable. Strategy is approved for Amelia.**

— Murat
