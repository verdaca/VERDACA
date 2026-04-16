# Praxis Stage 7.2 — POV Delivery Harness Test Strategy

**Stage:** Praxis 7.2 — Shell Test Strategy
**Author:** Murat (Master Test Architect)
**Date:** 2026-04-16
**Mode:** System-Level (architecture-driven)
**Status:** DRAFT v0.1 — pending team-lead spot-check and ratification

**Binding input:** `shell/architecture.md` — Winston 7.1 (1,019 lines, 17 sections, RATIFIED 2026-04-16)
**Pattern reference:** `mac/test-strategy.md` v0.3, `studio/test-strategy.md` (for naming conventions + gate structure)

---

## §1 — Scope and Stack

### §1.1 System Under Test

The POV Delivery Harness shell: Next.js frontend + FastAPI backend + Clerk auth + Stripe billing + Neon Postgres + 3 shell adapters (ShellCostAdapter, ShellMemoryAdapter, rendering-mode routing).

### §1.2 Test Stack

| Layer | Framework | Purpose |
|---|---|---|
| **Backend unit** | pytest + pytest-asyncio | FastAPI routes, adapters, models, tenant scoping |
| **Backend integration** | pytest + httpx (TestClient) | API endpoint integration, DB operations |
| **Frontend unit** | Vitest + React Testing Library | Component rendering, form validation |
| **E2E** | Playwright | Full signup→session→result flows |
| **Contract** | pytest (adapter contract tests) | C-2/C-3/C-4 adapter correctness against Pi-Mono/Memory contracts |

### §1.3 Coverage Gate

**Target: ≥75%** (Pipeline §7.4 requirement — lower than MAC's 94% because UI is iteratively tuned).

Backend Python code: ≥85% (adapters + routes are critical)
Frontend TypeScript: ≥65% (component tests + E2E cover the rest)

---

## §2 — Risk Assessment

### §2.1 Risk Matrix

| ID | Risk | Category | P | I | Score | Priority | Mitigation |
|---|---|---|---|---|---|---|---|
| R1 | **Billing errors (double-charge, incorrect amount)** | BUS | 2 | 3 | **6** | P1 | Stripe PaymentIntent idempotency + reconciliation test + Pi-Mono cost audit |
| R2 | **Cross-workspace data leakage** | SEC | 1 | 3 | **3** | P1 | TenantScopedSession + RLS + isolation tests |
| R3 | **C-2 adapter ULID mismatch** | TECH | 2 | 3 | **6** | P1 | Contract test: adapter output matches Pi-Mono ULID regex |
| R4 | **C-3 adapter shape violation** | TECH | 2 | 3 | **6** | P1 | Contract test: no usd_cost field on LLMResponse to Pi-Mono |
| R5 | **C-4 Memory facade method-name mismatch** | TECH | 2 | 3 | **6** | P1 | Contract test: verify promote_entries calls correct Memory facade method |
| R6 | **Session failure without refund** | BUS | 2 | 2 | **4** | P2 | Failed session test: no Stripe charge created |
| R7 | **Free trial consumed twice (race condition)** | BUS | 2 | 2 | **4** | P2 | DB constraint + idempotency test |
| R8 | **SSE connection leak** | PERF | 2 | 1 | **2** | P3 | Client disconnect test + connection cleanup |
| R9 | **Public dashboard exposes PII** | SEC | 1 | 3 | **3** | P1 | Aggregate-only test + minimum-threshold enforcement |
| R10 | **DL-15 mode routing broken** | TECH | 2 | 2 | **4** | P2 | Per-mode template routing test |
| R11 | **Clerk JWT validation bypass** | SEC | 1 | 3 | **3** | P1 | Unauthenticated request test on every protected endpoint |
| R12 | **Stripe webhook signature verification** | SEC | 1 | 3 | **3** | P1 | Invalid signature → 403 test |

### §2.2 P1 Risk Summary (score ≥ 3 AND impact = 3)

6 P1 risks: R1 (billing), R2 (isolation), R3 (C-2 ULID), R4 (C-3 shape), R5 (C-4 method), R9 (dashboard PII), R11 (auth bypass), R12 (webhook sig). All require dedicated test coverage with no-waiver enforcement.

---

## §3 — Testability Assessment

### §3.1 Controllability

| Area | Assessment | Notes |
|---|---|---|
| Auth (Clerk) | **Mock required** | Clerk JWT must be mocked in tests; use `clerk-sdk-python` test helpers or custom JWT factory |
| Billing (Stripe) | **Mock required** | Use `stripe-mock` Docker container or pytest fixtures with `stripe.PaymentIntent` stubs |
| Studio/MAC | **Fake required** | Reuse `studio/tests/fixtures/fake_mac.py` pattern; Studio returns canned SessionResult |
| Pi-Mono CostTracker | **Fake required** | Reuse `studio/tests/fixtures/fake_cost_tracker.py`; adapter wraps fake |
| Memory facade | **Fake required** | Stub `promote_task_entries()` to verify call signature (C-4 test) |
| Database | **Real Postgres** | Use testcontainers-python or Neon branch per test suite run |
| SSE | **httpx async streaming** | Test SSE endpoint via httpx `stream()` method |

### §3.2 Observability

- Sentry integration testable via `sentry_sdk.init(dsn="")` (noop mode)
- Pi-Mono cost events observable via fake tracker's `_events` list
- Session state transitions observable via DB queries in tests

### §3.3 Testability Concerns

1. **Clerk mocking complexity** — Clerk JWT validation requires JWKS endpoint mock. Recommendation: create a `FakeClerkProvider` that issues test JWTs with configurable workspace_id and role claims.
2. **Stripe webhook testing** — Webhook signature verification requires computing HMAC with the test webhook secret. Recommendation: create a `stripe_webhook_factory` fixture that produces correctly-signed payloads.
3. **SSE testing** — Standard httpx doesn't natively support SSE consumption. Recommendation: use `httpx_sse` library or raw async iteration on response stream.

---

## §4 — Test Catalog

### §4.1 Naming Convention

`SHELL-T-{AREA}-{TYPE}-{NN}` where:
- AREA: AUTH, BILL, ADAPT, TENANT, SESS, DASH, SSE, E2E
- TYPE: UNIT, INT, CONTRACT, E2E
- NN: sequential number

### §4.2 Adapter Contract Tests (P1 — debt blocker resolution verification)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-ADAPT-CONTRACT-01 | ShellCostAdapter.track_mac_call() produces LLMRequest with ULID-format request_id | R3 | PR |
| SHELL-T-ADAPT-CONTRACT-02 | ShellCostAdapter.track_mac_call() stashes MAC request_id in tags["mac_request_id"] | R3 | PR |
| SHELL-T-ADAPT-CONTRACT-03 | ShellCostAdapter.track_mac_call() produces LLMResponse with NO usd_cost field | R4 | PR |
| SHELL-T-ADAPT-CONTRACT-04 | ShellCostAdapter.track_mac_call() forwards only integer token counts | R4 | PR |
| SHELL-T-ADAPT-CONTRACT-05 | **ShellMemoryAdapter.promote_entries() calls Memory.promote_task_entries() with correct method name and signature** | R5 | PR |
| SHELL-T-ADAPT-CONTRACT-06 | ShellMemoryAdapter.promote_entries() passes workspace_id and task_signature | R5 | PR |
| SHELL-T-ADAPT-CONTRACT-07 | ShellCostAdapter produces CostRecord with correct session_id + workflow_id | R1 | PR |

### §4.3 Authentication Tests (P1)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-AUTH-UNIT-01 | Valid Clerk JWT → request proceeds with workspace_id extracted | R11 | PR |
| SHELL-T-AUTH-UNIT-02 | Missing JWT → 401 on all /api/ endpoints | R11 | PR |
| SHELL-T-AUTH-UNIT-03 | Expired JWT → 401 | R11 | PR |
| SHELL-T-AUTH-UNIT-04 | JWT for workspace A → cannot access workspace B sessions | R2 | PR |
| SHELL-T-AUTH-UNIT-05 | Viewer role → cannot create sessions (403) | R11 | PR |
| SHELL-T-AUTH-UNIT-06 | Member role → can create sessions, cannot manage billing | R11 | PR |

### §4.4 Billing Tests (P1/P2)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-BILL-UNIT-01 | Free trial → session starts without Stripe charge | R1 | PR |
| SHELL-T-BILL-UNIT-02 | Trial already consumed → Stripe PaymentIntent created | R1 | PR |
| SHELL-T-BILL-UNIT-03 | Quick session → PaymentIntent amount = 2900 cents | R1 | PR |
| SHELL-T-BILL-UNIT-04 | Deep session → PaymentIntent amount = 14900 cents | R1 | PR |
| SHELL-T-BILL-UNIT-05 | PaymentIntent failure → session NOT started, error returned | R6 | PR |
| SHELL-T-BILL-UNIT-06 | Trial consumed twice (concurrent requests) → only 1 free session (DB constraint) | R7 | PR |
| SHELL-T-BILL-INT-01 | Stripe webhook (payment_intent.succeeded) → session record updated | R1 | PR |
| SHELL-T-BILL-INT-02 | Stripe webhook with invalid signature → 403 | R12 | PR |
| SHELL-T-BILL-INT-03 | Session fails mid-run → no Stripe charge created | R6 | PR |

### §4.5 Tenant Isolation Tests (P1)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-TENANT-UNIT-01 | TenantScopedSession injects workspace_id on every query | R2 | PR |
| SHELL-T-TENANT-UNIT-02 | Direct session query without TenantScopedSession → test rejects | R2 | PR |
| SHELL-T-TENANT-INT-01 | Create sessions in workspace A + B → GET /sessions in A returns only A's sessions | R2 | PR |
| SHELL-T-TENANT-INT-02 | GET /sessions/:id with workspace B JWT for workspace A session → 404 | R2 | PR |
| SHELL-T-TENANT-INT-03 | Public dashboard /api/public/stats → no workspace_id, no question text in response | R9 | PR |

### §4.6 Session Lifecycle Tests (P2)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-SESS-UNIT-01 | CreateSessionRequest validation: question min 20 chars | — | PR |
| SHELL-T-SESS-UNIT-02 | CreateSessionRequest validation: question max 10000 chars | — | PR |
| SHELL-T-SESS-UNIT-03 | Session state: PENDING → RUNNING → COMPLETED | — | PR |
| SHELL-T-SESS-UNIT-04 | Session state: PENDING → RUNNING → FAILED | — | PR |
| SHELL-T-SESS-UNIT-05 | rendering_mode defaults to position_to_hold | R10 | PR |
| SHELL-T-SESS-INT-01 | POST /api/sessions → session created, background task enqueued | — | PR |
| SHELL-T-SESS-INT-02 | GET /api/sessions/:id → completed session returns result_markdown + result_html | — | PR |
| SHELL-T-SESS-INT-03 | GET /api/sessions → paginated list for workspace | — | PR |

### §4.7 Rendering Mode Tests (DL-15 — P2)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-SESS-UNIT-06 | rendering_mode=position_to_hold → Studio invoked with POSITION_TO_HOLD | R10 | PR |
| SHELL-T-SESS-UNIT-07 | rendering_mode=decision_framework → Studio invoked with DECISION_FRAMEWORK | R10 | PR |
| SHELL-T-SESS-UNIT-08 | rendering_mode=firm_voice → Studio invoked with FIRM_VOICE | R10 | PR |

### §4.8 Public Dashboard Tests (P1)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-DASH-UNIT-01 | GET /api/public/stats → returns aggregate metrics only | R9 | PR |
| SHELL-T-DASH-UNIT-02 | <10 sessions → response includes "insufficient_data" flag | R9 | PR |
| SHELL-T-DASH-UNIT-03 | No question content, workspace names, or user IDs in response | R9 | PR |

### §4.9 SSE Streaming Tests (P3)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-SSE-INT-01 | GET /api/sessions/:id/stream → receives cycle_start, cost_update, complete events | R8 | Nightly |
| SHELL-T-SSE-INT-02 | Client disconnects SSE → server cleans up, no resource leak | R8 | Nightly |
| SHELL-T-SSE-INT-03 | Unauthenticated SSE request → 401 | R11 | PR |

### §4.10 E2E Tests (Playwright)

| ID | Test | Risk | Gate |
|---|---|---|---|
| SHELL-T-E2E-01 | **Golden path:** Landing → signup (OAuth mock) → workspace → free trial session → result displayed | R1, R11 | Nightly |
| SHELL-T-E2E-02 | **Paid session:** Trial consumed → Stripe Checkout (mock) → paid deep session → result | R1 | Nightly |
| SHELL-T-E2E-03 | **Mode routing:** Submit with decision_framework mode → correct template in output | R10 | Nightly |
| SHELL-T-E2E-04 | **Public dashboard:** Navigate to /dashboard → metrics visible, no PII | R9 | Nightly |
| SHELL-T-E2E-05 | **Error handling:** Session fails → error message displayed, no charge | R6 | Nightly |

---

## §5 — Test Fixture Architecture

### §5.1 Core Fixtures

```python
# shell/tests/conftest.py

@pytest.fixture
def fake_clerk() -> FakeClerkProvider:
    """Issues test JWTs with configurable workspace_id and role."""
    return FakeClerkProvider(secret="test-secret")

@pytest.fixture
def fake_stripe() -> FakeStripeClient:
    """Stubs PaymentIntent creation with configurable success/failure."""
    return FakeStripeClient()

@pytest.fixture
def fake_studio() -> FakeStudioSession:
    """Returns canned SessionResult without running MAC."""
    return FakeStudioSession()

@pytest.fixture
def fake_cost_tracker() -> FakeCostTracker:
    """Records track_cost calls for assertion. From studio/tests pattern."""
    return FakeCostTracker()

@pytest.fixture
def fake_memory() -> FakeMemoryFacade:
    """Records promote_task_entries calls for C-4 contract verification."""
    return FakeMemoryFacade()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Real Postgres via testcontainers or Neon branch."""
    ...

@pytest.fixture
def cost_adapter(fake_cost_tracker) -> ShellCostAdapter:
    return ShellCostAdapter(tracker=fake_cost_tracker)

@pytest.fixture
def memory_adapter(fake_memory) -> ShellMemoryAdapter:
    return ShellMemoryAdapter(memory=fake_memory)

@pytest.fixture
def auth_headers(fake_clerk) -> dict:
    """JWT headers for default test workspace."""
    return {"Authorization": f"Bearer {fake_clerk.issue_jwt(workspace_id='ws-test-1', role='owner')}"}
```

### §5.2 FakeMemoryFacade (C-4 Contract Verification)

```python
class FakeMemoryFacade:
    """Captures calls to promote_task_entries for contract assertion.
    
    The REAL Memory facade exposes promote_task_entries() per Memory §6.6:914.
    This fake verifies that ShellMemoryAdapter calls the correct method name
    with the correct signature — the C-4 debt resolution correctness check.
    """
    
    def __init__(self):
        self.promote_calls: list[dict] = []
    
    async def promote_task_entries(
        self,
        workspace_id: str,
        task_signature: str,
        confirmation_source: str,
    ) -> None:
        self.promote_calls.append({
            "workspace_id": workspace_id,
            "task_signature": task_signature,
            "confirmation_source": confirmation_source,
        })
```

---

## §6 — Quality Gates

### §6.1 PR Gate (blocks merge)

- All SHELL-T-*-*-* tests with Gate=PR pass
- Coverage ≥ 75% overall (85% backend, 65% frontend)
- Zero P1 risk tests failing
- Adapter contract tests (SHELL-T-ADAPT-CONTRACT-01..07) all pass
- Auth tests (SHELL-T-AUTH-UNIT-01..06) all pass
- Billing tests (SHELL-T-BILL-*) all pass
- Tenant isolation tests (SHELL-T-TENANT-*) all pass

### §6.2 Nightly Gate (blocks release)

- All PR gate tests pass
- E2E tests (SHELL-T-E2E-01..05) pass
- SSE streaming tests pass
- Full Playwright suite green

### §6.3 Release Gate

- All nightly tests green for 3 consecutive runs
- A4 Spearman validation complete (ρ ≥ 0.6 or explicit team-lead disposition)
- Manual spot-check: signup → first result in <10 minutes (timed)

---

## §7 — Test Count Summary

| Category | Count | Gate |
|---|---|---|
| Adapter contract | 7 | PR |
| Auth | 6 | PR |
| Billing | 9 | PR |
| Tenant isolation | 5 | PR |
| Session lifecycle | 8 | PR |
| Rendering mode (DL-15) | 3 | PR |
| Public dashboard | 3 | PR |
| SSE streaming | 3 | Nightly |
| E2E (Playwright) | 5 | Nightly |
| **Total** | **49** | |

PR-gate: 41 tests
Nightly-gate: 49 tests (41 PR + 8 nightly)

---

## §8 — Frozen Artifact Discipline

- **MAC tests untouched:** `mac/tests/` baseline `211 passed, 30 skipped` must be preserved
- **Studio tests untouched:** `studio/tests/` baseline `97 passed, 19 deselected` must be preserved
- **Shell tests are additive:** all new tests live in `shell/tests/`
- **No cross-stage test imports:** shell tests do NOT import from `mac/tests/` or `studio/tests/`; they create their own fakes following the same patterns

---

## §9 — Session-Close Audit

### §9.1 Deliverable Metrics

| Metric | Value |
|---|---|
| Total document lines | (see wc -l) |
| Sections | 9 (§1–§9) |
| Total test IDs | 49 |
| Risk items | 12 (6 P1, 3 P2, 3 P3) |
| Adapter contract tests | 7 (C-2: 2, C-3: 2, C-4: 2, cost tracking: 1) |
| C-4 Memory facade method-name test | SHELL-T-ADAPT-CONTRACT-05 (team-lead flagged) |

### §9.2 Constraint Compliance

- **Coverage gate ≥ 75%:** Defined in §6.1 (85% backend, 65% frontend, 75% overall)
- **E2E: signup → billing → Studio session → result:** SHELL-T-E2E-01 + SHELL-T-E2E-02
- **Workspace isolation verified:** SHELL-T-TENANT-*-01..03
- **MAC test baseline preserved:** §8 frozen artifact discipline
- **Studio test baseline preserved:** §8 frozen artifact discipline
- **Memory writes:** NONE
- **Pipeline marks:** NONE

---

_Test strategy crafted as Murat, Master Test Architect — Stage 7.2 Praxis POV Delivery Harness_
