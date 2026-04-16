# Praxis Compression Layer — Test Strategy

**Module:** `praxis.kernel.compression`
**Stage:** Praxis Stage 2, Step 2.2 (Token Compression Quick Wins)
**Author:** Murat (Test Architect)
**Date:** 2026-04-12
**Status:** Approved for Amelia implementation + Quinn execution
**Version:** 1.0
**Risk class:** Orchestrator severity 4.15 (highest per Matrix 6), Caveman severity 3.60, Forge 2.90, TONL 2.85, RTK 1.85
**Depends on:**
- `compression/architecture.md` v0.2 (Winston, Stage 2.1 post-elicitation)
- `compression/requirements-validation.md` (Elicitation Round 1, Stage 2.1.5)
- `pi-mono/test-strategy.md` (Stage 1 convention source)
- Default assumption from Round 1 §5.1: **Caveman ships P0 behind `compression.caveman.enabled` feature flag (default OFF)**

---

## 0. EXECUTIVE SUMMARY

Winston's architecture has been hardened by Elicitation Round 1 — 16 edits applied across FMEA findings and comparative matrix scoring. My job is to convert that hardened surface into a test plan where **every claim the architecture makes is either structurally impossible to violate or caught by a test that fails red when the invariant slips**. The FMEA surfaced ten compression risks (CM1–CM10); Matrix 6 ranked the five components by severity. This strategy uses both as the source of priority.

The test pyramid follows Stage 1's convention with compression-specific additions:

```
            ┌──────────────────────────────────┐
            │  A/B Harness + Reconciliation    │   5%  — nightly cron
            ├──────────────────────────────────┤
            │  Cross-platform + Chaos          │  10%  — CI per PR + nightly
            ├──────────────────────────────────┤
            │  Integration (11 enumerated)     │  15%  — CI per PR
            ├──────────────────────────────────┤
            │  Adversarial corpus              │  10%  — CI per PR (Caveman)
            ├──────────────────────────────────┤
            │  Golden fixtures                 │  10%  — CI per PR
            ├──────────────────────────────────┤
            │  Property-based (Hypothesis)     │  25%  — CI per PR, fast
            ├──────────────────────────────────┤
            │  Unit (pytest)                   │  25%  — CI per commit
            └──────────────────────────────────┘
```

The two bands that are new versus Stage 1:
- **Adversarial corpus (10%).** Caveman semantic validators S3 and S4 exist specifically to catch drift patterns that fooled the earlier S1/S2-only design (FMEA V.2, V.3). They cannot be validated with property tests alone because the attacks are *patterns a clever LLM could produce*, not random inputs. An adversarial corpus is non-negotiable.
- **Cross-platform (shared band).** RTK is a vendored Rust binary. The cross-platform binary verification matrix has to run as part of CI because Amelia's machine cannot catch "binary missing on Linux arm64". This is a Stage-2-specific investment.

### 0.1 Coverage gates per module

Coverage targets are driven by risk + Matrix 6 severity, not by a flat percentage.

| Module | Coverage gate | Matrix 6 rank | Why |
|--------|---------------|:---:|-----|
| `compression/__init__.py` + `orchestrator.py` | **100%** line + branch | **1 (4.15)** | Cascade isolation. Uncovered branches are uncaught cascades. |
| `caveman/validate.py` (S1-S4) | **100%** line + branch | **2 (3.60)** | Every validator branch is a potential silent drift. |
| `caveman/compressor.py`, `caveman/gate.py` | **≥95%** line, 90% branch | 2 | Gate decision logic + Haiku fallback paths. |
| `forge/compactor.py`, `forge/strategy.py`, `forge/reasoning.py` | **≥95%** line, 90% branch | **3 (2.90)** | Compaction determinism + reasoning preservation. |
| `forge/transformers.py` | **100%** line | 3 | Stateless filters — trivially achievable. |
| `tonl/encode.py`, `tonl/decode.py` | **≥95%** line, 90% branch | **4 (2.85)** | Round-trip invariant plus security limits. |
| `tonl/tokenizers/*` | **≥90%** line | 4 | Real SDK fallbacks complicate full coverage; golden fixtures close the gap. |
| `tonl/security.py`, `tonl/errors.py` | **100%** line | 4 | Guards must be reachable by tests. |
| `rtk/client.py`, `rtk/resolver.py` | **≥85%** line | **5 (1.85)** | Subprocess boundary; full coverage is impractical without a binary on each platform. |
| `rtk/telemetry.py` | **≥90%** line | 5 | JSON parser must handle all RTK version outputs we pin. |
| `harness/*` | **≥85%** line | — | Harness is test infrastructure itself; reasonable coverage suffices. |

**Aggregate target per R13:** ≥85% module-wide. Any PR dropping below a module gate fails the build. `coverage.py` with `--branch` is the measurement tool; the gate runs as a final CI step after the test suite.

### 0.2 What this strategy does NOT cover

Scoped out explicitly:
- Production monitoring and dashboards (those live with Stage 7 POV harness)
- Pi-Mono internals (covered by Stage 1 test strategy; Stage 2 only validates integration contracts)
- Agent Runtime integration (Stage 4 concern)
- MAC engine 3-cycle behavior (Stage 5 concern)
- LLM model behavior — we mock Haiku in unit tests and use real Haiku only in gated nightly tests (to cap cost)

---

## 1. RISK REGISTER (SOURCE OF PRIORITY)

Every test in this plan anchors to a compression risk (CM-series) or an architectural invariant Winston declared. If a test does not map to one, it is not worth writing.

**Scoring:** Probability × Impact on 1–3 each; total 1–9. Score ≥6 requires explicit mitigation; score = 9 blocks the gate.

| ID | Risk | P | I | Score | Action | Matrix 6 component | Primary test layer | Secondary |
|----|------|:-:|:-:|:-:|--------|-------------------|-------------------|-----------|
| **CM5** | Caveman semantic polarity flip / antonym swap (FMEA V.2, V.3) | 3 | 3 | **9** | **BLOCK** | Caveman (2) | Adversarial corpus + Hypothesis P_V3/P_V4 | Integration #4 |
| **CM2** | Forge reasoning chain break (schema drift or non-overwrite) | 2 | 3 | 6 | MITIGATE | Forge (3) | Property P_F5/P_F5b/P_F6 | Integration #2 |
| **CM4** | Caveman corrupts code in mixed content | 2 | 3 | 6 | MITIGATE | Caveman (2) | Golden fixtures + Hypothesis P_V1 | Integration #4 |
| **CM9** | Cascade failure across layers (orchestrator fail-safe leak) | 2 | 3 | 6 | MITIGATE | **Orchestrator (1)** | Chaos integration #5 (enumerated 6 rows) | Unit |
| **CM10** | Tokenizer version drift (silent encode/decode mismatch) | 2 | 3 | 6 | MITIGATE | TONL (4) | Property P_T1 + version pinning test | Integration #1 |
| **CM6** | Caveman cost > savings (net-negative) | 2 | 2 | 4 | MONITOR | Caveman (2) | Integration #10 (prediction feedback) + A/B harness | Gate unit tests |
| **CM1** | TONL lossy round-trip | 1 | 3 | 3 | DOCUMENT | TONL (4) | Property P_T1 (Hypothesis, 10K cases) | Golden fixtures |
| **CM3** | Forge drops tool_use without tool_result | 1 | 3 | 3 | DOCUMENT | Forge (3) | Property P_F3 (fuzz pair interleaving) | Unit edge cases |
| **CM7** | RTK binary crash / timeout | 1 | 2 | 2 | DOCUMENT | RTK (5) | Integration #3 + subprocess unit tests | — |
| **CM8** | RTK telemetry race (concurrent attribution drift) | 3 | 1 | 3 | DOCUMENT | RTK (5) | Stress test with asyncio.gather | Integration #7 (orphan) |

### 1.1 Orchestrator-level risks surfaced by Murat (NOT in the FMEA CM-series)

These are Murat additions, not in the FMEA findings:

| ID | Risk | P | I | Score | Action | Rationale |
|----|------|:-:|:-:|:-:|--------|-----------|
| **CM11** | Tag budget silent truncation when 28-cap hit | 2 | 2 | 4 | MONITOR | §4.1 has the cap + priority drop order, but no test exists yet that forces the drop path. Integration #11 closes it. |
| **CM12** | A/B harness config drift between on/off arms | 2 | 3 | 6 | MITIGATE | §6.3 pinning + config_hash added post-FMEA. Integration #8 validates. |
| **CM13** | Caveman gate calibration staleness | 2 | 2 | 4 | MONITOR | §3.4.3 guard added post-FMEA. Integration #9 validates. |
| **CM14** | Caveman prediction feedback loop drift | 2 | 2 | 4 | MONITOR | §3.4.3 ground-truth loop added post-FMEA. Integration #10 validates. |
| **CM15** | Reconciliation round-trip drift (tag encoding or aggregation bug) | 2 | 3 | 6 | MITIGATE | §9.4 #6 from architecture — tightened to 0.5% drift threshold by Matrix 5. |

**The top-scoring risk is CM5 (Caveman polarity flip) at 9 — BLOCK.** This risk is structurally the single most dangerous failure in the whole compression layer. It gets the most test budget. Three other risks score 6 (CM2, CM4, CM9, CM10, CM12, CM15) and dominate the mitigation workload. Everything at ≤4 is covered but not over-invested.

### 1.2 Priority mapping

Per the P0-P3 convention:

| Priority | Risk score | Components | Coverage gate |
|:---:|:---:|-----------|---------------|
| **P0** | 9 | Caveman semantic validators (CM5) | 100% line + branch; adversarial corpus non-negotiable |
| **P1** | 6-8 | Orchestrator cascade (CM9), Forge reasoning (CM2), Caveman code corruption (CM4), TONL drift (CM10), A/B harness fairness (CM12), reconciliation (CM15) | ≥95% line, 90% branch |
| **P2** | 4-5 | Caveman cost guard (CM6), gate calibration (CM13), feedback loop (CM14), tag budget (CM11) | ≥85% line |
| **P3** | 1-3 | TONL round-trip edge (CM1), Forge tool pair (CM3), RTK crash (CM7), telemetry race (CM8) | Best effort |

---

## 2. TEST ORGANIZATION

### 2.1 Directory layout (mirrors Winston's module structure)

```
praxis/kernel/compression/
└── tests/
    ├── conftest.py                 # Shared fixtures: mock Haiku, synthetic conversation,
    │                                # tokenizer stubs, orphan clock, RTK binary resolver
    │
    ├── unit/
    │   ├── tonl/
    │   │   ├── test_encode.py
    │   │   ├── test_decode.py
    │   │   ├── test_schema_inference.py
    │   │   ├── test_security_limits.py
    │   │   ├── test_document.py
    │   │   └── test_tokenizers.py              # With SDK mocks
    │   ├── forge/
    │   │   ├── test_strategy.py                # evict/retain bounds
    │   │   ├── test_triggers.py                # three-threshold logic
    │   │   ├── test_transformers.py            # DropRole, DedupeRole, etc.
    │   │   ├── test_reasoning_schema.py        # Known schema registry
    │   │   └── test_compactor_unit.py          # Stateless pieces
    │   ├── caveman/
    │   │   ├── test_validate_structural.py     # H1-H5
    │   │   ├── test_validate_semantic.py       # S1-S4, exhaustive
    │   │   ├── test_gate.py                    # All gate paths
    │   │   ├── test_boundary.py                # Content classification
    │   │   └── test_dialects.py                # Prompt templates + wenyan gate
    │   ├── rtk/
    │   │   ├── test_resolver.py                # Platform → binary path
    │   │   ├── test_telemetry_parser.py        # `rtk gain --format json` parse
    │   │   └── test_client_subprocess.py       # Uses a fake subprocess fixture
    │   └── orchestrator/
    │       ├── test_pipeline_order.py          # §2.1 diagram order
    │       ├── test_fallback_tags.py           # Tag attribution on fallback
    │       └── test_tag_budget.py              # 28-cap + drop order
    │
    ├── property/
    │   ├── test_tonl_properties.py             # P_T1, P_T2, P_T3
    │   ├── test_forge_properties.py            # P_F1-P_F6 + P_F5b
    │   ├── test_caveman_properties.py          # P_V1-P_V7
    │   ├── test_rtk_properties.py              # P_R1-P_R2
    │   └── test_orchestrator_properties.py     # Cascade idempotency
    │
    ├── golden/
    │   ├── fixtures/
    │   │   ├── tonl/                           # Encoded examples per tokenizer
    │   │   ├── forge/                          # Conversations with reasoning / tool chains
    │   │   ├── caveman/                        # Prose with embedded code / markup
    │   │   └── rtk/                            # Raw command output → filtered
    │   ├── test_tonl_golden.py
    │   ├── test_forge_golden.py
    │   ├── test_caveman_golden.py
    │   ├── test_rtk_golden.py
    │   └── update_golden.py                    # Regeneration tool
    │
    ├── adversarial/
    │   ├── corpus/                             # Hand-curated AND generator-produced
    │   │   ├── polarity_flips/                 # S3-targeting: safe→unsafe, allow→deny
    │   │   ├── imperative_inversions/          # S4-targeting: do X → don't X
    │   │   ├── negation_drift/                 # S1-bypassing: simultaneous add+drop
    │   │   ├── number_loss/                    # S2-targeting: silent numeric drop
    │   │   ├── code_in_prose/                  # H2-targeting: boundary confusion
    │   │   └── README.md                       # Schema + curation process
    │   ├── test_caveman_adversarial.py         # Runs the full corpus through validators
    │   ├── test_caveman_generator.py           # Hypothesis-generated adversarial inputs
    │   └── labeling_tool.py                    # Human-labeling helper
    │
    ├── integration/
    │   ├── test_01_end_to_end_pipeline.py      # Real Haiku call; gated nightly
    │   ├── test_02_forge_bmad_replay.py        # Tokonomics Round 4 session replay
    │   ├── test_03_rtk_real_shell.py           # git log / docker ps / pytest
    │   ├── test_04_caveman_gate_decisions.py   # 20 synthetic prose inputs
    │   ├── test_05_chaos_cascade_isolation.py  # Iterates §5.2 6-row table
    │   ├── test_06_reconciliation_roundtrip.py # Pi-Mono tag aggregation vs harness
    │   ├── test_07_rtk_orphan_attribution.py   # 60s timeout bucket
    │   ├── test_08_ab_harness_config_drift.py  # HarnessConfigDriftError path
    │   ├── test_09_gate_calibration_stale.py   # 7-day staleness denial
    │   ├── test_10_gate_prediction_feedback.py # 30-run simulation → auto-raise
    │   └── test_11_tag_budget_overflow.py      # 20 non-compression tags → drops
    │
    ├── cross_platform/
    │   ├── test_rtk_linux_x64.py
    │   ├── test_rtk_linux_arm64.py              # Skipped if not on ARM CI
    │   ├── test_rtk_darwin_x64.py
    │   ├── test_rtk_darwin_arm64.py
    │   ├── test_rtk_windows_x64.py
    │   └── test_binary_version_pin.py           # Asserts --version matches RTK_PINNED_VERSION
    │
    ├── stress/
    │   ├── test_concurrent_rtk.py               # Telemetry race + orphan attribution drift
    │   ├── test_tonl_streaming_memory.py        # O(1) memory target on 1M objects
    │   └── test_forge_long_conversation.py     # 10,000-message synthetic conversation
    │
    ├── harness/
    │   ├── test_harness_seed_pinning.py
    │   ├── test_harness_config_hash.py
    │   ├── test_harness_report_format.py
    │   └── test_harness_db_schema.py
    │
    └── static/
        ├── test_no_float_in_tonl.py             # AST scan mirroring Stage 1
        ├── test_no_llm_calls_in_forge.py        # AST scan: assert no `anthropic.` / `openai.` imports in forge/
        ├── test_tag_namespace_discipline.py     # All compression tags start with `compression.`
        └── test_dependency_direction.py         # No circular imports; strict layer order
```

### 2.2 Test dependencies and ordering

Unit → property → golden → adversarial → integration → cross-platform → stress → harness → static. Each layer depends on the previous in the sense that its failure points to work remaining at a lower layer. CI runs them in the same order; the suite stops at the first broken layer to surface the lowest-level problem first.

### 2.3 Test identifiers

`{EPIC}.{STAGE}.{STORY}-{LEVEL}-{SEQ}`

Examples:
- `PRAXIS.S2.COMP-UNIT-001` — Caveman S1 negation validator unit test
- `PRAXIS.S2.COMP-PROP-P_V3` — Caveman polarity flip property test
- `PRAXIS.S2.COMP-INT-005` — Chaos cascade isolation integration test
- `PRAXIS.S2.COMP-XPF-LX64-RTK` — RTK on Linux x64 cross-platform test

---

## 3. PROPERTY-BASED TEST PLAN (HYPOTHESIS)

Winston's §9.2 enumerated 18 property tests. This section turns each into a concrete Hypothesis target with strategies, invariants, and acceptance criteria. Every test has a `@hypothesis.given` decorator, a `@settings(max_examples=N)` budget proportional to risk, and an assertion that binds back to a CM risk or an architectural invariant.

### 3.1 TONL properties (P_T1–P_T3)

**`P_T1. encode/decode round-trip`** — bound to CM1.

```
@given(payload=valid_pydantic_payloads())
@settings(max_examples=5000, deadline=None)
def test_round_trip(payload):
    encoded = tonl.encode(payload, tokenizer="claude-opus-4-6@2026-04-12")
    decoded = tonl.decode(encoded)
    assert decoded == payload
```

Hypothesis strategies:
- `valid_pydantic_payloads()` composes: `st.dictionaries`, `st.lists`, `st.integers(min=-1e18, max=1e18)`, `st.text(alphabet=printable, min=0, max=2048)`, `st.decimals(min="0", max="1e12", places=10, allow_nan=False)`, `st.booleans`, `st.none`
- Explicitly excludes `st.floats` (per Stage 1 R7) and `st.sampled_from([set(), map(), custom_class()])` (documented as encoder-rejection territory)

Acceptance: 0 Hypothesis counter-examples after 5000 cases. Counter-example is a blocker bug.

**`P_T2. Security limit enforcement`** — bound to architectural invariant in §3.1.5 (limits).

```
@given(payload=oversize_payloads())
def test_security_limits_raise(payload):
    with pytest.raises(TONLSecurityError):
        tonl.encode(payload)
```

Strategies generate payloads at or above each limit (nesting > 500, line length > 100 KB, fields > 10 K). Asserts typed exception, no silent truncation.

**`P_T3. Streaming equivalence`** — bound to R11 (O(1) memory).

```
@given(items=lists_of_payloads(min_size=1, max_size=1000))
async def test_streaming_equivalence(items):
    batch = tonl.encode(items)
    streamed = [chunk async for chunk in tonl.encode_stream(async_iter(items))]
    assert "".join(streamed) == batch
```

Plus a memory probe: use `tracemalloc` to assert peak memory is `O(1)` with respect to input size (measured as ratio peak_per_item ≤ 2× baseline).

### 3.2 Forge properties (P_F1–P_F6 + P_F5b)

**`P_F1. Idempotency`** — bound to architectural invariant F-C6.

```
@given(conv=synthetic_conversations())
def test_compact_idempotent(conv):
    once = compactor.compact(conv)
    twice = compactor.compact(once)
    assert once == twice
```

**`P_F2. Retention`** — bound to F2.

```
@given(conv=synthetic_conversations(min_messages=20))
def test_last_n_retained(conv):
    config = CompactionConfig(retention_window=6, ...)
    result = compactor.compact(conv, config)
    if result.compacted:
        assert result.messages[-6:] == conv.messages[-6:]  # Identity equality
```

**`P_F3. Tool pair preservation`** — bound to CM3.

```
@given(conv=conversations_with_tool_chains())
def test_tool_pair_not_split(conv):
    result = compactor.compact(conv)
    # Walk result, assert no tool_use is followed immediately by a non-tool_result
    for i, msg in enumerate(result.messages[:-1]):
        if has_tool_use(msg):
            assert has_tool_result(result.messages[i+1])
```

Hypothesis strategy `conversations_with_tool_chains()` intentionally generates adversarial patterns: tool_use at end of compacted range, nested tool chains, interleaved tool results. Run 3000 examples.

**`P_F4. Zero LLM calls`** — bound to CM9 (zero-cost invariant).

```
def test_compaction_makes_no_llm_calls():
    mock_provider = MagicMock()
    with patch("praxis.kernel.compression.forge.provider", mock_provider):
        for _ in range(100):
            conv = generate_random_conversation()
            compactor.compact(conv)
        assert mock_provider.call_count == 0
```

Runs 100 random compactions against a MagicMock that fails the test if called. Complementary static test in `static/test_no_llm_calls_in_forge.py` scans imports.

**`P_F5. Reasoning preservation, positive case`** — bound to F8.

```
@given(conv=conversations_with_reasoning_in_compacted_range(first_post_has_reasoning=False))
def test_reasoning_injected_when_missing(conv):
    result = compactor.compact(conv)
    if result.compacted and result.reasoning_preserved:
        first_post = first_assistant_after_boundary(result)
        assert first_post.reasoning_details is not None
        assert first_post.reasoning_details == last_reasoning_in_range(conv, result.range)
```

**`P_F5b. Reasoning non-overwrite`** — bound to CM2 / FMEA F.6. Critical new property post-elicitation.

```
@given(conv=conversations_with_reasoning_in_compacted_range(first_post_has_reasoning=True))
def test_reasoning_not_overwritten(conv):
    original_first_post_reasoning = first_assistant_after_boundary(conv).reasoning_details
    result = compactor.compact(conv)
    first_post = first_assistant_after_boundary(result)
    # The post-boundary message's reasoning must be identity-equal to its pre-compaction reasoning.
    assert first_post.reasoning_details == original_first_post_reasoning
```

**`P_F6. Reasoning schema drift detection`** — bound to CM2 / FMEA F.2.

```
@given(schema_version=st.text(min_size=3, max_size=40).filter(lambda v: v not in KNOWN_REASONING_SCHEMAS))
def test_unknown_schema_alerts_and_falls_back(schema_version, alerts_captured):
    conv = conversation_with_reasoning_schema(schema_version)
    result = compactor.compact(conv)
    assert result.reasoning_preserved is False
    assert result.reasoning_drift_detected is True
    assert any(a.name == "forge.reasoning.unknown_schema" and a.version == schema_version
               for a in alerts_captured)
    # Exactly one alert per unknown schema instance
    assert sum(1 for a in alerts_captured if a.name == "forge.reasoning.unknown_schema") == 1
```

### 3.3 Caveman properties (P_V1–P_V7)

Caveman properties are the single highest-priority family. Test budget is 3× the Forge budget. Hypothesis settings: `max_examples=3000` each.

**`P_V1. Structural validator roundtrip`** — bound to CM4.

```
@given(prose=prose_with_markup())
def test_structural_validator_catches_corruption(prose):
    corrupted = randomly_break_structure(prose)
    errors = validate_structural(prose, corrupted)
    assert len(errors) > 0  # At least one structural error detected
```

Strategy `randomly_break_structure` mutates in ways the validator should catch: remove a heading, corrupt a code fence, drop a URL, change a path. Inverse test asserts `validate_structural(prose, prose) == []`.

**`P_V2. Semantic validator negation count`** — bound to CM5 (coarse level).

Already in §9.2 as the S1 check. Run 3000 cases with negation-heavy sentences.

**`P_V3. Semantic validator polarity flip`** — bound to CM5, the RPN-9 risk.

```
@given(positive=st.sampled_from(POLARITY_POSITIVES),
       negative=st.sampled_from(POLARITY_NEGATIVES),
       context=surrounding_prose())
def test_polarity_flip_detected(positive, negative, context):
    # Pair must be in the lexicon
    assume((positive, negative) in POLARITY_PAIRS or (negative, positive) in POLARITY_PAIRS)

    original = f"{context} {positive} {context}"
    flipped = f"{context} {negative} {context}"
    errors = validate_semantic(original, flipped)
    assert any(e.code == "polarity_flip" for e in errors)
```

Plus a negative control: `@given(prose)` where compression preserves polarity, assert `not any(e.code == "polarity_flip")`. False positive rate must be < 2% on the negative corpus.

**`P_V4. Semantic validator imperative inversion`** — bound to CM5.

```
@given(positive_verb=st.sampled_from(IMPERATIVE_POSITIVE),
       negative_verb=st.sampled_from(IMPERATIVE_NEGATIVE),
       object_text=st.text(min_size=1, max_size=40, alphabet=printable_no_punctuation))
def test_imperative_inversion_detected(positive_verb, negative_verb, object_text):
    original = f"{positive_verb} {object_text}"
    inverted = f"{negative_verb} {object_text}"
    errors = validate_semantic(original, inverted)
    assert any(e.code == "imperative_drift" for e in errors)
```

**`P_V5. Gate below floor blocks`** — bound to architectural invariant §3.4.3.

```
@given(text=st.text(max_size=499))  # Intentionally below min_tokens=500
def test_below_floor_always_denies(text):
    req = CompressionRequest(text=text, intensity=Intensity.FULL, ...)
    passed, reason = should_compress(req, default_config, fresh_calibration)
    assert passed is False
    assert reason == "below_min_length"
```

**`P_V6. Calibration staleness blocks`** — bound to CM13 / FMEA V.4.

```
@given(age_seconds=st.integers(min_value=604801, max_value=100*86400))  # > 7 days
def test_stale_calibration_denies(age_seconds):
    stale = CalibrationSnapshot(refreshed_at=now() - timedelta(seconds=age_seconds), ...)
    req = valid_caveman_request()
    passed, reason = should_compress(req, default_config, stale)
    assert passed is False
    assert reason == "calibration_stale"
```

**`P_V7. Prediction feedback raises break_even`** — bound to CM14 / FMEA V.5.

```
def test_prediction_feedback_raises_break_even():
    calibration = CalibrationSnapshot(break_even_reads=3, ...)
    # Simulate 30 runs where actual_reads is half of expected
    for _ in range(30):
        calibration.record_observation(expected=5, actual=2)
    calibration.run_nightly_adjustment()
    assert calibration.break_even_reads > 3
    assert calibration.last_adjustment_reason == "prediction_error_median_exceeded"
```

Not a Hypothesis property (deterministic), but sits in the property file as a "simulation property" — the post-condition is the focus.

### 3.4 RTK properties (P_R1–P_R2)

**`P_R1. Subprocess budget`** — bound to R10 (<10ms RTK envelope).

```
def test_rtk_startup_budget():
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        _ = subprocess.run([RTK_BIN, "--version"], capture_output=True)
        timings.append(time.perf_counter() - start)
    median = statistics.median(timings)
    p95 = statistics.quantiles(timings, n=20)[18]
    assert median < 0.2  # 200ms generous budget incl. IPC
    assert p95 < 0.5
```

Gated behind `@pytest.mark.skipif(not binary_available())` so CI on platforms without a vendored binary don't fail.

**`P_R2. Binary resolution`** — bound to CM7.

```
def test_resolve_binary_for_current_platform():
    path = resolve_binary_path()
    assert path.exists()
    assert os.access(path, os.X_OK)
```

### 3.5 Orchestrator properties

Not in Winston's original §9.2, but added by Murat as a consequence of Matrix 6 ranking Orchestrator highest.

**`P_O1. Pipeline order idempotency`** — bound to architectural invariant §2.1.

```
@given(payload=valid_payloads())
async def test_pipeline_order_stable(payload):
    result_1 = await layer.encode_request(payload, session)
    result_2 = await layer.encode_request(payload, session_clone)
    assert result_1 == result_2  # Same input → same output, deterministic
```

**`P_O2. Fallback tag attribution`** — bound to architectural invariant §5.2.

```
@given(failing_component=st.sampled_from(["tonl", "forge", "caveman", "rtk"]))
async def test_fallback_tag_matches_failure(failing_component, force_fail):
    with force_fail(failing_component):
        request = await layer.encode_request(sample_payload(), session)
    assert request.tags.get("compression.fallback", "").startswith(failing_component)
```

---

## 4. GOLDEN FIXTURE STRATEGY

Property tests catch logic errors. Golden files catch regression against **actual payloads** and **actual provider outputs**.

### 4.1 TONL golden fixtures

```
tests/golden/fixtures/tonl/
├── uniform_array_claude_opus_4_6.json        # input
├── uniform_array_claude_opus_4_6.tonl        # expected encoded
├── uniform_array_gpt_5.json
├── uniform_array_gpt_5.tonl
├── uniform_array_gemini_3_1.json
├── uniform_array_gemini_3_1.tonl
├── mixed_scalar_nested.json
├── mixed_scalar_nested.tonl
├── unicode_heavy.json                         # BMP + supplementary plane
├── unicode_heavy.tonl
├── decimal_precision.json                     # Decimal("1.0000000001") preservation
├── decimal_precision.tonl
├── streaming_100k_objects.jsonl
└── streaming_100k_objects.tonl                # For O(1) streaming test
```

Each pair runs through `test_tonl_golden.py`:
```python
def test_golden_encode(input_file, expected_file, tokenizer):
    data = json.loads(input_file.read_text())
    encoded = tonl.encode(data, tokenizer=tokenizer)
    expected = expected_file.read_text()
    assert encoded == expected, f"TONL encoding drift on {input_file.name}"
```

Regeneration tool `update_golden.py` takes a `--confirm` flag; any PR modifying fixtures without running the tool is rejected.

### 4.2 Forge golden fixtures

```
tests/golden/fixtures/forge/
├── reasoning_chain_preserved/
│   ├── input.json                              # Conversation with reasoning blocks
│   ├── expected_compacted.json                 # After compaction
│   └── README.md                               # What this case exercises
├── tool_chain_walkback/
│   ├── input.json                              # Long tool_use chain
│   └── expected_compacted.json                 # Chain kept intact or returns no-op
├── trigger_by_tokens/
│   ├── input.json                              # Crosses token_threshold only
│   └── expected_compacted.json
├── trigger_by_turns/
│   └── ...
├── trigger_by_messages/
│   └── ...
└── first_post_already_has_reasoning/           # Non-overwrite case (P_F5b)
    ├── input.json
    └── expected_compacted.json                  # Original reasoning preserved
```

### 4.3 Caveman golden fixtures

```
tests/golden/fixtures/caveman/
├── prose_only_full.md                           # Expected-compressed at intensity=full
├── prose_only_full.compressed.md
├── prose_only_ultra.compressed.md
├── prose_with_embedded_code.md
├── prose_with_embedded_code.compressed.md      # Code block byte-exact
├── prose_with_inline_code.md
├── prose_with_yaml_block.md
├── prose_with_sql_block.md
├── negation_heavy.md                            # S1 sensitivity
├── number_heavy.md                              # S2 sensitivity
├── polarity_sensitive.md                        # S3 sensitivity
└── imperative_sensitive.md                      # S4 sensitivity
```

### 4.4 RTK golden fixtures

```
tests/golden/fixtures/rtk/
├── git_log_20_commits.raw.txt                   # Raw command output
├── git_log_20_commits.filtered.txt              # Expected RTK output
├── docker_ps_running.raw.txt
├── docker_ps_running.filtered.txt
├── pytest_collect_only.raw.txt
├── pytest_collect_only.filtered.txt
├── npm_install_verbose.raw.txt                  # With --verbose
├── npm_install_verbose.filtered.txt             # Should be less compressed
└── telemetry_gain_output_v0_35.json             # rtk gain --format json sample
```

---

## 5. ADVERSARIAL CORPUS — CAVEMAN S3/S4

The adversarial corpus is the most important test investment in the whole strategy because CM5 is the only RPN-9 risk. Property tests generate *random* adversarial inputs; the corpus contains *chosen* adversarial inputs that mirror actual attack patterns.

### 5.1 Corpus structure

```
tests/adversarial/corpus/
├── polarity_flips/
│   ├── 001_safe_to_unsafe.yaml                  # Input + expected validator output
│   ├── 002_allow_to_deny.yaml
│   ├── 003_recommended_to_discouraged.yaml
│   ├── 004_enable_to_disable.yaml
│   ├── 005_required_to_optional.yaml
│   ├── ... (20 cases, one per pair × both directions)
│   └── INDEX.yaml                               # Pair → case file mapping
├── imperative_inversions/
│   ├── 001_do_use_to_dont_use.yaml
│   ├── 002_run_to_avoid.yaml
│   ├── 003_include_to_exclude.yaml
│   ├── ... (15 cases)
│   └── INDEX.yaml
├── negation_drift/
│   ├── 001_add_one_drop_one.yaml                # S1 bypass via token count preservation
│   ├── 002_double_negative_collapse.yaml        # "not impossible" → "possible"
│   └── INDEX.yaml
├── number_loss/
│   ├── 001_silent_dollar_drop.yaml
│   ├── 002_percentage_loss.yaml
│   └── INDEX.yaml
├── code_in_prose/
│   ├── 001_json_payload_corrupted.yaml
│   ├── 002_yaml_indent_drift.yaml
│   ├── 003_sql_injection_risk.yaml              # A meta-case: compression introduces SQLi
│   ├── 004_path_separator_lost.yaml
│   └── INDEX.yaml
└── README.md                                     # Curation process + reviewer roles
```

Each YAML case has this shape:

```yaml
id: polarity_flips_001
description: "safe → unsafe single-token flip"
category: polarity_flip
severity: S1
original: |
  The library is safe for concurrent access.
compressed_expected_failing: |
  The library is unsafe for concurrent access.
validator_expected_error:
  code: polarity_flip
  pair: [safe, unsafe]
  orig_bias: 1
  comp_bias: -1
```

### 5.2 Curation protocol

- **Minimum 60 hand-curated cases at Stage 2 launch.** 20 polarity, 15 imperative, 10 negation drift, 5 number loss, 10 code-in-prose.
- **Every new production fallback event** that maps to a validator bypass becomes a new corpus entry the same day.
- **Quarterly review:** all corpus cases must still trigger the validator; any regression is a release blocker.
- **Labeler:** Murat first, then anyone with git commit access to the compression module. Two reviewers required per case.

### 5.3 Adversarial test runner

```python
def test_polarity_corpus_covered_by_S3(corpus_loader):
    for case in corpus_loader.load("polarity_flips"):
        errors = validate_semantic(case.original, case.compressed_expected_failing)
        matching = [e for e in errors if e.code == "polarity_flip"]
        assert matching, f"S3 missed {case.id}: {case.description}"
        if case.validator_expected_error:
            exp = case.validator_expected_error
            assert matching[0].pair == exp["pair"]
```

Identical runners for `imperative_inversions`, `negation_drift`, `number_loss`, `code_in_prose`.

### 5.4 Generator-produced adversarial inputs

Complements the hand-curated corpus. Uses Hypothesis to synthesize adversarial sentences within each category. Acceptance criterion: 0 validator misses across 1000 generated cases per category. Any miss is either (a) a validator bug we fix or (b) an insufficiently-specified generator we tighten.

### 5.5 Coverage gate for the adversarial layer

- **Polarity:** S3 catches 100% of corpus and ≥95% of generator cases (5% tolerance for pair-not-in-lexicon edge cases that Stage 3 embedding will cover)
- **Imperative:** S4 catches 100% of corpus and ≥90% of generator cases
- **Negation drift:** S1 catches 100% of corpus; S1-bypassing cases are caught by S3/S4 as a backup
- **Number loss:** S2 catches 100% of corpus
- **Code in prose:** H2 catches 100% of corpus

Any gate drop triggers a BLOCK — no Stage 2 gets released with a regressing corpus.

---

## 6. INTEGRATION TEST PLAN — THE ELEVEN TESTS

Winston enumerated 11 integration tests in architecture §9.4. This section turns each into a concrete test spec with fixtures, mocks, and acceptance criteria.

### 6.1 `test_01_end_to_end_pipeline` (gated nightly)

**Goal:** Full pipeline (TONL → Forge → Caveman → RTK) on a real workload. Real Haiku call.

- **Mode:** Real provider, gated behind `@pytest.mark.nightly`. Cost cap: $0.10 per run enforced by Pi-Mono pre-check.
- **Input:** 3 synthetic workloads from `tests/workloads/` (short prose, mixed prose+code, long numeric report).
- **Assertions:**
  - Token delta > 0 (compression actually happened)
  - All validators passed (`result.fallback is None`)
  - Pi-Mono records carry the expected compression.* tags
  - Real-Haiku cost for Caveman is < 20% of the savings it produced (net-positive)

### 6.2 `test_02_forge_bmad_replay`

**Goal:** Forge compaction fires correctly on a real BMAD session replay.

- **Input:** Tokonomics Round 4 session JSON at `tests/fixtures/bmad_sessions/tokonomics_r4.json`.
- **Assertions:**
  - Forge trigger fires exactly at the expected message count (derived from session: ~42 messages)
  - Retention window of 6 preserved
  - All tool pairs intact after compaction
  - Reasoning chain preserved (the session has at least one `thinking` block)
  - `result.tokens_saved > 0`

### 6.3 `test_03_rtk_real_shell`

**Goal:** RTK wrapper works against actual shell commands.

- **Mode:** Integration; skipped if RTK binary not available on test platform.
- **Commands run:**
  - `git log -20` (requires a git repo — use `tests/fixtures/fake_repo/`)
  - `docker ps` (mocked with `--format '{{.ID}}'` fixture; real docker optional)
  - `pytest --collect-only` (runs against `tests/smoke/`)
- **Assertions:**
  - Filtered output matches golden fixture byte-for-byte
  - Exit code preserved from the original command
  - `bytes_saved > 0`
  - `compression.rtk.bytes_saved_prior` tag attached to synthetic next LLMRequest

### 6.4 `test_04_caveman_gate_decisions`

**Goal:** Gate decisions match calibrated break-even for 20 synthetic inputs.

- **Input:** 20 fixtures in `tests/fixtures/caveman_gate/` with varying:
  - `expected_downstream_reads` (1 to 10)
  - `text_length_tokens` (100 to 5000)
  - `content_type` (prose, mixed, code-dominant)
- **Calibration:** `fresh_calibration(break_even_reads=3)` fixture
- **Assertions per fixture:**
  - Gate decision matches the expected `(passed, reason)` pair in the fixture
  - No Haiku call occurs when gate denies (mock provider's `call_count == 0`)
  - When gate passes, Haiku call is made exactly once (or up to MAX_RETRIES=2 for fixing)

### 6.5 `test_05_chaos_cascade_isolation` — **the Priority 1 test**

**Goal:** Iterate the enumerated §5.2 6-row cascade table. For each row: force the named component to raise, assert all listed "what still must run" components DID run and all listed "what does NOT happen" outcomes did NOT happen.

- **Mechanism:** `pytest.mark.parametrize` over the 6 rows. Fixture `force_fail(component)` monkey-patches the component's main entry point to raise `ComponentFailureError`.
- **Assertions per row:**
  - All "what still must run" components have a span with `status=ok` in the OTel recorder fixture
  - All "what does NOT happen" outcomes are explicitly negated via `assert not ...`
  - `compression.fallback` tag matches the failing component name + reason
  - Request completes successfully (caller gets a result)
  - Pi-Mono receives a CostRecord with accurate token counts (not compressed-intended)

**Test ID:** `PRAXIS.S2.COMP-INT-005` — tagged `@priority0`, runs first in CI.

### 6.6 `test_06_reconciliation_roundtrip` — tightened to 0.5% drift

**Goal:** Pi-Mono tag aggregation sum equals A/B harness reported savings within 0.5% drift.

- **Setup:** Spin up a real `CostTracker` against in-memory SQLite. Produce 100 compression-tagged `LLMRequest` objects via a fixture workload. Run them through the tracker.
- **Assertion:**
  ```python
  summary = await tracker.get_cost_summary(Filter(tag_match={"compression.mode": "on"}))
  tag_savings = sum(int(r.tags["compression.tokens.before"]) - int(r.tags["compression.tokens.after"])
                    for r in records_for_summary(summary))
  harness_savings = harness_run_result.total_tokens_saved
  drift = abs(tag_savings - harness_savings) / harness_savings
  assert drift < 0.005, f"Reconciliation drift {drift*100:.3f}% exceeds 0.5% gate"
  ```

### 6.7 `test_07_rtk_orphan_attribution`

**Goal:** RTK calls with no downstream `LLMRequest` within 60s land in the orphan bucket.

- **Setup:** Mock clock so `now()` advances predictably.
- **Steps:**
  1. `await rtk.run_command(["git", "status"])` → savings recorded
  2. Advance mock clock by 61 seconds
  3. Invoke nightly rollup `await harness.rollup_rtk_orphans()`
- **Assertion:** The savings are bucketed with `compression.rtk.orphan=true`; dashboard-metric-reader returns the bucket with the correct byte count.

### 6.8 `test_08_ab_harness_config_drift`

**Goal:** Mismatched config hashes between on/off arms raise `HarnessConfigDriftError` and abort the run.

- **Setup:** Run `harness.run_workload(workload, mode="request")` with an injected mid-run config swap.
- **Assertion:** `HarnessConfigDriftError` raised with both hash values in the message; no partial results written to the harness database.

### 6.9 `test_09_gate_calibration_stale` (P_V6 integration)

**Goal:** Caveman gate denies with `reason=calibration_stale` when calibration is older than 7 days.

- **Setup:** `CalibrationSnapshot` with `refreshed_at = now() - timedelta(days=8)`.
- **Assertion:** Gate returns `(False, "calibration_stale")`. Mock provider's `call_count == 0`. Tag `compression.caveman.gate_denied=calibration_stale` attached.

### 6.10 `test_10_gate_prediction_feedback` (P_V7 integration)

**Goal:** After 30 synthetic runs with over-predicted downstream reads, calibration's `break_even_reads` increments.

- **Setup:** Fresh calibration at `break_even_reads=3`. Simulate 30 compressions where `expected_downstream_reads=5` but observed `actual_reads_observed_in_7d=2` (below break-even).
- **Trigger:** Run nightly calibration adjustment step.
- **Assertion:** `calibration.break_even_reads >= 4`; `caveman.calibration.adjusted` event emitted with `reason=prediction_error_median_exceeded`.

### 6.11 `test_11_tag_budget_overflow`

**Goal:** When total tags on an `LLMRequest` would exceed 28, orchestrator drops lowest-priority compression tags per the §4.1 order.

- **Setup:** Construct an `LLMRequest` with 20 non-compression tags. Full compression pipeline attempts to add 14 compression tags → total 34, exceeding the 28 ceiling.
- **Assertions:**
  - After pipeline, `LLMRequest.tags` has ≤ 28 keys
  - Must-keep tags (`compression.mode`, `compression.pipeline`, `compression.tokens.before/after`, `compression.bytes.before/after`, `compression.fallback`) are all present
  - Lowest-priority tags (`compression.caveman.intensity`, `compression.caveman.dialect`, `compression.tonl.tokenizer`) are dropped
  - `orchestrator.tag_budget_exceeded` event emitted with the dropped tag list

---

## 7. COMPONENT-SPECIFIC TEST STRATEGIES

### 7.1 Orchestrator (Matrix 6 Rank 1, severity 4.15)

**Doctrine:** The orchestrator is the priority 1 test target. It is simultaneously the smallest component by LOC and the most important by consequence. Tests run FIRST in CI (`pytest -k orchestrator` is the smoke layer before the full suite).

**Test emphasis:**
- Integration #5 (chaos cascade) is the centerpiece
- Unit tests cover pipeline order, tag attribution, fallback propagation, try/except boundary correctness
- Static tests: AST scan asserts every component-touching method has an explicit `try/except ComponentFailureError` boundary
- No property test targets the orchestrator directly beyond P_O1/P_O2

**Definition of Done:** Integration #5 green on all 6 cascade rows. Unit tests at 100% line+branch. Static AST scan green.

### 7.2 Caveman (Rank 2, severity 3.60) — the **most invested test surface**

**Doctrine:** Caveman is the RPN-9 risk-owner. It ships P0 behind `compression.caveman.enabled` (default OFF per §5.1 of requirements-validation.md). Test strategy covers Caveman at full depth regardless of the flag — the flag is a safety net, not a test scope reduction.

**Test emphasis, in priority order:**
1. **Adversarial corpus (§5) — 60+ hand-curated cases + generator**
2. **Property tests P_V1–P_V7 — 3000 Hypothesis cases each**
3. **Integration tests #4 (gate decisions), #9 (calibration staleness), #10 (prediction feedback)**
4. **Golden fixtures for every intensity × dialect combination**
5. **Unit tests for validate_structural (H1-H5), validate_semantic (S1-S4), boundary detector, gate logic**

**Negative tests:** A separate directory `tests/caveman_negative/` contains inputs that MUST pass (legitimate compression, not corruption). False positive rate target: < 2%. If S3/S4 triggers on legitimate prose more often than that, the lexicon is too aggressive.

**Definition of Done:**
- 100% adversarial corpus catch rate
- Property tests at 3000 cases, zero counter-examples
- False positive rate on negative corpus < 2%
- Net-positive gate simulation (integration #10) green

### 7.3 Forge (Rank 3, severity 2.90)

**Doctrine:** Determinism is Forge's value proposition. The most important invariants are zero LLM calls and reasoning preservation.

**Test emphasis:**
1. **Property P_F4 — mock provider, count = 0** (absolute gate)
2. **Static AST scan** — `static/test_no_llm_calls_in_forge.py` asserts no `anthropic`, `openai`, or `google.generativeai` imports anywhere in `forge/`
3. **Property P_F5b** (non-overwrite, from FMEA F.6) — single-most-important new post-elicitation property
4. **Property P_F6** (schema drift) — fuzz-injection against unknown `reasoning_schema_version`
5. **Golden fixtures for each trigger type** (tokens, turns, messages)
6. **Integration #2** — BMAD session replay

**Fuzz corpus for reasoning schemas:**
```
tests/golden/fixtures/forge/reasoning_schemas/
├── anthropic_thinking_v1.json                  # Current known-good
├── anthropic_extended_thinking_hypothetical.json # Fuzz target for P_F6
├── openai_reasoning_details_v1.json
├── unknown_schema_XYZ.json                      # Should trigger alert
└── missing_required_field.json                  # Should log warn, continue
```

**Definition of Done:** Zero LLM calls verified three ways (property, static scan, integration #2). P_F5b green. Schema fuzz corpus all 5 cases handled correctly.

### 7.4 TONL (Rank 4, severity 2.85)

**Doctrine:** Round-trip correctness is the entire value proposition. Hypothesis does most of the work.

**Test emphasis:**
1. **Property P_T1** at `max_examples=5000` with aggressive strategy composition
2. **Golden fixtures per tokenizer** — catches silent format drift
3. **Security limit tests** (P_T2) — every limit must be reachable in a test
4. **Streaming memory test** — `tracemalloc` assertion for O(1)
5. **Unit tests for each optimizer strategy** (tabular, delta, column reorder)

**Tokenizer version pinning test:** `test_tonl_tokenizer_version_rejected.py` generates a payload encoded with `tokenizer="claude-opus-4-6@2025-01-01"` (non-existent version) and asserts decode raises `TONLValidationError`.

**Definition of Done:** Round-trip property green at 5000 cases. All 3 tokenizer SDKs verified in golden fixtures. Streaming memory test asserts `peak_per_item ≤ 2× baseline`.

### 7.5 RTK (Rank 5, severity 1.85) — least invested, most platform-sensitive

**Doctrine:** RTK is the smallest test investment because failures are loud and isolated. But cross-platform verification is mandatory — Amelia cannot catch "binary missing on Linux arm64" from her dev machine.

**Test emphasis:**
1. **Cross-platform matrix** — 5 platforms minimum (see §2.1)
2. **Binary version pin test** — `rtk --version` matches `RTK_PINNED_VERSION`
3. **Subprocess timeout test** — synthetic hanging command
4. **Telemetry JSON parse round-trip**
5. **Integration #3** (real shell) and **#7** (orphan attribution)

**Cross-platform CI matrix:**

| Platform | CI runner | Skipped unless |
|----------|-----------|----------------|
| Linux x64 | `ubuntu-latest` | Always runs |
| Linux arm64 | Self-hosted ARM runner | Available |
| macOS x64 | `macos-13` | Always runs |
| macOS arm64 | `macos-14` | Always runs |
| Windows x64 | `windows-latest` | Always runs |

Each platform runs `test_cross_platform/test_rtk_{platform}.py` which exercises:
- Binary resolution
- `--version` smoke
- One real command (`git --version` to confirm subprocess execution)
- Telemetry JSON read

**Definition of Done:** All 5 platforms green on the binary version pin + one real-command test.

---

## 8. A/B BENCHMARK HARNESS TEST OWNERSHIP

The harness is test infrastructure but it IS tested itself. Without test coverage on the harness, regressions in the harness get silently attributed to compression regressions.

### 8.1 Harness test coverage targets

| Harness component | Target | Why |
|-------------------|:---:|-----|
| `harness/runner.py` | ≥90% line | Orchestrates runs; bugs here invalidate all results |
| `harness/compare.py` | ≥95% line | Diff math must be exact |
| `harness/reporter.py` | ≥85% line | Reports go to the public dashboard eventually |
| `harness/storage.py` | ≥90% line | SQLite schema + queries |
| `harness/workloads/*` | ≥75% line | Workload replays; partial coverage acceptable |

### 8.2 Harness-specific tests

- **Seed pinning:** `test_harness_seed_pinning.py` — run two on-arms with the same seed, assert byte-identical tokens consumed.
- **Config hash:** `test_harness_config_hash.py` — mutate config mid-run, assert `HarnessConfigDriftError` raised.
- **Report format:** `test_harness_report_format.py` — generate a report, parse it as Markdown, assert all required sections present.
- **DB schema:** `test_harness_db_schema.py` — round-trip a report through SQLite, assert no data loss.

### 8.3 Gated test: full nightly harness run against real Haiku

`integration/test_01_end_to_end_pipeline.py` is the only test that hits real Haiku. Cost cap: $0.10 per run, enforced by a pre-check that estimates tokens and fails the test before any API call if the estimate exceeds cap.

---

## 9. CI PIPELINE AND GATE CONFIGURATION

### 9.1 CI job layout

```yaml
# .github/workflows/compression-tests.yml (sketch)
jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check praxis/kernel/compression/
      - run: mypy --strict praxis/kernel/compression/
      - run: pytest tests/static/

  unit:
    needs: static
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/ --cov=praxis/kernel/compression --cov-branch --cov-report=xml

  property:
    needs: static
    runs-on: ubuntu-latest
    strategy:
      matrix:
        suite: [tonl, forge, caveman, rtk, orchestrator]
    steps:
      - run: pytest tests/property/test_${{ matrix.suite }}_properties.py

  golden:
    needs: unit
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/golden/

  adversarial:
    needs: unit
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/adversarial/

  integration:
    needs: [property, golden, adversarial]
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/integration/ -m "not nightly"

  cross_platform:
    needs: static
    strategy:
      matrix:
        os: [ubuntu-latest, macos-13, macos-14, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - run: pytest tests/cross_platform/

  stress:
    needs: integration
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'   # nightly only
    steps:
      - run: pytest tests/stress/

  nightly_harness:
    needs: integration
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - run: pytest tests/integration/ -m nightly
      - run: python -m praxis.compression.harness.runner --workload bmad_r4 --nightly
```

### 9.2 Gate thresholds (matching §0.1 coverage)

CI fails on:
- Any ruff/mypy error
- Any unit/property/golden/adversarial test failure
- Integration failure (any of 11)
- Cross-platform failure on any of the 5 platforms
- Aggregate coverage drop below 85%
- Module coverage drop below the table in §0.1
- Hypothesis counter-example on any property test

CI warns (not fails) on:
- Caveman false positive rate on negative corpus in range 2–5%
- A/B harness drift 0.2–0.5% (below the 0.5% fail gate)
- RTK orphan rate between 3% and 5% (below the 5% investigation threshold)

### 9.3 CI-specific perf budget

- Unit tests: < 30 seconds
- Property tests: < 3 minutes (Hypothesis at 3000 cases each)
- Golden: < 30 seconds
- Adversarial: < 1 minute
- Integration (non-nightly): < 5 minutes
- Cross-platform (per OS): < 2 minutes

Total CI time for a PR: < 15 minutes. Nightly (harness + stress) is off the critical path.

---

## 10. GATE DECISION PROTOCOL

Every Stage 2 release uses the Murat gate protocol from `risk-governance.md`:

```
GATE = PASS  if no BLOCKERS and no open CONCERNS
     | CONCERNS if highs exist with mitigation plans + owners
     | FAIL  if any BLOCKER (score=9) or unresolved coverage gap
     | WAIVED if all risks waived by authorized approver
```

### 10.1 Gate evaluation per Stage 2 release

| Risk | Current status | Gate contribution |
|------|---------------|-------------------|
| CM5 (polarity flip) | OPEN, mitigated by S3/S4 + adversarial corpus | Contributes CONCERNS until corpus catch rate = 100% |
| CM2 (reasoning break) | OPEN, mitigated by P_F5b + P_F6 | Contributes CONCERNS until both properties green |
| CM4 (code corruption) | OPEN, mitigated by H2 + boundary detector | Contributes CONCERNS until golden fixtures for every mixed case green |
| CM9 (cascade isolation) | OPEN, mitigated by integration #5 | **BLOCKER until integration #5 is green on all 6 rows** |
| CM10 (tokenizer drift) | OPEN, mitigated by version pinning | Contributes CONCERNS until pinning test green |
| CM12 (A/B config drift) | OPEN, mitigated by integration #8 | Contributes CONCERNS until green |
| CM15 (reconciliation drift) | OPEN, mitigated by integration #6 | Contributes CONCERNS until green at 0.5% |

**Minimum for PASS:** All BLOCKER-contributing items green; all CONCERNS items have mitigations applied or waivers signed.

### 10.2 Waiver policy

Waivers require:
- Signed by Andrey (product) AND Winston (architect)
- Expiry date (maximum 30 days)
- Re-evaluation on expiry
- Documentation in `_bmad-output/test-artifacts/praxis/compression/waivers/`

The compression layer SHOULD NOT ship with any CM5-related waiver. That's the hill I'll die on.

---

## 11. OPEN QUESTIONS

### 11.1 Should the adversarial corpus be public?

**Question:** The polarity + imperative lexicons are finite. Once public, adversaries can craft inputs outside the lexicon. Should the corpus ship with Praxis or stay internal?

**Default:** Internal for Stage 2 P0. Publish selected examples as part of the quality-preservation pitch in Stage 7.

**Who decides:** Andrey.

### 11.2 How often do we regenerate golden fixtures?

**Question:** When a provider SDK changes (rare) or a tokenizer snapshot updates (monthly), we regenerate TONL and Caveman golden fixtures. Is monthly right?

**Default:** Tied to the Pi-Mono pricing snapshot cadence (monthly, first of month UTC). Documented in `update_golden.py` as the canonical refresh trigger.

**Who decides:** Winston + Murat.

### 11.3 Real-Haiku nightly cost cap

**Question:** Nightly harness runs against real Haiku. Cost cap is $0.10 per run per integration test. At 30 days × 1 run/day × 3 workloads, that's ~$9/month. Acceptable?

**Default:** Yes, trivially below budget. If the cap needs to rise (e.g., to cover more workloads), it's a dollar-per-day decision Andrey owns.

**Who decides:** Andrey.

### 11.4 Flakiness budget

**Question:** Integration tests hit real subprocesses (RTK) and a real network (Haiku, nightly). Some flakiness is inevitable. What's the acceptable pass rate?

**Default:** 99.5% on a rolling 7-day window. Any test dropping below 99% is flagged as flaky and enters burn-in remediation (see `ci-burn-in.md`). Flakiness is critical technical debt — I won't let it normalize.

**Who decides:** Murat. Non-blocking for Stage 2.

### 11.5 Should `test_05_chaos_cascade_isolation` run on every PR or nightly only?

**Question:** It's the highest-priority test and it's fast (< 30 seconds). Run every PR.

**Default:** Every PR. P0 tests run first.

**Who decides:** Murat. Confirmed.

---

## 12. REQUIREMENT → TEST TRACEABILITY MATRIX

Every requirement in Winston's `compression/architecture.md` §11.1 (R1–R13) maps to at least one test in this strategy.

| R | Requirement | Tests |
|:---:|-------------|-------|
| R1 | TONL replaces JSON + tokenizer-aware encoding | Property P_T1, golden fixtures per tokenizer |
| R2 | Forge deterministic compaction + 6-msg retention + two-tier triggers | Property P_F1 (idempotency), P_F2 (retention), unit test_triggers |
| R3 | RTK transparent CLI + flag-aware | Integration #3, golden fixtures per command, cross-platform matrix |
| R4 | Caveman 6 intensity levels + multi-dialect + circuit breaker | Unit test_dialects, golden fixtures per intensity, adversarial corpus |
| R5 | Pipeline composition (TONL → LLM → Caveman → RTK); Forge orthogonal | Unit test_pipeline_order (§7.1), property P_O1 |
| R6 | Pi-Mono integration via tags | Integration #6 (reconciliation round-trip) |
| R7 | Quality circuit breakers per component + fallback | Integration #5 (chaos), property P_O2 (fallback tag) |
| R8 | A/B benchmark harness runnable | Harness test suite (§8) + integration #1 (nightly) |
| R9 | Zero-cost Forge (no LLM calls) | Property P_F4 + static AST scan |
| R10 | RTK <10ms per command | Property P_R1 + stress test |
| R11 | TONL streaming O(1) memory | Property P_T3 + tracemalloc assertion |
| R12 | All components use Pi-Mono Decimal | Static AST scan mirroring Stage 1 + integration #6 |
| R13 | Test coverage ≥ 85% | CI gate in §9.2 |

Every CM risk in §1 maps to at least one test:

| CM | Risk | Primary test |
|:---:|------|--------------|
| CM1 | TONL lossy round-trip | P_T1 |
| CM2 | Forge reasoning break | P_F5, P_F5b, P_F6 |
| CM3 | Forge tool pair split | P_F3 |
| CM4 | Caveman code corruption | P_V1 + H2 golden fixtures |
| **CM5** | **Caveman polarity flip** | **Adversarial corpus + P_V3 + P_V4** |
| CM6 | Caveman cost > savings | Integration #10 + harness |
| CM7 | RTK binary crash | Integration #3 + subprocess unit |
| CM8 | RTK telemetry race | Stress `test_concurrent_rtk` |
| CM9 | Cascade failure | **Integration #5** (the single most important test) |
| CM10 | Tokenizer drift | TONL version pinning test |
| CM11 | Tag budget overflow | Integration #11 |
| CM12 | A/B config drift | Integration #8 |
| CM13 | Calibration staleness | Integration #9 (P_V6) |
| CM14 | Prediction feedback drift | Integration #10 (P_V7) |
| CM15 | Reconciliation drift | Integration #6 (tightened to 0.5%) |

Every gap = blocker. Every test = a risk owner.

---

## 13. DEFINITION OF DONE (PER COMPONENT)

### 13.1 Orchestrator
- [ ] Integration #5 green on all 6 cascade rows
- [ ] Unit tests at 100% line + branch coverage
- [ ] P_O1 + P_O2 property tests green
- [ ] Static AST scan: every component call has explicit try/except boundary

### 13.2 Caveman
- [ ] Adversarial corpus 100% catch rate (60+ cases)
- [ ] Property tests P_V1–P_V7 green at 3000 cases each
- [ ] False positive rate on negative corpus < 2%
- [ ] Integration tests #4, #9, #10 green
- [ ] Feature flag `compression.caveman.enabled` validated in both ON and OFF states

### 13.3 Forge
- [ ] Property P_F4 green (0 LLM calls)
- [ ] Static AST scan: no LLM imports in `forge/`
- [ ] Property P_F5b green (non-overwrite)
- [ ] Property P_F6 green (schema drift detection)
- [ ] Integration #2 (BMAD replay) green
- [ ] All 5 golden fixtures per trigger type green

### 13.4 TONL
- [ ] Property P_T1 green at 5000 cases
- [ ] Golden fixtures per tokenizer green
- [ ] Streaming memory test green (peak_per_item ≤ 2× baseline)
- [ ] Tokenizer version pinning test green

### 13.5 RTK
- [ ] Cross-platform tests green on all 5 platforms
- [ ] Binary version pin test green
- [ ] Integration #3 (real shell) green
- [ ] Integration #7 (orphan attribution) green

### 13.6 Harness
- [ ] Seed pinning test green
- [ ] Config drift test (integration #8) green
- [ ] Report format test green
- [ ] DB schema round-trip test green

---

## 14. HANDOFF

This strategy is ready for Amelia (Step 2.3) and Quinn (Step 2.4).

### 14.1 For Amelia (implementation)

The test skeleton (directory layout in §2.1) is the scaffold. For each module, write code that makes its P0 tests green FIRST, then work down the priority list. The Murat principle applies: *tests first, AI implements, suite validates.*

Non-negotiable for P0:
- Every orchestrator method has `try/except ComponentFailureError` boundaries (Matrix 6 Rank 1)
- Every Caveman validator method returns typed errors matching the adversarial corpus expectations (CM5)
- Forge's compactor never imports `anthropic`, `openai`, or `google.generativeai` (R9)
- RTK wrapper has a vendored binary for all 5 platforms

### 14.2 For Quinn (QA execution)

Test execution priority:
1. Static + unit (fastest, surface most bugs)
2. Property (Hypothesis catches real cases)
3. Adversarial (this is where P0 CM5 lives)
4. Integration #5 (chaos — highest Matrix 6 severity)
5. Integration #4 (Caveman gate)
6. Integration #6 (reconciliation at 0.5%)
7. Remaining integration (#1-#11 minus already-run)
8. Cross-platform (per-OS matrix)
9. Stress + nightly harness (off critical path)

Quinn owns: making every test green. Murat owns: deciding which tests exist. Amelia owns: making the code match both.

### 14.3 For Winston (if elicitation round 2 is needed)

If Amelia or Quinn surfaces a failure mode this strategy does not cover, route it back through `/bmad-advanced-elicitation` as Elicitation Round 2. Do NOT amend this document in place — elicitation is episodic, and this strategy is the v1.0 contract for Stage 2.2.

### 14.4 For Andrey

Two decisions still outstanding from `requirements-validation.md` §5.1 and §5.2:
- **§5.1 Caveman P0 scope.** This strategy assumes Option C (feature-flagged). If you pick Option A or B, the Caveman section scales up or down; the rest of the strategy is unchanged.
- **§5.2 Embedding validator window.** Strategy has embedding as Stage 2 P1. Confirm or override.

**Test strategy v1.0 is ready for implementation.**

— Murat, Master Test Architect
2026-04-12
