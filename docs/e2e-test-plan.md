# Verdaca — End-to-End Test Plan

**Date:** 2026-04-17
**Status:** Design only — no tests implemented, no debt items closed
**Authors:** Murat (TEA, risk-based spec), Quinn (QA, runnable skeletons), Winston (Architect, boundary review)
**Supersedes:** ad-hoc coverage assumptions from Stages 1-6

---

## Purpose & Scope

Verdaca is a 7-module pipeline (Pi-Mono → Compression → Memory → Runtime → MAC → Studio → Shell). Unit and integration tests cover each module in isolation. This plan defines the **top of the test pyramid** — a minimal set of E2E scenarios that exercise the wiring *between* modules under realistic conditions.

**In scope:** cross-module contract drift, latent integration bugs (C-2, C-4), observability under load, tenant isolation, webhook delivery.

**Out of scope:** Pi-Mono Decimal arithmetic (property tests), TONL round-trip encoders (unit), Forge determinism (unit), MAC gate scorers in isolation (unit), Studio Jinja2 rendering (unit), Clerk JWT parsing (unit). Delegated to existing suites.

---

## Current State — Nothing Has Been Fixed Yet

Verified from code inspection on 2026-04-17:

| Issue | Status | Evidence |
|---|---|---|
| **C-4 Memory promotion** | ❌ Unwired | `kernel/mac/pre-sales-report.md:34` — *"Memory `reuse_successful` promotion path has no caller in the current build. Stage 7 must resolve."* |
| **A4 human validation** | ❌ Deferred | Benchmark is N=10 directional only; no p-values, no human panel |
| **C-2 ID prefix drift** | ❌ Live | Shell uses ULIDs; MAC spec says `mac:` prefix |
| **5 Cleo WARNINGs** | ❌ Present | 31 occurrences of `manufactured_dissent` / `synthesized raw_score` / broad `except Exception` across 14 files |
| **Brand rename** | ❌ Not propagated | `src/praxis/*` still the namespace |
| **E2E suite** | ❌ No directory | `tests/e2e/` does not exist |

---

## Order of Operations Before Tests Run

1. Wire `mac.reuse_successful` caller in MAC (fixes C-4 — **required** for VERDACA-E2E-02 to flip from xfail to strict)
2. Reconcile ULID vs `mac:` prefix (fixes C-2 — **required** for VERDACA-E2E-04 to pass)
3. Bound `_events` ring buffer; replace broad `except Exception` with typed handlers (fixes 2 of 5 Cleo WARNINGs)
4. Stand up `tests/e2e/` with `docker-compose.e2e.yml` (Postgres + pgvector + Redis), `pytest-docker`, Playwright-python, Toxiproxy
5. Seed Clerk test tenant + Stripe test-mode webhook listener + LLM cassettes
6. Record `tests/fixtures/session_a_memory_dump.sql` (needed by -02)
7. Implement VERDACA-E2E-01 — must go green first
8. Run Dr. Quinn's 20-decision blind-rater benchmark (closes A4 — unblocks all headline claims)
9. Flip VERDACA-E2E-02 from `@pytest.mark.xfail` to strict

---

## Scenario Catalog

### VERDACA-E2E-01 — Single-session strategic advisory, happy path

| Field | Value |
|---|---|
| **Risk-priority** | HIGH (PR-gate blocker) |
| **Targets** | Rename refactor (RPN 100), Cleo `_events` unbounded (RPN 168 partial), Stage 7 smoke (RPN 384 partial) |
| **Runtime budget** | 90-120s |
| **CI trigger** | Every PR |
| **LLM cost** | ~$0.15 replayed (cassette), $0 real |

#### Preconditions
- Clean Postgres + pgvector + Redis containers (docker-compose.e2e.yml)
- Clerk test tenant seeded with `user_e2e_01` + active Stripe test subscription
- Stripe test-mode webhook listener attached
- 16-agent manifest loaded; Class A-E tool tiers registered
- Empty Beads store, empty Mem0 index

#### Arrange
```python
@pytest.fixture
def verdaca_stack():
    # boots FastAPI + Next.js preview on :3000, applies migrations
    ...
```
Mock boundaries: **only** outbound LLM calls → recorded-cassette replay (deterministic). Everything else real.

#### Act
1. `[Shell]` `POST /api/v1/sessions` with Clerk JWT → returns `session_id`
2. `[Shell→Studio]` hydrates `strategic-advisory.yaml`, renders Jinja2 with prompt *"Should we enter EU market in Q3?"*
3. `[Studio→MAC]` rendered plan → task interpreter → plan decomposer → 3 sub-tasks
4. `[MAC→Runtime]` 3-cycle controller dispatches Analyst, Strategist, Skeptic (Class-B tools)
5. `[Runtime→Compression]` context TONL-encoded + Forge-compacted outbound; Caveman-compressed inbound
6. `[Runtime→Pi-Mono]` every LLM call emits `CostEvent` with `decimal.Decimal`
7. `[MAC→Memory]` gates fire; `quality_score` computed; Beads writes snapshot; Atelier writes decision embedding; Mem0 writes semantic chunk
8. `[Shell]` Stripe webhook on session close → usage billed

#### Assert

| Module | Assertion |
|---|---|
| Pi-Mono | `sum(CostEvent.amount) == session.total_cost` using `Decimal` equality; all amounts `quantize(Decimal('0.000001'))` |
| Compression | TONL-decoded payload round-trips byte-equal for ≥1 agent turn; Forge ratio ≥ 0.3 on prompts > 2KB |
| Memory | Beads snapshot count == 3; Atelier pgvector has 1 decision row with 1536-dim embedding; Mem0 retrieve returns ≥ 1 chunk |
| Runtime | Exactly 3 agents dispatched; all calls used Class-B tools; MCP sandbox records no escape attempts |
| MAC | All 12 gates evaluated; `quality_score ∈ [0,1]`; Pydantic validator raises no `ValidationError`; `_events` length ≤ configured cap |
| Studio | Rendered template matches golden `tests/goldens/strategic-advisory-rendered.txt` |
| Shell | Session row committed; Stripe webhook delivered HTTP 200; `GET /api/v1/sessions/{id}` returns full transcript |

#### Runnable skeleton

```python
# tests/e2e/test_strategic_decision_smoke.py
import pytest
from decimal import Decimal
import httpx

@pytest.mark.e2e_pr
@pytest.mark.asyncio
async def test_strategic_decision_smoke(
    verdaca_stack, clerk_test_user, pi_mono_tracker, memory_store, studio_templates
):
    """Happy path: one query hits every module once. If red, nothing else matters."""
    template = studio_templates.load("strategic_decision_v1.yaml")
    prompt = template.render(question="Should we enter the EU market in Q3?")
    pi_mono_tracker.reset()
    assert pi_mono_tracker.total_cost_usd == Decimal("0")

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        resp = await client.post(
            "/api/v1/sessions",
            json={"prompt": prompt, "template_id": "strategic_decision_v1"},
            headers={"Authorization": f"Bearer {clerk_test_user.session_token}"},
        )
    assert resp.status_code == 200
    result = resp.json()

    assert result["cycles_completed"] == 3
    assert 0.0 <= result["quality_score"] <= 1.0
    assert result["quality_score"] >= 0.65
    assert pi_mono_tracker.total_cost_usd > Decimal("0")
    assert result["compression_ratio"] < 1.0
    assert memory_store.has_trace(result["trace_id"])
    assert len(result["agents_invoked"]) >= 3
    # Stripe metered-usage event enqueued
    assert result["billing"]["stripe_event_id"] is not None
```

#### Failure modes caught
- Rename refactor breaks `src/praxis/*` imports
- Pydantic field drift between MAC ↔ Memory
- Cost-event schema drift
- Unbounded `_events` leak (single-session bound check)
- Studio template regression
- Stripe webhook silent drop

---

### VERDACA-E2E-02 — Cross-session memory reuse (C-4 canary) **[CRITICAL]**

| Field | Value |
|---|---|
| **Risk-priority** | HIGH |
| **Targets** | **C-4 Memory promotion (RPN 560) — closes latent bug**; A4 partial (RPN 810 partial) via reuse-consistency check |
| **Runtime budget** | 150-180s |
| **CI trigger** | Nightly + PR path-filter on `kernel/memory/**` or `kernel/mac/**` |
| **LLM cost** | ~$0.20 replayed |
| **Current state** | `@pytest.mark.xfail(strict=False, reason="C-4 deferred")` until `mac.reuse_successful` caller wired |

#### Preconditions
- Stack from -01
- Beads/Mem0/Atelier pre-seeded from `tests/fixtures/session_a_memory_dump.sql` (recorded from prior -01 run)
- Seed dump contains 3 high-`quality_score` decisions tagged `reusable=True`
- MAC config: `enable_cross_session_reuse=True`, `reuse_threshold=0.75`
- Cassette replay disabled for Atelier *retrieve* path (real pgvector similarity); LLM generation still replayed
- `user_e2e_02` is a **different** Clerk user than Session A's owner (tenant-isolation test)

#### Act
1. `[Shell]` Session B starts with prompt semantically similar to Session A's (cosine > 0.85 expected)
2. `[MAC]` Info-Asymmetry Router flags "prior decision available"; Cross-Session Learning Loop calls `mac.reuse_successful(query_embedding)`
3. **`[MAC→Memory]` `mac.reuse_successful` MUST invoke Atelier pgvector query → return ≥1 decision row → MAC MUST consume it into plan decomposer as a seed** *(the C-4 canary — this call path must exist)*
4. `[MAC]` Plan decomposer produces sub-tasks informed by retrieved decision (sub-task prompt contains `[reused:decision_id=...]`)
5. `[Runtime→Compression→Pi-Mono]` as in -01
6. `[Memory]` new Beads snapshot with `parent_decision_id` FK to reused Atelier row
7. `[MAC]` gates re-score; `quality_score` of reused path ≥ original (monotone-reuse invariant)

#### Assert

| Module | Assertion |
|---|---|
| **Memory** | **Atelier query log shows ≥1 `SELECT ... ORDER BY embedding <=> $1 LIMIT N` during Session B** (C-4 canary) |
| MAC | `reuse_successful` called (spy count == 1); `plan.seeds` non-empty; `quality_score_B ≥ quality_score_A − 0.05` |
| Memory | Beads row has non-null `parent_decision_id`; cross-session FK resolves |
| Pi-Mono | `session_B_cost < session_A_cost × 0.7` (reuse saves tokens) |
| Compression | Forge cache-hit rate ≥ 0.2 on seeded context |
| Runtime | No Class-D/E tools invoked (reuse path stays sandboxed) |
| Studio | Template rendered with non-empty `{{ reused_context }}` block |
| Shell | Response payload includes `reused_from: session_a_id` audit field |
| **Tenant isolation** | `user_e2e_01`'s other memories (not tagged reusable) MUST NOT appear in `user_e2e_02`'s retrieval — assert by ID exclusion list |

#### Runnable skeleton

```python
# tests/e2e/test_cross_session_memory_reuse.py
import pytest
from decimal import Decimal

@pytest.mark.e2e_nightly
@pytest.mark.xfail(strict=False, reason="C-4 deferred to Stage 7")
@pytest.mark.asyncio
async def test_cross_session_memory_reuse(
    verdaca_stack, seed_session_a, mac_controller, memory_store, pi_mono_tracker
):
    """
    C-4 GUARD: mac.reuse_successful has no production caller today.
    This test MUST fail until Stage 7 wires the promotion path.
    Flip to strict once C-4 is closed.
    """
    query_a = "What's our recommended cloud migration sequence for a regulated bank?"
    query_b = "How should a regulated bank sequence its cloud migration?"

    # Session 1 — cold
    pi_mono_tracker.reset()
    r1 = await mac_controller.deliberate(prompt=query_a, user_id="user_e2e_01", session_id="sess-001")
    cost_cold = pi_mono_tracker.total_cost_usd
    assert r1.memory_hits == 0
    assert cost_cold > Decimal("0")

    await mac_controller.close_session("sess-001")
    memory_store.flush_session_cache()

    # Session 2 — different user, semantic twin
    pi_mono_tracker.reset()
    r2 = await mac_controller.deliberate(prompt=query_b, user_id="user_e2e_02", session_id="sess-002")
    cost_warm = pi_mono_tracker.total_cost_usd

    # C-4 canary
    assert memory_store.spy.call_count("reuse_successful") == 1
    assert r2.memory_hits >= 1, "C-4 regression: no cross-session promotion"
    assert cost_warm < cost_cold * Decimal("0.7"), "Expected >=30% cost reduction from reuse"
    assert r2.quality_score >= r1.quality_score - 0.05
    assert r2.metadata["reused_from"] is not None
    # Tenant isolation — user_e2e_02 must not see user_e2e_01's non-reusable memories
    assert not memory_store.leaked_ids(from_user="user_e2e_01", to_user="user_e2e_02")
```

#### Failure modes caught
- **C-4 regression** (absence of caller for `reuse_successful`)
- Tenant leakage in pgvector retrieval
- Stale embedding dimension
- `parent_decision_id` FK broken
- Stage 7 debt item #4 silent regression

---

### VERDACA-E2E-03 — Sustained load + chaos (16-agent saturation)

| Field | Value |
|---|---|
| **Risk-priority** | MED |
| **Targets** | Stage 7 zero-traffic gap (RPN 384); Cleo WARNINGs full (RPN 168 — broad `except`, synthesized `raw_score`, Any-typed callables) |
| **Runtime budget** | 8-10 min |
| **CI trigger** | Nightly only |
| **LLM cost** | ~$0.30 replayed |

#### Preconditions
- -01 stack + Locust (or `pytest-xdist`) for concurrent runner
- All 16 agents from manifest exercised at least once
- Toxiproxy in front of Redis for fault injection
- 3 rotated Studio templates; LLM cassettes parameterized for variety

#### Act
1. Ramp to 50 concurrent `[Shell]` session creates over 5 minutes
2. `[MAC]` routes across all 16 agents; Class A-E tools all hit ≥1
3. `[Compression]` RTK CLI proxy handles ≥100 compaction calls; Caveman compresses every response
4. Toxiproxy injects 200ms Redis latency at t=120s, then 5s Redis blackout at t=180s
5. Observe `[Memory]` Beads/Atelier write-queue behavior under blackout
6. Redis restored t=185s; assert queue drains

#### Assert

| Module | Assertion |
|---|---|
| Pi-Mono | Zero cost events lost (`len(events) == expected_count`); no `Decimal → float` coercion in logs |
| Compression | TONL decode 100%; Forge determinism hash stable across 3 identical inputs; RTK proxy p99 < 500ms |
| Memory | Writes queue locally during blackout; post-recovery Beads + Atelier reconcile with zero drops; Mem0 eventual-consistency < 10s |
| Runtime | All 16 agent IDs observed in trace; MCP sandbox zero escape events; Class-E tool calls all carry human-approval token |
| MAC | No broad `except Exception` swallowed a real fault (log-scan: every caught exception has typed handler); `raw_score` distribution varied (not all identical — synthesized-score smell) |
| Studio | All 3 templates rendered without Jinja2 `UndefinedError` under concurrency |
| Shell | HTTP error rate < 1%; Stripe webhook delivery 100% post-recovery |

#### Runnable skeleton

```python
# tests/e2e/test_sustained_load_chaos.py
import pytest
import asyncio
from pytest_toxiproxy import ToxiproxyClient

@pytest.mark.e2e_nightly
@pytest.mark.slow
@pytest.mark.asyncio
async def test_sustained_load_chaos(verdaca_stack, toxiproxy, locust_runner, telemetry):
    """50 concurrent sessions over 5 min + Redis latency/blackout. All 16 agents exercised."""
    redis_proxy = toxiproxy.proxy("redis")

    locust_runner.ramp(users=50, duration_s=300, templates=["strategic", "operational", "m_and_a"])

    await asyncio.sleep(120)
    redis_proxy.add_toxic("latency", attributes={"latency": 200})
    await asyncio.sleep(60)
    redis_proxy.disable()  # 5s blackout
    await asyncio.sleep(5)
    redis_proxy.enable()

    await locust_runner.wait_complete()

    assert telemetry.cost_events_lost == 0
    assert telemetry.agents_observed >= 16
    assert telemetry.http_error_rate < 0.01
    assert telemetry.webhook_delivery_rate == 1.0
    assert telemetry.memory_queue_drops == 0
    # Cleo WARNING guards
    assert telemetry.broad_except_swallows == 0, "broad except Exception caught a real fault"
    assert telemetry.raw_score_distinct_values >= 3, "synthesized raw_score — all identical"
```

#### Failure modes caught
- Silent cost loss under load
- Memory-queue drops during Redis failover
- Broad-except swallowing a real fault
- Agent-manifest drift (one of 16 agents never dispatched)
- Template `UndefinedError` under concurrency
- Stripe webhook backlog corruption

---

### VERDACA-E2E-04 — Cost-event round-trip with ID prefix assertion (Winston's addition)

| Field | Value |
|---|---|
| **Risk-priority** | MED |
| **Targets** | **C-2 ULID vs `mac:` prefix drift** — whole class of silent cost-drift bugs |
| **Runtime budget** | 30-45s |
| **CI trigger** | Every PR |
| **LLM cost** | ~$0.05 replayed |

#### Preconditions
- Stack from -01
- Single MAC deliberation that triggers ≥1 Studio template render and ≥1 Memory reuse attempt

#### Act
1. Subscribe to Pi-Mono cost-event bus with capturing sink
2. Execute one deliberation through `[Shell→Studio→MAC→Runtime→Memory]`
3. Collect every `CostEvent` emitted during the run

#### Assert
- Every event has an ID matching its emitting module's declared prefix (`mac:` for MAC, ULID for Shell, `studio:` for Studio)
- Shell's billing aggregator resolves 100% of IDs back to a module (zero unresolved)
- No event dropped between emit and aggregate (`emitted_count == aggregated_count`)

#### Runnable skeleton

```python
# tests/e2e/test_cost_event_id_prefix.py
import pytest

@pytest.mark.e2e_pr
@pytest.mark.asyncio
async def test_cost_event_id_prefix_roundtrip(verdaca_stack, cost_event_sink, billing_aggregator):
    """Catches C-2 + any future module that forgets to declare its ID prefix."""
    deliberation_id = await verdaca_stack.run_deliberation(
        prompt="Mini pricing scenario", template_id="strategic_decision_v1"
    )

    events = cost_event_sink.events_for(deliberation_id)
    assert len(events) > 0

    valid_prefixes = {"mac:", "studio:", "runtime:"}  # plus ULID for Shell
    for event in events:
        assert (
            event.id.startswith(tuple(valid_prefixes))
            or event.id_is_ulid()
        ), f"Event {event.id} has unknown prefix (C-2 regression or new module without declared prefix)"

    aggregated = billing_aggregator.aggregate(deliberation_id)
    assert aggregated.event_count == len(events), "Billing dropped events between emit and aggregate"
    assert aggregated.unresolved_ids == [], f"Unresolved IDs: {aggregated.unresolved_ids}"
```

#### Failure modes caught
- **C-2 regression**: Shell ULID vs MAC `mac:` prefix mismatch
- Any future module added without declaring its cost-event prefix
- Silent cost drift between emit and aggregate

---

## Coverage Matrix — Scenarios vs Integration Boundaries

| Scenario | Cost bus | Compression wire | Mem telemetry | MCP tiers | quality_score | YAML template | Webhook auth | ID prefix |
|---|---|---|---|---|---|---|---|---|
| **E2E-01** Happy path | ✅ | ✅ | ✅ | ⚠️ Class A-B only | ✅ | ✅ | ⚠️ pre-auth assumed | ❌ |
| **E2E-02** Memory reuse | ✅ | ⚠️ cache, not codec | ✅ | ❌ not exercised | ⚠️ reuse path | ❌ template unchanged | ✅ **primary test** | ⚠️ same prefix |
| **E2E-03** Load/chaos | ✅ | ✅ | ⚠️ failure-path weak | ⚠️ if adversary probes D-E | ✅ | ❌ malformed not target | ❌ | ❌ |
| **E2E-04** ID prefix | ✅ | — | — | — | — | — | — | ✅ **primary test** |

**Boundaries undertested even by the 4 scenarios:**
- MCP Class D-E tiers — highest-blast-radius external integrations, unexercised
- YAML template schema validation — malformed template at load time
- Stripe webhook auth under session handoff

**Recommendation:** add one Class-D MCP scenario before paid GA.

---

## CI Integration

### Layout
```
tests/
└── e2e/
    ├── conftest.py                                # fixtures: verdaca_stack, clerk_test_user, etc.
    ├── docker-compose.e2e.yml                     # postgres + pgvector + redis
    ├── fixtures/
    │   ├── session_a_memory_dump.sql              # for E2E-02 seed
    │   └── cassettes/                             # recorded LLM replays
    ├── goldens/
    │   └── strategic-advisory-rendered.txt
    ├── test_strategic_decision_smoke.py           # E2E-01
    ├── test_cross_session_memory_reuse.py         # E2E-02 (xfail until C-4 wired)
    ├── test_sustained_load_chaos.py               # E2E-03
    └── test_cost_event_id_prefix.py               # E2E-04
```

### Pytest markers
- `@pytest.mark.e2e_pr` — runs on every PR (E2E-01, E2E-04)
- `@pytest.mark.e2e_nightly` — runs nightly (E2E-02, E2E-03)
- `@pytest.mark.slow` — excluded from PR-gate, runs in dedicated nightly job (E2E-03)

### GitHub Actions triggers
```yaml
e2e_pr:
  on: [pull_request]
  run: pytest -m e2e_pr tests/e2e/
  # ~2 min, ~$0.20 replayed LLM cost

e2e_memory_touch:
  on:
    pull_request:
      paths:
        - 'kernel/memory/**'
        - 'kernel/mac/**'
  run: pytest -m e2e_nightly -k memory_reuse tests/e2e/
  # Forces E2E-02 on any MAC/Memory change — C-4 tripwire

e2e_nightly:
  on:
    schedule: [{cron: "0 3 * * *"}]
  run: pytest -m e2e_nightly tests/e2e/
  # ~12 min, ~$0.55 replayed, pages #verdaca-oncall on failure
```

### Promotion rule
If E2E-02 passes 30 consecutive nightlies, promote to `e2e_pr` and delete the path filter.

---

## Required Fixtures & Infrastructure

| Fixture | Provides | Dependencies |
|---|---|---|
| `verdaca_stack` | Running FastAPI + Next.js, migrated DBs | `pytest-docker`, `docker-compose.e2e.yml` |
| `clerk_test_user` | Seeded Clerk user + JWT | Clerk test tenant, `CLERK_TEST_SECRET_KEY` env |
| `pi_mono_tracker` | Reset-able cost tracker | `kernel.pi_mono` direct import |
| `memory_store` | Beads + Mem0 + Atelier facade with spy wrappers | `kernel.memory` direct import |
| `studio_templates` | YAML loader | `kernel.studio` direct import |
| `mac_controller` | Real `MetaAgentController` against real memory | `kernel.mac` direct import |
| `seed_session_a` | Pre-loads `session_a_memory_dump.sql` into pgvector | DB container from `verdaca_stack` |
| `toxiproxy` | Redis fault injection | `pytest-toxiproxy` |
| `locust_runner` | Concurrent session generator | `locust` |
| `cost_event_sink` | Captures all Pi-Mono events during a test | hooks `kernel.pi_mono.event_bus` |
| `billing_aggregator` | Resolves event IDs → modules | hooks Shell's billing module |
| `telemetry` | Aggregated counters: cost lost, agents observed, error rate, broad-except count | custom test-only collector |

---

## Acceptance Criteria Summary

A Verdaca release is E2E-ready for **paid POV** when:

- ✅ VERDACA-E2E-01 green on PR-gate for 10 consecutive PRs
- ✅ VERDACA-E2E-02 flipped from xfail to strict (C-4 wired) and green on nightly for 5 consecutive runs
- ✅ VERDACA-E2E-03 green nightly for 7 consecutive runs, zero cost-event loss observed
- ✅ VERDACA-E2E-04 green on PR-gate (C-2 resolved)
- ✅ Dr. Quinn's 20-decision blind-rater benchmark completed with Spearman ρ ≥ 0.55 (closes A4; removes "(internal scoring)" caveat from headline)
- ✅ One Class-D MCP scenario added (Winston's ship-readiness gate)
- ✅ `_events` ring buffer bounded (Cleo WARNING #1 closed)
- ✅ Broad `except Exception` replaced with typed handlers (Cleo WARNING #2 closed)

**Until all 8 criteria are met, Verdaca is code-complete but not customer-ready.**

---

## Changelog

- **2026-04-17** — Initial E2E plan authored in party-mode session (Murat lead spec, Quinn runnable skeletons, Winston boundary review + 4th scenario). Status: design only — no tests implemented, no debt items closed.
