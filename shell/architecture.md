# Praxis Stage 7.1 — POV Delivery Harness Architecture

**Stage:** Praxis 7.1 — Shell (Web UI + Auth + Billing + Onboarding + API)
**Author:** Winston (BMAD Architect)
**Date:** 2026-04-16
**Status:** DRAFT v0.1 — pending team-lead spot-check and ratification

**Binding upstream artifacts:**
1. `shell/pricing-strategy.md` — Victor 7.0.1 (459 lines, RATIFIED 2026-04-16)
2. `shell/messaging-and-onboarding.md` — Sophia 7.0.2 (409 lines, RATIFIED 2026-04-16)
3. `studio/architecture.md` — Winston 6.1 (977 lines, RATIFIED 2026-04-16)
4. `mac/architecture.md` — Winston 5.1 (2,028 lines, v0.3+ binding, RATIFIED 2026-04-14)
5. `pi-mono/pi-mono-cost-tracker-architecture.md` — Winston 1.1 (billing integration surface)

**Disposition anchors (from Stage 7 preload, team-lead ratified 2026-04-16):**
- DQ-1: Shell adapters only, MAC stays frozen. C-2/C-3/C-4 resolved via shell-layer code.
- DQ-2: A4 Option C — score existing package in parallel, fallback to fresh re-run.
- DQ-3: ADR-08 deferred to Stage 8 (MVP = Markdown + HTML).
- DQ-4: Shell→Studio→MAC only. C-1/C-5 advisory (Stage 8).
- 6-item blocker list: C-2 (ULID adapter), C-3 (LLMResponse shape), C-4 (promotion hook), A4 (parallel), ADR-10 (dashboard), DL-15 (mode routing).

---

## §1 — UI Information Architecture

### §1.1 Page Hierarchy

```
/ (public)
├── /                       Landing page (hero + how-it-works + pricing + dashboard)
├── /login                  Clerk OAuth redirect
├── /signup                 Clerk signup → workspace creation → first session prompt
│
/ (authenticated, /app prefix)
├── /app                    Mission Control dashboard
├── /app/sessions/new       Session intake form
├── /app/sessions/:id       Session detail (live view during run, results after)
├── /app/sessions/:id/share Shareable link (auth-gated per ADR-10)
├── /app/history            Session history list
├── /app/settings           Workspace settings (billing, team, API keys)
├── /app/settings/billing   Stripe Customer Portal embed
├── /app/settings/team      Team member management (RBAC)
│
/ (public)
├── /dashboard              "Built With Praxis" public dashboard (ADR-10)
```

### §1.2 Route Structure (Next.js App Router)

```
app/
├── layout.tsx              Root layout (ClerkProvider, theme, fonts)
├── page.tsx                Landing page
├── login/page.tsx          Clerk SignIn
├── signup/page.tsx         Clerk SignUp + workspace creation
├── dashboard/page.tsx      Public "Built With Praxis" dashboard
├── app/
│   ├── layout.tsx          Authenticated layout (ClerkProtect, sidebar nav)
│   ├── page.tsx            Mission Control
│   ├── sessions/
│   │   ├── new/page.tsx    Intake form
│   │   └── [id]/
│   │       ├── page.tsx    Session detail + live view + results
│   │       └── share/page.tsx  Shareable link view
│   ├── history/page.tsx    Session list
│   └── settings/
│       ├── page.tsx        Settings overview
│       ├── billing/page.tsx Stripe portal
│       └── team/page.tsx   Team RBAC
```

### §1.3 Component Composition (shadcn/ui)

Primary component library: **shadcn/ui** (Radix primitives + Tailwind CSS).

Key custom components:
- `<SessionIntakeForm>` — strategic question textarea + context + depth selector + cost preview
- `<SessionLiveView>` — SSE-driven progress indicator + cost counter + streaming trace
- `<SessionResultView>` — rendered Markdown/HTML output + dissent section + cost breakdown + export
- `<PricingCard>` — quick/deep tier comparison (from Sophia §E.4)
- `<PublicDashboard>` — aggregate metrics + savings breakdown (ADR-10)
- `<OnboardingChecklist>` — 3-step signup flow (from Sophia §G.1)

---

## §2 — Visual Design Specification

### §2.1 Color Palette

**Forest + Midnight** (per Sally's brand work in Business Session):
- Primary: `#1B4332` (forest green)
- Secondary: `#0D1B2A` (midnight blue)
- Accent: `#52B788` (sage green)
- Background: `#FAFAF9` (warm white)
- Text: `#1A1A1A` (near-black)
- Muted: `#6B7280` (gray-500)
- Error: `#DC2626` (red-600)
- Success: `#059669` (emerald-600)

### §2.2 Typography

- **Headings:** Inter (sans-serif, variable weight)
- **Body:** Inter
- **Code / data / cost figures:** JetBrains Mono (monospace)

### §2.3 Key Component Wireframes

**Session Intake Form:**
```
┌─────────────────────────────────────────────────┐
│ What's your strategic question?                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ [textarea — 4 lines visible]                │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Context (optional)                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ [textarea — 2 lines visible]                │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Depth:  [● Quick ~4min $29]  [○ Deep ~12min $149]│
│                                                  │
│ Estimated cost: $29        [Start Analysis →]    │
└─────────────────────────────────────────────────┘
```

**Session Live View:**
```
┌─────────────────────────────────────────────────┐
│ Analysis in progress...                          │
│ ████████████░░░░░░░░  Cycle 2 of 3              │
│                                                  │
│ Cost so far: $1.87          Est. remaining: $0.63│
│ Elapsed: 7:42               Est. total: ~12 min  │
│                                                  │
│ ▼ Reasoning trace (collapse)                     │
│   [streaming text of current cycle reasoning]    │
└─────────────────────────────────────────────────┘
```

---

## §3 — Backend API Design

### §3.1 Endpoint Specifications

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/sessions` | JWT | Start a new Studio session |
| `GET` | `/api/sessions/:id` | JWT | Session status + results |
| `GET` | `/api/sessions/:id/stream` | JWT | SSE stream of progress events |
| `GET` | `/api/sessions` | JWT | List user's sessions (paginated) |
| `GET` | `/api/usage` | JWT | User's usage stats (Pi-Mono backed) |
| `POST` | `/api/webhooks/stripe` | Stripe sig | Stripe webhook handler |
| `GET` | `/api/public/stats` | None | "Built With Praxis" dashboard data |
| `POST` | `/api/webhooks/delivery` | HMAC | Customer webhook delivery (async) |

### §3.2 Core Data Models (Pydantic)

```python
# shell/api/models.py

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from decimal import Decimal
import ulid

class SessionDepth(str, Enum):
    QUICK = "quick"
    DEEP = "deep"

class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class RenderingMode(str, Enum):
    """DL-15 resolution: expose all 3 modes to user."""
    POSITION_TO_HOLD = "position_to_hold"
    DECISION_FRAMEWORK = "decision_framework"
    FIRM_VOICE = "firm_voice"

class CreateSessionRequest(BaseModel):
    question: str = Field(..., min_length=20, max_length=10000)
    context: str | None = Field(None, max_length=5000)
    depth: SessionDepth = SessionDepth.DEEP
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD

class SessionResponse(BaseModel):
    id: str                         # ULID
    workspace_id: str               # Clerk org ID
    status: SessionStatus
    depth: SessionDepth
    rendering_mode: RenderingMode
    question: str
    context: str | None
    cost_usd: Decimal | None        # from Pi-Mono, populated after completion
    started_at: datetime
    completed_at: datetime | None
    result_url: str | None          # shareable link (ADR-10)
```

### §3.3 Error Response Format

```json
{
  "error": {
    "code": "SESSION_BUDGET_EXCEEDED",
    "message": "Session cost exceeded the $10 budget ceiling.",
    "detail": "Actual cost: $11.23. Session results are available but marked as over-budget.",
    "session_id": "01HXYZ..."
  }
}
```

All errors follow this shape. HTTP status codes: 400 (validation), 401 (auth), 403 (authz), 404, 422 (business logic), 500.

---

## §4 — Authentication and Authorization

### §4.1 Clerk Integration

**Approach:** Clerk as the sole auth provider. No custom auth logic.

```
Frontend (Next.js)          Clerk                    Backend (FastAPI)
    │                         │                           │
    │── OAuth (Google/GH) ───→│                           │
    │←── JWT ─────────────────│                           │
    │                         │                           │
    │── API call + JWT ──────────────────────────────────→│
    │                         │    ←── verify JWT ───────→│
    │                         │    (Clerk JWKS endpoint)  │
    │←── response ───────────────────────────────────────│
```

- **OAuth providers:** Google, GitHub, Microsoft
- **JWT validation:** FastAPI middleware validates Clerk JWTs via JWKS endpoint
- **Session management:** Clerk handles session lifecycle; backend is stateless

### §4.2 Workspace Model

Clerk Organizations map to Praxis Workspaces:

```
Workspace (Clerk Organization)
├── owner: User (created the workspace)
├── members: User[] (invited)
├── sessions: Session[] (scoped to workspace)
├── billing: Stripe Customer (linked)
└── settings: WorkspaceSettings
```

**First signup flow:**
1. Clerk OAuth → User created
2. Auto-create personal workspace (Clerk personal org)
3. Skip team invites (per Sophia §G.1)
4. Direct to session intake with free trial

### §4.3 RBAC

| Role | Create sessions | View own | View team | Manage billing | Manage team |
|---|---|---|---|---|---|
| **Owner** | yes | yes | yes | yes | yes |
| **Member** | yes | yes | yes | no | no |
| **Viewer** | no | no | yes (shared only) | no | no |

Enforced at FastAPI middleware level via Clerk organization membership + role metadata.

### §4.4 API Key Strategy

For webhook/programmatic access (Stage 8 scope):
- Clerk API keys per workspace
- Scoped to workspace_id
- Rate-limited independently from JWT-authenticated requests

Not implemented at MVP — all access via Clerk JWT.

---

## §5 — Billing and Metering Design

### §5.1 Stripe Product Catalog

```
Stripe Products:
├── praxis_studio_quick     $29/session   (one-time payment)
├── praxis_studio_deep      $149/session  (one-time payment)
└── praxis_trial_credit     $0            (1 free quick session per workspace)
```

**Per Victor 7.0.1:** two tiers at launch (quick $29 / deep $149). Credit packs are planned evolution — NOT built at Stage 7 MVP. [HYPOTHETICAL pricing]

### §5.2 Billing Flow

```
User clicks "Start Analysis"
    │
    ├── Has free trial credit? → Consume trial, start session
    │
    ├── Has Stripe payment method?
    │   └── Yes → Create Stripe PaymentIntent ($29 or $149)
    │       └── PaymentIntent succeeds → Start session
    │       └── PaymentIntent fails → Show error, don't start
    │
    └── No payment method → Redirect to Stripe Checkout
        └── Checkout completes → Start session
```

### §5.3 Pi-Mono Integration (C-2 / C-3 Adapter)

**Problem (C-2):** MAC sets `request_id = "mac:{cycle_id}:{phase}:{seq}"` which does NOT match Pi-Mono's ULID regex `^[0-9A-HJKMNP-TV-Z]{26}$`.

**Problem (C-3):** MAC's local `LLMResponse` has `usd_cost: float` which Pi-Mono explicitly forbids ("No cost on response. Only integer token counts.").

**Solution: Shell-layer adapter** (MAC frozen per DQ-1):

```python
# shell/api/adapters/cost_adapter.py

import ulid
from praxis.kernel.cost.tracker import CostTracker, LLMRequest, LLMResponse

class ShellCostAdapter:
    """Adapts MAC's internal cost events to Pi-Mono's canonical contracts.
    
    C-2 resolution: mints a ULID for Pi-Mono, stashes MAC's
    "mac:{cycle_id}:{phase}:{seq}" in tags["mac_request_id"].
    
    C-3 resolution: strips usd_cost from MAC's LLMResponse before
    forwarding to Pi-Mono. Pi-Mono computes cost from its pricing
    snapshot — that's the contract.
    """
    
    def __init__(self, tracker: CostTracker) -> None:
        self._tracker = tracker
    
    async def track_mac_call(
        self,
        mac_request_id: str,        # "mac:cycle_1:propose:3"
        provider: str,
        model_id: str,
        session_id: str,            # Praxis session ULID
        workflow_id: str,           # Studio workflow ULID
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        started_at: datetime = ...,
        finished_at: datetime = ...,
    ) -> CostRecord:
        # C-2: mint a ULID for Pi-Mono, stash MAC ID in tags
        pi_mono_request_id = str(ulid.new())
        
        request = LLMRequest(
            request_id=pi_mono_request_id,
            provider=provider,
            model_id=model_id,
            session_id=session_id,
            workflow_id=workflow_id,
            agent="mac",
            tags={"mac_request_id": mac_request_id},
            started_at=started_at,
        )
        
        # C-3: LLMResponse with token counts ONLY — no usd_cost
        response = LLMResponse(
            request_id=pi_mono_request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            finished_at=finished_at,
            stop_reason="stop",
        )
        
        return await self._tracker.track_cost(request, response)
```

### §5.4 Session Cost Tracking

Each Studio session produces N LLM calls (typically 6-12 for deep, 2-4 for quick). The adapter tracks each call individually via Pi-Mono. Session-level cost is an aggregate query:

```sql
SELECT SUM(cost_total_usd) 
FROM cost_records 
WHERE session_id = :session_id;
```

The customer-facing price ($29 or $149) is separate from the internal cost. The Stripe charge is the customer price; Pi-Mono tracks the internal cost for margin analysis and the "Built With Praxis" dashboard.

### §5.5 Trial Mechanics

- 1 free quick session per workspace
- Tracked via `workspace_settings.trial_used: bool` in Postgres
- No credit card required for trial
- Trial session runs at full quality (not degraded)
- After trial: CTA "Run a deep analysis for $149" (per Sophia §G.2)

---

## §6 — Onboarding Flow Design

### §6.1 Signup Sequence (per Sophia §G.1)

```
Landing page → [Run your first analysis free] CTA
    │
    ▼
Clerk OAuth (Google / GitHub / Microsoft)  ← 1 click
    │
    ▼
Workspace naming  ← 1 text field
    │ (auto-skip team invites)
    ▼
Session intake form with:
    - Free trial badge visible
    - 3 sample questions (from MAC benchmark suite, adapted)
    - OR paste your own question
    │
    ▼
First session runs (quick mode, free)
    │
    ▼
Results view + [Run Deep Analysis — $149] CTA
```

### §6.2 Sample Questions Library

Adapted from MAC benchmark suite (customer dialect, not producer dialect):

1. "We're evaluating a 3-year exclusivity partnership with a distribution partner who has 50K customers. What scenarios should we plan for?" (Q4 adapted)
2. "Our core value proposition is under pricing pressure from a competitor 40% lower. Two enterprise accounts are asking to renegotiate. What position can we hold?" (Q6 adapted)
3. "The board wants European expansion based on 2 inbound leads. What entity-specific risks are we not seeing?" (Q7 adapted)

### §6.3 Post-Trial Billing Upsell (per Sophia §G.3)

After free trial consumed:
- Show result with full quality
- CTA: "Run a deep analysis for $149" or "Run another quick for $29"
- "Connect billing" redirects to Stripe Checkout
- No subscription push at MVP (per Victor 7.0.1 Option A)

---

## §7 — Session Lifecycle Management

### §7.1 Session State Machine

```
PENDING → RUNNING → COMPLETED
                  → FAILED
```

### §7.2 Start Session Flow

```python
# shell/api/routes/sessions.py

@router.post("/api/sessions")
async def create_session(
    req: CreateSessionRequest,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
    stripe: StripeClient = Depends(get_stripe),
    studio: StudioSession = Depends(get_studio),
):
    # 1. Check trial or payment
    if not workspace.trial_used:
        workspace.trial_used = True  # consume trial
    else:
        payment = await stripe.create_payment_intent(
            amount=2900 if req.depth == "quick" else 14900,
            currency="usd",
            customer=workspace.stripe_customer_id,
        )
        if payment.status != "succeeded":
            raise HTTPException(402, "Payment failed")
    
    # 2. Create session record
    session = Session(
        id=str(ulid.new()),
        workspace_id=workspace.id,
        question=req.question,
        context=req.context,
        depth=req.depth,
        rendering_mode=req.rendering_mode,  # DL-15 resolution
        status="pending",
    )
    db.add(session)
    await db.commit()
    
    # 3. Enqueue session execution (background task)
    background_tasks.add_task(
        run_session, session.id, req, workspace
    )
    
    return SessionResponse.from_orm(session)
```

### §7.3 Session Execution (Background)

```python
async def run_session(session_id: str, req: CreateSessionRequest, workspace: Workspace):
    # 1. Update status to RUNNING
    session.status = "running"
    
    # 2. Select YAML template based on depth
    template_path = (
        "strategic_session_quick.yaml" if req.depth == "quick"
        else "strategic_session.yaml"
    )
    
    # 3. Invoke Studio (DL-15: pass rendering_mode from user input)
    result = await studio.invoke(
        template_path=template_path,
        question=req.question,
        context=req.context,
        rendering_mode=req.rendering_mode,  # DL-15: routes to correct templates
    )
    
    # 4. Track cost via adapter (C-2 / C-3)
    total_cost = await cost_adapter.track_session(session_id, result.cost_events)
    
    # 5. C-4 resolution: promotion hook
    if result.status == "completed":
        await memory_adapter.promote_entries(
            workspace_id=workspace.id,
            session_id=session_id,
            task_signature=result.task_signature,
        )
    
    # 6. Render output via Studio renderer
    rendered = await renderer.render(result, req.rendering_mode)
    
    # 7. Update session
    session.status = "completed"
    session.result_html = rendered.html
    session.result_markdown = rendered.markdown
    session.cost_usd = total_cost
    session.completed_at = utcnow()
```

### §7.4 SSE Progress Streaming

```python
@router.get("/api/sessions/{id}/stream")
async def stream_session(
    id: str,
    workspace: Workspace = Depends(get_workspace),
):
    async def event_generator():
        async for event in session_events.subscribe(id):
            yield {
                "event": event.type,  # "cycle_start", "cycle_end", "cost_update", "complete"
                "data": event.json(),
            }
    
    return EventSourceResponse(event_generator())
```

Events emitted:
- `cycle_start` — which cycle (1/2/3), which agents active
- `cost_update` — current running cost (from ShellCostAdapter)
- `cycle_end` — cycle complete, gate scores
- `complete` — session done, result available
- `error` — session failed, reason

### §7.5 Webhook Delivery (Stage 8 scope)

Architecture defined but not implemented at MVP:
- `POST` to customer-configured URL
- HMAC-SHA256 signed with workspace webhook secret
- Retry with exponential backoff (1s, 5s, 30s, 5min, 30min)
- Event types: `session.completed`, `session.failed`

### §7.6 Email Notifications (Stage 8 scope)

Architecture defined but not implemented at MVP:
- Session complete email with result link
- Monthly usage summary
- Via Resend or SendGrid (TBD at implementation)

---

## §8 — "Built With Praxis" Public Dashboard (ADR-10)

### §8.1 Data Sources

All data from Pi-Mono aggregates — privacy-safe, no customer data exposed.

| Metric | Source | Update cadence |
|---|---|---|
| Total sessions run | `COUNT(*)` on sessions table | Real-time |
| Total internal cost | `SUM(cost_total_usd)` from Pi-Mono | Real-time |
| Average session cost | Derived | Real-time |
| Average session time | `AVG(completed_at - started_at)` | Real-time |
| Sessions today | Date-filtered count | Real-time |
| Build pipeline data | 7-stage historical (pre-computed at deploy) | Static |

### §8.2 Visual Design

```
┌─────────────────────────────────────────────────────────┐
│  BUILT WITH PRAXIS                                       │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Sessions │  │ Avg Cost │  │ Avg Time │  │  Today   ││
│  │   127    │  │  $2.41   │  │  11 min  │  │    8     ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                          │
│  "We built Praxis using Praxis. Every architectural      │
│   decision in the 7-stage build pipeline was run through │
│   the same analytical process you can buy today."        │
│                                                          │
│  [Run Your First Analysis Free →]                        │
└─────────────────────────────────────────────────────────┘
```

### §8.3 Privacy Safeguards

- No customer names, workspace names, or question content exposed
- Only aggregate metrics (counts, averages, totals)
- Minimum 10 sessions before any metric is shown (prevent single-customer inference)
- No per-customer breakdown
- Auth-gated link sharing per ADR-10 (individual session shares require workspace auth)

---

## §9 — Multi-Tenant Isolation

### §9.1 Query Layer Enforcement

**Every database query includes `workspace_id` in the WHERE clause.** This is enforced architecturally, not by convention:

```python
# shell/api/middleware/tenant.py

class TenantScopedSession:
    """Wraps SQLAlchemy AsyncSession to inject workspace_id filter
    on every query. Direct table access bypassing this wrapper
    is forbidden — enforced by test coverage."""
    
    def __init__(self, session: AsyncSession, workspace_id: str):
        self._session = session
        self._workspace_id = workspace_id
    
    async def query(self, model, **filters):
        return await self._session.execute(
            select(model).filter_by(
                workspace_id=self._workspace_id,
                **filters,
            )
        )
```

### §9.2 Isolation Rules

1. Session data: scoped to workspace_id (FK enforced in Postgres)
2. Billing data: scoped to Stripe customer ID (1:1 with workspace)
3. Memory retrieval: scoped to workspace_id (passed to Memory facade)
4. API keys (Stage 8): scoped to workspace_id
5. Webhook configs (Stage 8): scoped to workspace_id

### §9.3 Cross-Workspace Prevention

- No `JOIN` across workspaces without explicit aggregation intent (public dashboard only)
- No admin API for cross-workspace queries at MVP
- Postgres RLS (Row-Level Security) as defense-in-depth behind application-layer filtering

---

## §10 — Integration Contracts

### §10.1 Shell → Studio

```python
# The shell calls Studio via StudioSession.invoke()
# Studio handles MAC delegation internally.

from praxis.kernel.studio import StudioSession
from praxis.kernel.studio.schema import WorkflowTemplate, RenderingMode

# DL-15 resolution: shell passes rendering_mode from user input
result = await studio.invoke(
    template_path="strategic_session.yaml",  # or _quick
    question=user_question,
    context=user_context,
    rendering_mode=RenderingMode(req.rendering_mode),
)
# result: SessionResult (frozen dataclass from studio/models.py)
```

### §10.2 Shell → Pi-Mono (via ShellCostAdapter)

See §5.3. The adapter is the sole interface between shell and Pi-Mono. MAC never talks to Pi-Mono directly — the shell intercepts MAC's cost events and translates them.

### §10.3 Shell → Memory (C-4 Promotion Hook)

**Problem (C-4):** MAC's `reuse_successful` does retrieval, not TENTATIVE→CONFIRMED promotion. The promotion path has no caller.

**Solution:** Shell triggers promotion at session-completion time:

```python
# shell/api/adapters/memory_adapter.py

class ShellMemoryAdapter:
    """C-4 resolution: wire the promotion trigger at session-completion
    time. After MAC returns DeliberationResult and user has their
    result, shell calls memory.promote_entries() to confirm that
    the retrieved experiences were useful."""
    
    async def promote_entries(
        self,
        workspace_id: str,
        session_id: str,
        task_signature: str,
    ) -> None:
        # Calls Memory facade's promotion handler
        # TENTATIVE entries from this session → CONFIRMED
        await self._memory.promote_task_entries(
            workspace_id=workspace_id,
            task_signature=task_signature,
            confirmation_source=f"session:{session_id}",
        )
```

**Note:** This promotion happens automatically on session completion. A future enhancement (Stage 8) could make it user-triggered ("Was this analysis helpful? [Yes/No]") for higher-fidelity signal.

### §10.4 Shell → Clerk

- JWT validation via Clerk JWKS endpoint
- Organization (workspace) management via Clerk API
- User invitation via Clerk invitation API
- No custom auth logic

### §10.5 Shell → Stripe

- PaymentIntent creation for per-session charges
- Customer creation on first billing interaction
- Customer Portal for self-service billing management
- Webhook handler for payment events (succeeded, failed, refunded)

---

## §11 — Observability Setup

### §11.1 Error Tracking

**Sentry** (Python + Next.js):
- FastAPI: `sentry-sdk[fastapi]` integration
- Next.js: `@sentry/nextjs` integration
- Session ID attached to all Sentry events for correlation
- PII scrubbing: strip question/context content from error reports

### §11.2 Metrics (OpenTelemetry)

From Pi-Mono CostTracker + Studio session lifecycle:
- `praxis.session.duration_seconds` (histogram)
- `praxis.session.cost_usd` (histogram)
- `praxis.session.status` (counter by status)
- `praxis.session.depth` (counter by depth)
- `praxis.billing.payment_status` (counter by status)

### §11.3 User Analytics

**Plausible** (privacy-respecting, no cookies):
- Landing page → signup conversion
- Signup → first session conversion
- Trial → paid conversion
- Session frequency per workspace (aggregated)

### §11.4 Operational Dashboard (Grafana)

- Session throughput (sessions/hour)
- Error rate (failed sessions / total sessions)
- P95 session duration
- Pi-Mono cost tracking lag
- Stripe webhook delivery success rate

---

## §12 — Deployment Architecture

### §12.1 Infrastructure

```
┌─────────────────────────────────────────────────┐
│                   Vercel                          │
│  ┌───────────────────────────────────────────┐   │
│  │  Next.js App (SSR + API routes for BFF)   │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────┐
│              Railway / ECS Fargate                │
│  ┌───────────────────────────────────────────┐   │
│  │  FastAPI Backend                           │   │
│  │  + Praxis Engine (Pi-Mono, MAC, Studio)    │   │
│  │  + ShellCostAdapter                        │   │
│  │  + ShellMemoryAdapter                      │   │
│  └───────────────────────────────────────────┘   │
└─────────────┬──────────────┬────────────────────┘
              │              │
┌─────────────▼──┐  ┌───────▼──────────┐
│   Neon Postgres │  │  External APIs   │
│   (managed)     │  │  - Clerk         │
│                 │  │  - Stripe        │
│                 │  │  - Anthropic     │
│                 │  │  - Sentry        │
└─────────────────┘  └────────────────┘
```

### §12.2 Database Schema (Postgres)

```sql
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,                    -- Clerk org ID
    name TEXT NOT NULL,
    stripe_customer_id TEXT,
    trial_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                    -- ULID
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    question TEXT NOT NULL,
    context TEXT,
    depth TEXT NOT NULL CHECK (depth IN ('quick', 'deep')),
    rendering_mode TEXT NOT NULL DEFAULT 'position_to_hold',
    status TEXT NOT NULL DEFAULT 'pending',
    cost_usd NUMERIC(10,4),
    stripe_payment_intent_id TEXT,
    result_markdown TEXT,
    result_html TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_workspace ON sessions(workspace_id);
CREATE INDEX idx_sessions_status ON sessions(workspace_id, status);
```

### §12.3 Secrets Management

| Secret | Storage | Access |
|---|---|---|
| `CLERK_SECRET_KEY` | Railway env var | FastAPI only |
| `CLERK_PUBLISHABLE_KEY` | Vercel env var | Next.js only |
| `STRIPE_SECRET_KEY` | Railway env var | FastAPI only |
| `STRIPE_WEBHOOK_SECRET` | Railway env var | FastAPI only |
| `ANTHROPIC_API_KEY` | Railway env var | FastAPI (engine) only |
| `DATABASE_URL` | Railway env var | FastAPI only |
| `SENTRY_DSN` | Both env vars | Both |

**Note:** `ANTHROPIC_API_KEY` is for the production engine. The development/build environment (this CLI) uses Claude Max subscription without an API key.

---

## §13 — Testability Notes for Murat

### §13.1 E2E Test Scenarios

1. **Signup → first session → result:** OAuth mock → workspace creation → free trial session → result rendered
2. **Paid session flow:** Trial consumed → Stripe Checkout → payment → session → result
3. **Session failure + no charge:** Session fails mid-run → error shown → no Stripe charge created
4. **Rendering mode routing (DL-15):** Submit with each mode → verify correct template family used
5. **Multi-workspace isolation:** Create 2 workspaces → sessions in workspace A not visible in workspace B

### §13.2 Billing Reconciliation Tests

1. **Pi-Mono cost matches Stripe charge:** Run session → verify Pi-Mono total = internal cost, Stripe charge = customer price
2. **ULID adapter (C-2):** Verify Pi-Mono request_id is ULID format; verify MAC ID in tags
3. **Shape adapter (C-3):** Verify LLMResponse sent to Pi-Mono has no usd_cost field
4. **Trial idempotency:** Consuming trial twice in race condition → only 1 free session

### §13.3 Workspace Isolation Tests

1. **Query-layer enforcement:** Direct DB query without workspace_id filter → test framework rejects
2. **Cross-workspace session access:** Request session from workspace B with workspace A JWT → 404
3. **Postgres RLS:** Disable application-layer filter → RLS still blocks cross-workspace access

### §13.4 Public Dashboard Tests

1. **Privacy:** Dashboard endpoint returns no question content, no workspace names
2. **Minimum threshold:** <10 sessions → dashboard returns "Not enough data yet"
3. **Aggregate accuracy:** Dashboard totals match Pi-Mono aggregate queries

### §13.5 SSE Streaming Tests

1. **Live view events:** Start session → subscribe SSE → receive cycle_start, cost_update, complete events
2. **Client disconnect:** Client drops SSE connection → server cleans up, session continues
3. **Auth on SSE:** Unauthenticated SSE request → 401

---

## §14 — Launch Checklist

### §14.1 Pre-Launch

- [ ] Domain registered and DNS configured
- [ ] SSL via Vercel (automatic)
- [ ] Clerk application created with OAuth providers
- [ ] Stripe account activated (live mode)
- [ ] Stripe products created (quick $29, deep $149)
- [ ] Neon Postgres provisioned + schema migrated
- [ ] Railway/Fargate backend deployed
- [ ] Sentry projects created (frontend + backend)
- [ ] Plausible analytics configured
- [ ] `ANTHROPIC_API_KEY` set in production env

### §14.2 Launch Day

- [ ] Landing page live (per Sophia §E copy)
- [ ] Pricing page live ($29 / $149 per Victor 7.0.1)
- [ ] "Built With Praxis" dashboard populated with build pipeline data
- [ ] Free trial functional (1 quick session, no CC)
- [ ] A4 Spearman validation complete (if ρ ≥ 0.6, drop caveat from landing page)
- [ ] First POV customer contacted via warm outreach

### §14.3 Post-Launch

- [ ] Monitor Sentry for errors in first 24 hours
- [ ] Track trial→paid conversion (target ≥25%)
- [ ] Collect WTP feedback from first 5 customers (Victor H1 budget-anchor test)
- [ ] Add credit packs when ≥3 customers have ≥5 sessions each

---

## §15 — Open Questions

### §15.1 Resolved at This Stage

| Question | Resolution |
|---|---|
| Pricing model | Per-session MVP (Victor 7.0.1 Option A) |
| Number of tiers | Two: quick $29 / deep $149 |
| Trial policy | 1 free quick session, no CC |
| MAC unfreezing | No — shell adapters only (DQ-1) |
| C-1 / C-5 scope | Advisory, deferred to Stage 8 (DQ-4) |
| Export formats | Markdown + HTML only (ADR-08 → Stage 8) |
| Rendering mode routing | Exposed to user via CreateSessionRequest (DL-15) |

### §15.2 Deferred to Stage 8+

| Question | Rationale |
|---|---|
| Credit packs | Add when repeat usage signals emerge |
| Enterprise tier | Add when annual >$5K commitment requested |
| PDF/`.pptx` export | ADR-08 — pull when real buyer requests |
| Webhook delivery | Architecture defined, implementation deferred |
| Email notifications | Architecture defined, implementation deferred |
| API key access | Clerk API keys, deferred to programmatic access demand |
| User-triggered promotion | C-4 enhancement: "Was this helpful?" signal |

---

## §16 — Stage 7 Debt Ledger Disposition

### §16.1 Blockers Resolved

| # | Item | Resolution |
|---|---|---|
| C-2 | Pi-Mono ULID vs MAC prefix | `ShellCostAdapter` mints ULID, stashes MAC ID in `tags["mac_request_id"]` (§5.3) |
| C-3 | LLMResponse shape drift | `ShellCostAdapter` strips `usd_cost`, sends token-only response to Pi-Mono (§5.3) |
| C-4 | Memory promotion semantic mismatch | `ShellMemoryAdapter.promote_entries()` called at session completion (§10.3) |
| ADR-10 | "Built With Praxis" public dashboard | Designed at §8, API at `/api/public/stats`, privacy safeguards defined |
| DL-15 | Rendering-mode routing unreachable | `CreateSessionRequest.rendering_mode` field exposes all 3 modes; passed through to Studio (§7.2, §10.1) |

### §16.2 Parallel (Not Architectural)

| # | Item | Status |
|---|---|---|
| A4 | Spearman validation | Option C: Andrey scores existing package in parallel with build. Not an architecture item. |

### §16.3 Advisory (Deferred to Stage 8)

| # | Items | Reason |
|---|---|---|
| MAC W-2/W-3/W-4/W-5/W-7 | 5 MAC Cleo WARNINGs | MAC frozen; shell wraps MAC as-is |
| C-1 | Compression class name drift | Shell doesn't touch Compression (DQ-4) |
| C-5 | Runtime spawner method drift | Shell doesn't touch Runtime (DQ-4) |
| Studio W-1/W-2/W-3/W-4 | 4 Studio Cleo WARNINGs | Studio frozen; shell wraps Studio as-is |
| DL-14 | CostTrackerProtocol rename | Observability naming, no behavioral impact |
| ADR-08 | PDF/`.pptx` export | MVP scope (DQ-3) |

---

## §17 — Session-Close Audit

### §17.1 — Deliverable Metrics

| Metric | Value |
|---|---|
| Sections | 17 (§1–§17) |
| Debt blockers resolved | 5/6 (C-2, C-3, C-4, ADR-10, DL-15; A4 is parallel non-arch) |
| Adapter code blocks | 2 (ShellCostAdapter §5.3, ShellMemoryAdapter §10.3) |
| API endpoints defined | 8 |
| Database tables defined | 2 (workspaces, sessions) |
| E2E test scenarios | 15 (§13) |
| [HYPOTHETICAL] pricing references | All pricing ($29/$149) sourced from Victor 7.0.1 with [HYPOTHETICAL] flag |

### §17.2 — Constraint Compliance

- **MAC frozen (DQ-1):** Zero modifications to MAC source. All 3 blocker resolutions (C-2, C-3, C-4) via shell adapters.
- **Studio frozen:** Zero modifications to Studio source. DL-15 resolved by passing `rendering_mode` through Studio's existing `RenderingMode` enum.
- **C1 (no pre-sales numbers):** Zero instances of +47%, +21%, 25.2, 13.7, 10/10, composite, beat-count.
- **Tokonomics firewall:** No tokonomics-era vocabulary in any customer-facing surface (landing page copy, error messages, onboarding flow).
- **ADR-08:** MVP = Markdown + HTML only. No PDF export designed.
- **Memory writes:** NONE.
- **Pipeline marks:** NONE.

---

_Architecture crafted as Winston, BMAD Architect — Stage 7.1 Praxis POV Delivery Harness_
