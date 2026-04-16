# PRAXIS STAGE 8: Production Hardening + Deployment

**Date:** 2026-04-16
**Supplements:** `docs/pipeline.md` (master orchestration, Stages 1-7), `shell/alignment-review.md` (19-item debt ledger)
**Purpose:** Everything needed to go from "code works locally" to "customers can use it in production." This is the IMPLEMENTATION pipeline -- not a plan, but a build checklist.

**Repo structure (post-Stage 7 restructure):**
```
praxis/
├── kernel/
│   ├── pi-mono/          # Stage 1 — measurement
│   ├── compression/      # Stage 2 — TONL + Forge + RTK + Caveman
│   ├── memory/           # Stage 3 — Beads + Mem0 + Atelier
│   ├── runtime/          # Stage 4 — agent loader + spawner + MCP
│   ├── mac/              # Stage 5 — Meta-Agent Controller
│   └── studio/           # Stage 6 — workflow template engine
├── shell/                # Stage 7 — Next.js + FastAPI web app
└── docs/                 # documentation (including this file)
```

---

## FRESH SESSION BOOTSTRAP

If you are a new Claude session seeing this file for the first time:

1. **Read `docs/pipeline.md` Section 3** — confirm ALL Stages 1-7 are `[x]`
2. **Read this file's Status Tracker (Section 2)** — find last completed item, identify NEXT incomplete item
3. **Verify repo structure** — `kernel/` has 6 packages, `shell/` has Next.js + FastAPI, `docs/` exists
4. **Verify billing mode** — `echo $ANTHROPIC_API_KEY` must be empty (Max billing)
5. **Do not skip sub-stages.** 8.1 through 8.8 are mostly sequential with explicit parallelization notes

---

## SECTION 1: DEPENDENCY FLOW

```
                    ┌────────────────────────────────┐
                    │ 8.1 Deployment Infrastructure  │
                    │ (Docker, CI/CD, DB, hosting)   │
                    └──────────┬─────────────────────┘
                               │
                    ┌──────────┴─────────────────────┐
                    │                                 │
                    ▼                                 ▼
     ┌──────────────────────────┐   ┌──────────────────────────┐
     │ 8.2 Debt Ledger          │   │ 8.4 Monorepo Tooling     │
     │ (19 carried items)       │   │ (uv workspace, hooks)    │
     │ Needs: 8.1 for CI/CD    │   │ Needs: 8.1 for CI config │
     └──────────┬───────────────┘   └──────────┬───────────────┘
                │                               │
                ▼                               │
     ┌──────────────────────────┐               │
     │ 8.3 Production Wiring   │◄──────────────┘
     │ (replace all fakes)     │
     │ Needs: 8.1 + 8.2        │
     └──────────┬───────────────┘
                │
                ▼
     ┌──────────────────────────┐
     │ 8.6 Observability       │
     │ (Sentry, analytics,     │
     │  health checks)         │
     │ Needs: 8.3              │
     └──────────┬───────────────┘
                │
     ┌──────────┴─────────────────────┐
     │                                 │
     ▼                                 ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│ 8.7 A4 Human Validation  │   │ 8.5 Credit Packs +       │
│ (Spearman scoring)       │   │ Enterprise Features      │
│ Needs: 8.3 (real calls)  │   │ Needs: 8.3 (real Stripe) │
│ PARALLEL with 8.5/8.8    │   │ DEFERRED until triggers  │
└──────────┬───────────────┘   └───────────────────────────┘
           │
           ▼
     ┌──────────────────────────┐
     │ 8.8 Launch              │
     │ (DNS, SSL, outreach)    │
     │ Needs: 8.1-8.4, 8.6    │
     │ 8.7 PASS recommended    │
     └─────────────────────────┘
```

**Parallelization notes:**
- 8.2 (Debt Ledger) and 8.4 (Monorepo Tooling) can run in parallel after 8.1
- 8.5 (Credit Packs + Enterprise) is event-triggered, not sequenced -- build when conditions are met
- 8.7 (A4 Validation) can run as soon as 8.3 delivers real `LLMJudgeClient.call_live()`
- 8.8 (Launch) requires 8.1 + 8.3 + 8.6 at minimum; 8.7 PASS strongly recommended before first outreach

---

## SECTION 2: STATUS TRACKER

**Legend:** `[ ]` not started  |  `[~]` in progress  |  `[x]` complete  |  `[!]` blocked

### Pre-Flight Checks (Before Any 8.x Work)

- [ ] Stages 1-7 ALL `[x]` in `docs/pipeline.md` Section 3
- [ ] Repo restructured to `kernel/` + `shell/` + `docs/` layout
- [ ] `ANTHROPIC_API_KEY` unset (Max billing confirmed)
- [ ] 19-item debt ledger reviewed from `shell/alignment-review.md` Section 6
- [ ] Domain name secured (praxis.ai or equivalent)
- [ ] GitHub repo created (or existing repo cleaned for production)
- [ ] Neon Postgres account provisioned (free tier to start)
- [ ] Clerk account provisioned (free tier to start)
- [ ] Stripe account provisioned (test mode)
- [ ] Vercel account provisioned (free tier to start)

---

### 8.1 — Deployment Infrastructure

**Goal:** Production hosting for backend + frontend + database. CI/CD pipeline. Zero manual deploys after this stage.

**Assigned agents:** Winston (architecture decisions), Amelia (implementation)
**Model:** Sonnet 4.6 [1M] (Amelia) / Opus 4.6 (Winston for infra ADRs)

#### 8.1.1 — Dockerfile for FastAPI Backend

- [ ] **Winston: Infra ADR** — containerization strategy
  - [ ] Multi-stage Dockerfile (build + runtime layers)
  - [ ] Python 3.11+ slim base image
  - [ ] Non-root user, health check instruction
  - [ ] `.dockerignore` (exclude tests, docs, node_modules, .git)
  - [ ] Decision: Railway vs ECS Fargate vs Fly.io for backend hosting
  - [ ] Output: `docs/adr-infra-01-backend-hosting.md`

- [ ] **Amelia: Implement Dockerfile**
  - [ ] `Dockerfile` at repo root (backend)
  - [ ] `docker-compose.yml` for local dev (Postgres + backend + frontend)
  - [ ] Backend runs on port 8000, Postgres on 5432, frontend on 3000
  - [ ] Alembic migrations run automatically on container startup
  - [ ] Health check endpoint `/api/health` returns 200

#### 8.1.2 — Database (Neon Postgres + Alembic)

- [ ] **Amelia: Database setup**
  - [ ] Neon Postgres project created (production branch + dev branch)
  - [ ] Alembic initialized in `shell/api/migrations/`
  - [ ] Migration 0001: `workspaces` table (from shell/architecture.md)
  - [ ] Migration 0002: `sessions` table (from shell/architecture.md)
  - [ ] Migration 0003: `mac_bootstrap_metadata` sidecar table (from mac/architecture.md Option Y)
  - [ ] Migration 0004: `jobs_queue` table (from runtime/architecture.md F-3)
  - [ ] Migration 0005: `events_outbox` table (from runtime/architecture.md F-1)
  - [ ] `alembic upgrade head` succeeds on clean Neon instance
  - [ ] `alembic downgrade -1` succeeds for each migration (reversibility)
  - [ ] Connection string via `DATABASE_URL` environment variable

#### 8.1.3 — Frontend Deployment (Vercel)

- [ ] **Amelia: Vercel config**
  - [ ] `vercel.json` at `shell/frontend/` root
  - [ ] Build command: `npm run build` (Next.js)
  - [ ] Environment variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  - [ ] Preview deployments on PR branches
  - [ ] Production deployment on `main` branch push
  - [ ] Custom domain wired (if domain secured)

#### 8.1.4 — Backend Deployment

- [ ] **Amelia: Backend hosting** (per Winston's ADR)
  - [ ] Deployment config for chosen platform (Railway `railway.toml` OR ECS task definition OR `fly.toml`)
  - [ ] Auto-deploy on `main` branch push
  - [ ] Environment variables provisioned: `DATABASE_URL`, `CLERK_SECRET_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY` (production only), `SENTRY_DSN`
  - [ ] Minimum 1 instance, auto-scale to 3 on load
  - [ ] 512MB RAM minimum (MAC deliberation is memory-intensive)

#### 8.1.5 — Environment Variable Management

- [ ] **Amelia: Env var strategy**
  - [ ] `.env.example` at repo root with ALL required variables (no values)
  - [ ] `.env.local` in `.gitignore`
  - [ ] Deployment platform secret management (Railway secrets / Vercel env vars / AWS SSM)
  - [ ] Validation on app startup: crash immediately if required vars missing
  - [ ] No secrets in Docker images, Dockerfiles, or committed files

#### 8.1.6 — CI/CD with GitHub Actions

- [ ] **Amelia: GitHub Actions workflows**
  - [ ] `.github/workflows/ci.yml` — runs on every PR:
    - [ ] `ruff check` + `ruff format --check` (all kernel packages + shell)
    - [ ] `mypy` type check (strict mode)
    - [ ] `pytest` PR-gate tests (all 6 kernel packages + shell backend)
    - [ ] Frontend: `npm run lint` + `npm run build`
    - [ ] Coverage gate: fail if any package drops below its ratified floor (Pi-Mono 79%, Compression 94%, Memory 98%, Runtime 97%, MAC 94%, Studio 96%, Shell 92%)
  - [ ] `.github/workflows/nightly.yml` — runs nightly at 03:00 UTC:
    - [ ] Full test suite including `--run-nightly` tests
    - [ ] Cross-stage drift canaries
    - [ ] Dependency vulnerability scan (`pip-audit`)
  - [ ] `.github/workflows/deploy.yml` — runs on merge to `main`:
    - [ ] Backend deploy (Railway/ECS/Fly)
    - [ ] Frontend deploy (Vercel -- auto via Vercel Git integration)
    - [ ] Alembic migration auto-run post-deploy
  - [ ] Branch protection: require CI pass before merge to `main`

**Gate 8.1 complete:** Docker Compose `docker compose up` starts full stack locally. CI pipeline runs on PR. Deploy pipeline pushes to production. Alembic migrations succeed against Neon.

---

### 8.2 — Debt Ledger Resolution (19 Items from Stages 5-7)

**Goal:** Close every carried-forward item. Zero technical debt entering production.

**Assigned agents:** Amelia (implementation), Cleo (review each batch), Murat (test strategy for non-trivial items)
**Model:** Sonnet 4.6 (Amelia) / Sonnet 4.6 (Cleo)

**Rule:** Each item is resolved via a dedicated commit. No bundling unrelated fixes. Each fix includes a test proving the fix and a regression test proving no breakage.

#### 8.2.1 — MAC Cleo WARNINGs (5 items, from Stage 5.3.5)

- [ ] **W-2: Unbounded `_events` list**
  - [ ] Add max-size ring buffer or periodic flush to `_events` accumulator
  - [ ] Test: verify events are bounded under sustained load (property test)
  - [ ] Commit: `fix(mac): bound _events list to prevent memory leak (W-2)`

- [ ] **W-3: Broad `except ValueError`**
  - [ ] Narrow exception handling to specific exception types
  - [ ] Test: verify correct exceptions are caught and incorrect ones propagate
  - [ ] Commit: `fix(mac): narrow except ValueError to specific types (W-3)`

- [ ] **W-4: Misleading synthesized `raw_score`**
  - [ ] Replace placeholder raw_score with actual scoring output or explicit sentinel
  - [ ] Test: verify raw_score is meaningful when scoring runs and sentinel when not
  - [ ] Commit: `fix(mac): replace synthesized raw_score with actual/sentinel (W-4)`

- [ ] **W-5: Hardcoded `manufactured_dissent_detected=False`**
  - [ ] Wire actual dissent detection logic from MAC 3-cycle output
  - [ ] Test: verify dissent detection returns True when genuine dissent exists in Cycle A
  - [ ] Commit: `fix(mac): wire manufactured_dissent_detected to actual detection (W-5)`

- [ ] **W-7: `Any`-typed `HybridScoringHarness` callables**
  - [ ] Add proper `Protocol` or `Callable[[...], ...]` type annotations
  - [ ] Test: mypy strict check passes on `HybridScoringHarness`
  - [ ] Commit: `fix(mac): type HybridScoringHarness callables (W-7)`

#### 8.2.2 — Studio Cleo WARNINGs (4 items, from Stage 6.3.5)

- [ ] **W-1: Broad `except` in Studio workflow engine**
  - [ ] Narrow to specific exception types (same pattern as MAC W-3)
  - [ ] Commit: `fix(studio): narrow broad except to specific types (W-1)`

- [ ] **W-2: Renderer `Any` type**
  - [ ] Add proper `Protocol` for renderer interface
  - [ ] Commit: `fix(studio): type renderer interface with Protocol (W-2)`

- [ ] **W-3: Deferred imports in Studio**
  - [ ] Move imports to top-level or document why deferred (circular dependency? lazy load?)
  - [ ] Commit: `fix(studio): resolve deferred imports (W-3)`

- [ ] **W-4: Silent empty fallback**
  - [ ] Add explicit logging or raise on empty fallback conditions
  - [ ] Commit: `fix(studio): add explicit handling for empty fallback (W-4)`

#### 8.2.3 — Cross-Stage Contradictions (2 items, from Stage 5.5)

- [ ] **C-1: Compression class name drift (`Compressor` vs `CompressionLayer`)**
  - [ ] Audit: grep all references in arch docs + source code
  - [ ] Pick canonical name, rename all references
  - [ ] Test: import test confirms canonical name resolves; old name raises ImportError or DeprecationWarning
  - [ ] Commit: `refactor(compression): unify class name to {canonical} (C-1)`

- [ ] **C-5: Runtime spawner method drift (`spawn` vs `spawn_subagent`)**
  - [ ] Audit: grep all references in arch docs + source code
  - [ ] Pick canonical name, rename all references
  - [ ] Test: import test confirms canonical method name resolves
  - [ ] Commit: `refactor(runtime): unify spawner method name to {canonical} (C-5)`

#### 8.2.4 — Protocol Rename (1 item, from Stage 6.5)

- [ ] **DL-14: `CostTrackerProtocol` rename to `MetricsSinkProtocol`**
  - [ ] Rename across all packages that reference it (pi-mono, shell, studio)
  - [ ] Test: mypy passes, all existing tests pass
  - [ ] Commit: `refactor(kernel): rename CostTrackerProtocol to MetricsSinkProtocol (DL-14)`

#### 8.2.5 — Deferred Feature (1 item, from Stage 6.0.3)

- [ ] **ADR-08: PDF/pptx export**
  - [ ] Implement PDF export via `weasyprint` or `pdfkit` (Markdown/HTML to PDF)
  - [ ] Implement `.pptx` export via `python-pptx` (deck rendering mode only)
  - [ ] Wire to Studio output rendering pipeline
  - [ ] Test: PDF export produces valid PDF with correct content; pptx export produces valid PowerPoint
  - [ ] Commit: `feat(studio): add PDF and pptx export (ADR-08)`

#### 8.2.6 — Shell Cleo WARNINGs (7 items, from Stage 7.3.5)

These were ACCEPT AS-IS at Quinn 7.4 but should be cleaned before production:

- [ ] **W-1/W-2: Unused imports in `sessions.py` and `main.py`**
  - [ ] Remove unused imports or wire placeholder code
  - [ ] Commit: `fix(shell): remove unused imports (W-1/W-2)`

- [ ] **W-3: Lazy imports in `public.py`**
  - [ ] Move to top-level or document reason
  - [ ] Commit: `fix(shell): resolve lazy imports in public.py (W-3)`

- [ ] **W-4: Weak type hints in `_is_today`**
  - [ ] Strengthen type annotations
  - [ ] Commit: `fix(shell): strengthen type hints (W-4)`

- [ ] **W-5: `db.py` Numeric/float mismatch**
  - [ ] Align DB column type with Python type (Decimal throughout, per Pi-Mono precedent)
  - [ ] Commit: `fix(shell): align Numeric/Decimal types in db.py (W-5)`

- [ ] **W-6: Placeholder route handlers**
  - [ ] Wire to real implementations or mark as `501 Not Implemented` with explicit TODO
  - [ ] Commit: `fix(shell): wire or mark placeholder routes (W-6)`

- [ ] **W-7: Missing return type annotations**
  - [ ] Add return types to all route handlers
  - [ ] Commit: `fix(shell): add return type annotations (W-7)`

#### 8.2.7 — A4 Spearman Validation (see 8.7 for full protocol)

- [ ] **A4 deferred from Stage 5.6** — handled in 8.7 sub-stage below

**Cleo review of all 8.2 changes:**
- [ ] Cleo runs `/bmad-code-review` across all 8.2 commits
- [ ] 0 CRITICAL violations
- [ ] All WARNING items resolved or explicitly documented

**Gate 8.2 complete:** Debt ledger = 0 items. All carried WARNINGs resolved. All cross-stage contradictions unified. All renames propagated. PDF/pptx export functional. CI pipeline green.

---

### 8.3 — Production Wiring (Replace All Fakes)

**Goal:** Every `Fake*` class in the codebase is replaced with a real implementation. The app works against real external services.

**Assigned agents:** Winston (integration architecture decisions), Amelia (implementation), Murat (integration test strategy)
**Model:** Opus 4.6 [1M] (Winston — cross-stage integration is high-context), Sonnet 4.6 [1M] (Amelia), Opus 4.6 (Murat)

**Rule:** Each fake replacement is a separate PR. Tests run against both fake (unit) and real (integration, gated by env var) implementations. The `Fake*` classes are NOT deleted -- they remain as test doubles.

#### 8.3.1 — Wire Real Pi-Mono CostTracker

- [ ] **Winston: Integration ADR** — how Pi-Mono connects to Anthropic billing API
  - [ ] Decision: poll vs webhook for cost reconciliation
  - [ ] Decision: local accumulation period before DB write (batch vs per-request)
- [ ] **Amelia: Replace `FakeCostTracker`**
  - [ ] `ShellCostAdapter` (from Stage 7) wired to real Pi-Mono `CostTracker`
  - [ ] Real Anthropic `usage` response fields parsed into `CostEvent`
  - [ ] Per-session cost accumulation writes to `sessions.total_cost_usd`
  - [ ] Test: integration test with real Anthropic API call (env-gated: `PRAXIS_INTEGRATION_TESTS=1`)
  - [ ] Test: unit test with `FakeCostTracker` still passes
  - [ ] Commit: `feat(shell): wire real Pi-Mono CostTracker`

#### 8.3.2 — Wire Real Memory Facade

- [ ] **Amelia: Replace `FakeMemory`**
  - [ ] Real `Memory` facade from kernel/memory connected to Neon Postgres + pgvector
  - [ ] Beads store wired to filesystem or object storage (S3/R2)
  - [ ] Mem0 backend configured with real pgvector connection
  - [ ] Atelier decision store wired to Postgres
  - [ ] Tenant scoping enforced via real workspace_id (not fake ULIDs)
  - [ ] Test: integration test stores and retrieves a real memory entry
  - [ ] Test: cross-tenant isolation test (workspace A cannot see workspace B memories)
  - [ ] Commit: `feat(shell): wire real Memory facade with Postgres + pgvector`

#### 8.3.3 — Wire Real Studio Session

- [ ] **Amelia: Replace `FakeStudio`**
  - [ ] Real `Studio.invoke()` calls real MAC `MetaAgentController.deliberate()`
  - [ ] Real Jinja2 template rendering produces actual brief/deck/exec_summary
  - [ ] Real quality gate scoring via R1-R12 rubric
  - [ ] Real register-check (ADR-11) enforces muted operator-realism
  - [ ] Test: E2E test runs a real question through the full pipeline (env-gated)
  - [ ] Test: output format matches ADR-01 four-feature backbone
  - [ ] Commit: `feat(shell): wire real Studio session pipeline`

#### 8.3.4 — Wire Real Clerk JWT Validation

- [ ] **Amelia: Replace `FakeClerkProvider`**
  - [ ] Clerk SDK installed (`clerk-backend-api`)
  - [ ] JWT validation middleware on all `/api/sessions/*` routes
  - [ ] User info extracted from JWT claims: `user_id`, `email`, `workspace_id`
  - [ ] Webhook endpoint for Clerk `user.created` / `user.deleted` events
  - [ ] Test: integration test with real Clerk JWT (env-gated)
  - [ ] Test: unit test with `FakeClerkProvider` still passes (JWT mocked)
  - [ ] Commit: `feat(shell): wire real Clerk JWT validation`

#### 8.3.5 — Wire Real Stripe

- [ ] **Amelia: Replace `FakeStripeClient`**
  - [ ] Stripe SDK installed (`stripe`)
  - [ ] Checkout session creation for paid sessions ($29 quick / $149 deep per Victor 7.0.1)
  - [ ] Webhook endpoint for `checkout.session.completed` → mark session as paid
  - [ ] Webhook endpoint for `charge.refunded` → handle refund state
  - [ ] Usage metering: Pi-Mono cost per session logged to Stripe usage records (for future gain-share reporting)
  - [ ] Test: integration test with Stripe test mode (env-gated)
  - [ ] Test: webhook signature validation test
  - [ ] Commit: `feat(shell): wire real Stripe billing`

#### 8.3.6 — Database-Backed Session Storage

- [ ] **Amelia: Replace in-memory dicts**
  - [ ] `SessionStore` writes to Neon Postgres `sessions` table via SQLAlchemy async
  - [ ] `WorkspaceStore` writes to `workspaces` table
  - [ ] Connection pooling: `pool_size=10, max_overflow=15, pool_pre_ping=True` (per Memory NR-SC-R2 precedent)
  - [ ] Query optimization: index on `workspace_id` + `created_at` for session listing
  - [ ] Test: CRUD operations against real Postgres (env-gated)
  - [ ] Test: concurrent session creation stress test
  - [ ] Commit: `feat(shell): database-backed session storage`

#### 8.3.7 — SSE Streaming with Real Events

- [ ] **Amelia: Replace placeholder SSE**
  - [ ] Real SSE events from MAC deliberation cycle:
    - `cycle_start` (cycle number, phase name)
    - `agent_spawned` (agent name, role)
    - `gate_result` (gate ID, score, pass/fail)
    - `cycle_complete` (cycle number, summary)
    - `rendering` (output type, progress)
    - `complete` (session ID, result URL)
  - [ ] Backpressure handling: if client disconnects, cancel MAC execution
  - [ ] Reconnection: client can resume SSE stream via `Last-Event-ID` header
  - [ ] Test: SSE event sequence test (correct order, correct payloads)
  - [ ] Commit: `feat(shell): real SSE streaming from MAC deliberation`

**Murat: Integration test strategy for 8.3**
- [ ] Test strategy doc at `docs/test-strategy-8.3-integration.md`
- [ ] Env-gated integration test suite: `pytest -m integration` (requires real credentials)
- [ ] Contract tests: each adapter Protocol still satisfied by both Fake and Real implementations
- [ ] Smoke test script: `scripts/smoke_test_production.py` — hits real endpoints, verifies 200s

**Gate 8.3 complete:** Zero `Fake*` classes used in production code path. All fakes retained as test doubles. Integration tests pass against real Neon + Clerk + Stripe + Anthropic. Full E2E: real user signs up via Clerk, pays via Stripe, runs a real MAC deliberation, gets a real rendered output, cost tracked via real Pi-Mono.

---

### 8.4 — Monorepo Tooling

**Goal:** Single-command build, test, and lint for all 6 kernel packages + shell. Developer experience: `uv run pytest` from repo root runs everything.

**Assigned agents:** Amelia (implementation)
**Model:** Sonnet 4.6 (straightforward tooling)

#### 8.4.1 — Root `pyproject.toml` with `uv` Workspace

- [ ] Root `pyproject.toml` declaring workspace members:
  ```
  [tool.uv.workspace]
  members = [
    "kernel/pi-mono",
    "kernel/compression",
    "kernel/memory",
    "kernel/runtime",
    "kernel/mac",
    "kernel/studio",
    "shell",
  ]
  ```
- [ ] Each package has its own `pyproject.toml` with local path dependencies
- [ ] `uv sync` from root installs all packages in editable mode
- [ ] `uv run pytest` from root discovers and runs all tests
- [ ] Commit: `feat(repo): add uv workspace root pyproject.toml`

#### 8.4.2 — Shared Dev Dependencies

- [ ] Root `pyproject.toml` dev dependencies:
  - `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist`
  - `ruff` (linting + formatting)
  - `mypy` (type checking)
  - `pip-audit` (vulnerability scanning)
  - `hypothesis` (property-based testing)
- [ ] Version pins aligned across all packages (no dependency conflicts)
- [ ] Commit: `feat(repo): shared dev dependencies in root pyproject.toml`

#### 8.4.3 — Cross-Module Test Runner

- [ ] `scripts/test_all.sh` — runs all packages with coverage:
  ```bash
  uv run pytest kernel/ shell/ --cov --cov-report=term-missing --cov-fail-under=80
  ```
- [ ] `scripts/test_pr.sh` — PR-gate tests only (excludes nightly + release tiers)
- [ ] `scripts/test_nightly.sh` — full suite including `--run-nightly`
- [ ] Coverage floors enforced per package (not just aggregate)
- [ ] Commit: `feat(repo): cross-module test runner scripts`

#### 8.4.4 — Pre-Commit Hooks

- [ ] `.pre-commit-config.yaml`:
  - `ruff check --fix` (auto-fix safe lint issues)
  - `ruff format` (formatting)
  - `mypy` (type check, cached for speed)
  - NR-S-R1 `_internal` import guard (grep tripwire from Stage 3)
  - No-secrets check (`detect-secrets` or `gitleaks`)
- [ ] `pre-commit install` documented in README
- [ ] Commit: `feat(repo): pre-commit hooks configuration`

**Gate 8.4 complete:** `uv sync && uv run pytest` from repo root succeeds. Pre-commit hooks catch issues before commit. CI uses same test runner as local dev. No package version conflicts.

---

### 8.5 — Credit Packs + Enterprise Features (Event-Triggered)

**Goal:** Revenue diversification beyond per-session pricing. Build ONLY when trigger conditions are met.

**Assigned agents:** Victor (business strategy validation), Winston (architecture), Amelia (implementation)
**Model:** Opus 4.6 (Victor/Winston) / Sonnet 4.6 (Amelia)

**IMPORTANT:** This sub-stage is NOT sequenced. Items are built when their trigger fires, not on a schedule. Track triggers here; implement when conditions are met.

#### 8.5.1 — Credit Pack Billing

- [ ] **Trigger:** 3+ customers have completed 5+ sessions each
- [ ] **Victor: Validate credit pack pricing** — `/bmad-cis-innovation-strategy`
  - [ ] Credit pack tiers (e.g., 10 sessions at 15% discount, 25 sessions at 25% discount)
  - [ ] Expiration policy (90 days? 180 days? never?)
  - [ ] Partial credit usage (1 quick = 1 credit, 1 deep = 5 credits?)
- [ ] **Winston: Credit pack architecture**
  - [ ] `credit_balances` table schema
  - [ ] Stripe product/price for credit packs
  - [ ] Session authorization: check credit balance before MAC execution
  - [ ] Credit deduction: atomic decrement on session completion
- [ ] **Amelia: Implement credit packs**
  - [ ] New Stripe products for each credit pack tier
  - [ ] Credit balance API endpoints: `GET /api/credits`, `POST /api/credits/purchase`
  - [ ] Session flow: credit check before execution, deduction after completion
  - [ ] Test: purchase → use → balance check E2E
  - [ ] Commit: `feat(shell): credit pack billing`

#### 8.5.2 — Enterprise Tier

- [ ] **Trigger:** Annual commitment >$5K from a single customer
- [ ] **Victor: Enterprise pricing validation**
  - [ ] Annual contract vs monthly billing
  - [ ] Volume discounts
  - [ ] SLA commitments (uptime, response time, data residency)
- [ ] **Winston: Enterprise architecture**
  - [ ] Dedicated workspace isolation (separate DB schema or separate Neon branch)
  - [ ] SSO integration (SAML/OIDC via Clerk Enterprise)
  - [ ] Audit log export
  - [ ] Custom quality gate configuration per workspace
- [ ] **Amelia: Implement enterprise tier**
  - [ ] Workspace type enum: `free_trial`, `per_session`, `credit_pack`, `enterprise`
  - [ ] Enterprise workspace provisioning API
  - [ ] SSO configuration UI
  - [ ] Commit: `feat(shell): enterprise tier workspace`

#### 8.5.3 — Consultancy Partner Program (White-Label `firm_voice`)

- [ ] **Trigger:** 1+ consultancy firm requests white-label capability
- [ ] **Victor: Partner program design**
  - [ ] Revenue share model (70/30? 80/20?)
  - [ ] Branding customization scope (logo, colors, output header/footer)
  - [ ] `firm_voice` rendering mode configuration per partner
- [ ] **Winston: White-label architecture**
  - [ ] Partner workspace with custom branding config
  - [ ] `firm_voice` template overrides (Jinja2 inheritance)
  - [ ] Custom domain support (partner.praxis.ai or partner's own domain)
- [ ] **Amelia: Implement white-label**
  - [ ] Partner configuration table
  - [ ] Template override resolution (partner-specific → default)
  - [ ] Commit: `feat(studio): consultancy white-label firm_voice`

**Gate 8.5:** No fixed gate — items are individually complete when their trigger fires and implementation ships. Track completion per item.

---

### 8.6 — Observability

**Goal:** See what is happening in production. Errors, costs, usage, health. No blind spots.

**Assigned agents:** Amelia (implementation)
**Model:** Sonnet 4.6 (standard wiring)

#### 8.6.1 — Sentry Error Tracking

- [ ] **Backend:**
  - [ ] `sentry-sdk[fastapi]` installed
  - [ ] DSN via `SENTRY_DSN` env var
  - [ ] Release tracking: git SHA as release version
  - [ ] User context: workspace_id (NOT email/PII) attached to events
  - [ ] Performance tracing: sample 10% of transactions
  - [ ] Test: intentional error captured in Sentry test project
  - [ ] Commit: `feat(shell): Sentry error tracking (backend)`

- [ ] **Frontend:**
  - [ ] `@sentry/nextjs` installed
  - [ ] DSN via `NEXT_PUBLIC_SENTRY_DSN` env var
  - [ ] Source maps uploaded on deploy
  - [ ] User context: workspace_id only
  - [ ] Test: intentional error captured
  - [ ] Commit: `feat(shell): Sentry error tracking (frontend)`

#### 8.6.2 — Plausible Analytics

- [ ] Plausible Cloud account (or self-hosted)
- [ ] Script tag in Next.js `_document` or `layout.tsx`
- [ ] Custom events: `session_started`, `session_completed`, `trial_used`, `paid_session`
- [ ] No cookies, no PII, GDPR-compliant by design
- [ ] Commit: `feat(shell): Plausible analytics`

#### 8.6.3 — Pi-Mono Cost Dashboard (Internal)

- [ ] Internal-only route: `/api/internal/costs` (auth-gated to admin workspace)
- [ ] Metrics: total spend (today/week/month), cost per session (avg/p50/p95), cost by model, cost by workflow mode (quick/deep)
- [ ] Alert: email/Slack if daily spend exceeds $50 (configurable threshold)
- [ ] Commit: `feat(shell): internal Pi-Mono cost dashboard`

#### 8.6.4 — Health Check Endpoints

- [ ] `GET /api/health` — returns `{"status": "ok", "version": "<git-sha>"}` (public, no auth)
- [ ] `GET /api/health/ready` — checks DB connection + Clerk reachability + Stripe reachability
- [ ] `GET /api/health/live` — Kubernetes/Railway liveness probe (always 200 if process running)
- [ ] Deployment platform health check configured to use `/api/health/ready`
- [ ] Commit: `feat(shell): health check endpoints`

**Gate 8.6 complete:** Sentry captures errors in both backend + frontend. Plausible tracks page views + custom events. Internal cost dashboard shows real-time spend. Health checks pass in production.

---

### 8.7 — A4 Human Validation (Spearman Scoring)

**Goal:** Complete the deferred A4 validation from Stage 5.6. If pass: drop the "(internal scoring; A4 deferred)" caveat from ALL materials. If fail: expanded N re-run.

**Assigned agents:** Andrey (human scorer), Amelia (scoring harness)
**Model:** Opus 4.6 (scoring analysis)

**Pre-requisite:** 8.3 complete (real `LLMJudgeClient.call_live()` functional, not fakes)

#### 8.7.1 — Scoring Harness Preparation

- [ ] **Amelia: Prepare blinded scoring package**
  - [ ] Reuse prepared artifacts from `mac/a4-sampling-blinded.md` + `mac/a4-sampling-mapping.md`
  - [ ] Re-run all 10 benchmark questions through real production pipeline (8.3 wiring)
  - [ ] Generate fresh blinded evaluation sheets (3 conditions: B1 vanilla, B2 enhanced, B3 Praxis)
  - [ ] Scoring rubric: R1-R12 gates with integer 1-10 scale per gate per question
  - [ ] Commit: `feat(mac): A4 production scoring harness`

#### 8.7.2 — Human Scoring Session

- [ ] **Andrey: Score all 30 outputs (10 questions x 3 conditions) blind**
  - [ ] Score each output on R1-R12 using the rubric
  - [ ] Record scores in structured format (CSV or JSON)
  - [ ] Do NOT unblind until all 30 are scored

#### 8.7.3 — Spearman Correlation Analysis

- [ ] **Amelia: Compute Spearman rho**
  - [ ] Compare Andrey's human rankings to LLM judge rankings
  - [ ] Compute Spearman rho per gate and overall
  - [ ] **IF rho >= 0.6:** A4 PASS
    - [ ] Strip "(internal scoring; A4 deferred)" caveat from ALL materials:
      - `mac/pre-sales-report.md`
      - `shell/pre-sales-report.md` (launch announcement)
      - `studio/` customer-facing copy
      - `docs/pipeline.md` Stage 5.6 + 6.6 entries
    - [ ] Commit: `feat(mac): A4 PASS — strip scoring caveat from all materials`
  - [ ] **IF rho < 0.6:** A4 FAIL
    - [ ] Expanded re-run with N=20 questions
    - [ ] Recalibrate R1-R12 gates based on human-LLM divergence analysis
    - [ ] Re-run A4 with recalibrated gates
    - [ ] Document findings in `mac/a4-validation-report.md`

**Gate 8.7 complete:** Spearman rho computed and documented. Either caveat stripped (PASS) or recalibration completed (FAIL + retry).

---

### 8.8 — Launch

**Goal:** Real domain, real SSL, real customers.

**Assigned agents:** Amelia (infra), team lead (outreach)
**Model:** Sonnet 4.6 (Amelia)

**Pre-requisites:** 8.1 (infra) + 8.3 (real wiring) + 8.6 (observability) complete. 8.7 PASS strongly recommended.

#### 8.8.1 — Domain + DNS

- [ ] Domain registered (praxis.ai / getpraxis.io / praxis.work — per build-plan.md §1)
- [ ] DNS configured:
  - `praxis.ai` → Vercel (frontend)
  - `api.praxis.ai` → Railway/ECS/Fly (backend)
- [ ] CNAME records verified via `dig` or `nslookup`
- [ ] Commit: `docs: record domain + DNS configuration`

#### 8.8.2 — SSL

- [ ] Vercel auto-provisions SSL for frontend (Let's Encrypt)
- [ ] Backend hosting auto-provisions SSL (Railway/Fly auto-SSL, ECS via ACM + ALB)
- [ ] Verify: `curl -I https://praxis.ai` returns 200 with valid cert
- [ ] Verify: `curl -I https://api.praxis.ai/api/health` returns 200 with valid cert
- [ ] HSTS header enabled on both frontend and backend

#### 8.8.3 — Production Smoke Test

- [ ] Run `scripts/smoke_test_production.py` against live production:
  - [ ] Health check endpoints respond
  - [ ] Clerk OAuth redirect works
  - [ ] Free trial session completes end-to-end
  - [ ] "Built With Praxis" dashboard renders
  - [ ] SSE streaming delivers events during MAC deliberation
  - [ ] Sentry captures test error
  - [ ] Plausible records page view

#### 8.8.4 — First 10-Founder Outreach (per Victor 7.0.1 Section H.1)

- [ ] **Identify 10 Series A-C founders with active strategic decisions**
  - [ ] Warm intros preferred (LinkedIn, mutual connections, founder communities)
  - [ ] Target: founders who have mentioned struggling with strategic analysis
- [ ] **Outreach message** (from `shell/pre-sales-report.md` medium version):
  - [ ] Personalized to each founder's public strategic context
  - [ ] Lead with free trial, not pitch
  - [ ] Budget-anchor test: frame as "AI-powered strategic analysis" (not "consulting replacement")
- [ ] **Track:**
  - [ ] Sent: 10
  - [ ] Opened: _/10
  - [ ] Tried free: _/10 (target: 3/10)
  - [ ] Converted paid: _/_ (target: 1/3 who tried)
- [ ] **Budget-anchor A/B test:**
  - [ ] 5 founders get "AI tool" framing
  - [ ] 5 founders get "advisory" framing
  - [ ] Track which framing converts better

#### 8.8.5 — Post-Launch Monitoring (First 48 Hours)

- [ ] Sentry alert channel active (email or Slack)
- [ ] Neon Postgres connection pool metrics monitored
- [ ] Pi-Mono cost dashboard reviewed every 4 hours
- [ ] Plausible real-time view open
- [ ] On-call: respond to any 500 errors within 30 minutes

**Gate 8.8 complete:** Domain live with SSL. Production smoke test passes. First 10 outreach messages sent. Monitoring active. **PRAXIS IS IN PRODUCTION.**

---

## SECTION 3: AGENT INVOCATION CHAIN (STAGE 8)

Stage 8 uses a lighter agent chain than Stages 1-7. No elicitation rounds -- the product decisions are made. This is pure engineering + operations.

```
8.1  Winston (infra ADRs) → Amelia (implement)
8.2  Amelia (fix) → Cleo (review batch)
8.3  Winston (integration ADRs) → Murat (integration test strategy) → Amelia (implement)
8.4  Amelia (implement)
8.5  Victor (validate trigger) → Winston (arch) → Amelia (implement)  [event-triggered]
8.6  Amelia (implement)
8.7  Amelia (harness) → Andrey (score) → Amelia (analyze)
8.8  Amelia (infra) → team lead (outreach)
```

### Model Allocations

| Sub-stage | Agent | Model | Thinking | Rationale |
|-----------|-------|-------|----------|-----------|
| 8.1 | Winston | Opus 4.6 | high | Infrastructure decisions have long-term consequences |
| 8.1 | Amelia | Sonnet 4.6 [1M] | medium | Docker/CI is pattern-following |
| 8.2 | Amelia | Sonnet 4.6 | medium | Each fix is isolated and well-scoped |
| 8.2 | Cleo | Sonnet 4.6 | medium | Code review of focused fixes |
| 8.3 | Winston | Opus 4.6 [1M] | high | Cross-stage integration is high-context |
| 8.3 | Murat | Opus 4.6 | high | Integration test design for real services |
| 8.3 | Amelia | Sonnet 4.6 [1M] | high | Wiring real services requires reading multiple stage architectures |
| 8.4 | Amelia | Sonnet 4.6 | low | Standard monorepo tooling |
| 8.5 | Victor | Opus 4.6 | high | Business model decisions |
| 8.5 | Winston | Opus 4.6 | high | Architecture for billing/enterprise |
| 8.5 | Amelia | Sonnet 4.6 | medium | Implementation of billing features |
| 8.6 | Amelia | Sonnet 4.6 | low | SDK integration is well-documented |
| 8.7 | Amelia | Sonnet 4.6 | medium | Scoring harness |
| 8.7 | Analysis | Opus 4.6 | high | Statistical analysis of human-LLM correlation |
| 8.8 | Amelia | Sonnet 4.6 | low | DNS/SSL is mechanical |

---

## SECTION 4: GATE CONDITIONS

### Before starting 8.1:
- [ ] All Stages 1-7 `[x]` in `docs/pipeline.md`
- [ ] Repo restructured to `kernel/` + `shell/` + `docs/`
- [ ] External accounts provisioned (Neon, Clerk, Stripe, Vercel)

### Before starting 8.2:
- [ ] 8.1.6 CI pipeline green (can run tests in CI)

### Before starting 8.3:
- [ ] 8.1 complete (deployment infra exists)
- [ ] 8.2 complete (no technical debt in codebase)

### Before starting 8.4:
- [ ] 8.1 complete (CI config exists to wire into)

### Before starting 8.5 (any item):
- [ ] Trigger condition met for that specific item
- [ ] 8.3 complete (real Stripe wired)

### Before starting 8.6:
- [ ] 8.3 complete (need real production deployment to observe)

### Before starting 8.7:
- [ ] 8.3 complete (real `LLMJudgeClient.call_live()` functional)

### Before starting 8.8:
- [ ] 8.1 complete (infra)
- [ ] 8.3 complete (real wiring)
- [ ] 8.6 complete (observability -- do NOT launch blind)
- [ ] 8.7 PASS recommended (can launch with caveat if FAIL, but strongly prefer PASS)

---

## SECTION 5: COST ESTIMATE

| Sub-stage | Estimated LLM cost (Max billing) | Estimated wall-clock time | Rationale |
|-----------|----------------------------------|--------------------------|-----------|
| 8.1 | ~$5 | 1 session (2-3 hours) | Docker + CI is mostly config files |
| 8.2 | ~$8 | 2 sessions (4-5 hours) | 19 focused fixes, each small |
| 8.3 | ~$15 | 3 sessions (6-8 hours) | Real service integration is the hardest part |
| 8.4 | ~$3 | 1 session (1-2 hours) | Standard monorepo setup |
| 8.5 | ~$5 per item | Event-triggered | Build only when needed |
| 8.6 | ~$3 | 1 session (1-2 hours) | SDK integration is well-documented |
| 8.7 | ~$8 | 1 session + Andrey scoring time | Re-run 10 questions through production |
| 8.8 | ~$2 | 1 session (1 hour) | DNS/SSL/smoke test |

**Total Stage 8 estimate:** ~$44-50 LLM cost, ~8-10 sessions, ~20-25 hours wall-clock (excluding 8.5 event-triggered items and 8.7 human scoring wait time).

---

## SECTION 6: RISK REGISTER

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R8-1 | Neon Postgres free tier rate limits hit during launch | MEDIUM | HIGH | Upgrade to paid tier ($19/mo) before outreach begins |
| R8-2 | Clerk webhook delivery failures lose signup events | LOW | MEDIUM | Idempotent webhook handlers + retry queue |
| R8-3 | Stripe webhook signature validation rejects legitimate events | LOW | HIGH | Test extensively in Stripe test mode first |
| R8-4 | Anthropic API rate limits during concurrent MAC sessions | MEDIUM | HIGH | Queue sessions, max 2 concurrent MAC deliberations initially |
| R8-5 | A4 Spearman rho < 0.6 (human-LLM scoring divergence) | MEDIUM | MEDIUM | Expanded N=20 re-run with recalibrated gates |
| R8-6 | Docker image size bloats past 2GB (all kernel packages) | LOW | LOW | Multi-stage build, .dockerignore, alpine base |
| R8-7 | Pre-commit hooks slow down developer workflow | LOW | LOW | Cache mypy results, parallelize checks |
| R8-8 | First 10 outreach messages get 0 responses | MEDIUM | LOW | A/B test framing; iterate message; expand to 20 |

---

## SECTION 7: SUCCESS CRITERIA (STAGE 8 COMPLETE WHEN)

1. **Infrastructure:** `docker compose up` starts full stack locally; CI pipeline green; production deployment auto-deploys on merge to `main`
2. **Debt:** 0 items on debt ledger (all 19 resolved or explicitly retired with documented rationale)
3. **Real wiring:** Zero `Fake*` classes in production code path; all fakes retained as test doubles only
4. **Monorepo:** `uv sync && uv run pytest` from repo root runs all packages; pre-commit hooks installed
5. **Observability:** Sentry + Plausible + health checks + internal cost dashboard all functional
6. **A4 Validation:** Spearman rho computed; either caveat stripped (PASS) or recalibration documented (FAIL)
7. **Live:** Domain + SSL + production smoke test passing; first 10 outreach messages sent
8. **Monitoring:** 48-hour post-launch monitoring complete with zero unresolved P0 incidents
