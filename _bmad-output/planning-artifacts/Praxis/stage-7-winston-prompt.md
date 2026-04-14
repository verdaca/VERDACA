# Stage 7 Launch Prompt — Winston (Architect) for POV Delivery Harness

**Purpose:** Finalized prompt for Stage 7 — POV Delivery Harness (Web UI + Auth + Billing + Onboarding + API).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stages 1-6 complete. Stage 7 wraps the engine in a sellable product shell.

---

## THE PROMPT (COPY-PASTE READY)

```
Design the POV Delivery Harness for Praxis Stage 7 (the customer-facing shell).

## PROJECT CONTEXT

Stages 1-6 built the engine: measurement, compression, memory, runtime, MAC,
and the first workflow template (Studio). Stage 7 wraps all of this in a
minimal but sellable product shell so the first POV customer can go from
signup to their first Praxis Studio result in < 10 minutes.

Stage 7 is deliberately LAST. We don't build the UI before the engine works.
We build just enough UI to sell the engine. More polish happens post-launch
based on customer feedback.

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Architecture context for Layer 5 Product Shells:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\box-core-architecture.md
(see "Layer 5: Product Shells" section — thinnest possible layer over the engine)

Dependencies (your inputs):
- Pi-Mono (Stripe metering integrates with this):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md
- Memory (session persistence, result history):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\memory\architecture.md
- Runtime (permissions, tenant scoping):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\runtime\architecture.md
- MAC (workflow execution API):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\mac\architecture.md
- Studio (the workflow we're wrapping):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\studio\architecture.md

## READ FIRST — PRE-SALES NARRATIVE

Before designing the UI, read:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Pay attention to Part 3 ("Self-Demonstrating Savings Dashboard") and Part 4
("The Pre-Sales Engine"). The UI is NOT just a product — it is a proof
exhibit for the "Built With Praxis" story.

## STRATEGY

Stage 7 is mostly NEW CODE, but using well-established SaaS patterns
(Next.js + FastAPI + Clerk + Stripe). No porting from reference projects.
No new research. Focus: SHIP FAST, not BUILD RIGHT.

## PRAXIS REQUIREMENTS

### Web UI Requirements

1. **Marketing/Landing Page** (publicly accessible)
   - Hero: "Praxis. Reasoning, executed." + live savings counter
   - "Built With Praxis" public dashboard (hero feature)
   - Example Studio session output (real, anonymized)
   - "How it works" (5-stage diagram)
   - Pricing (per-session for Studio, tier transparency)
   - Signup CTA

2. **Authenticated App Dashboard** (post-signup)
   - Mission Control view: sessions this month, total savings, current credits
   - Start new Studio session (single CTA)
   - Session history (list + detail views)
   - Settings (API keys, billing, team)

3. **Session Intake Form**
   - Strategic question (textarea)
   - Context (optional textarea)
   - Depth selector (quick / standard / deep)
   - Budget estimate preview (from Pi-Mono historical data)
   - "Start Analysis" button

4. **Session Live View**
   - Real-time progress indicator (which cycle, which agents active)
   - Live cost counter (per Pi-Mono)
   - Streaming reasoning trace (optional, for power users)
   - Estimated time remaining

5. **Session Results View**
   - Structured brief (rendered Markdown)
   - Visual deck (rendered HTML, shareable link)
   - Dissenting views section (prominently displayed, not buried)
   - Cost breakdown (tokens, API cost, Praxis fee)
   - Export options (PDF, Markdown, share link)

6. **"Built With Praxis" Public Dashboard**
   - Headline metrics: total tokens processed, total savings, workflows run
   - Layered savings breakdown (per compression layer, memory retrieval)
   - Live session counter (privacy-safe, no customer data)
   - "12 weeks of data, 100% transparent"

### Backend API Requirements

7. **FastAPI service** exposing:
   - `POST /api/sessions` — start a new Studio workflow
   - `GET /api/sessions/{id}` — session status + results
   - `GET /api/sessions/{id}/stream` — SSE stream of progress events
   - `GET /api/usage` — user's usage stats (Pi-Mono backed)
   - `POST /api/webhooks/stripe` — Stripe webhook handler
   - `GET /api/public/stats` — "Built With Praxis" dashboard data

8. **Authentication** via Clerk (chosen for fastest setup)
   - OAuth via Google/GitHub/Microsoft
   - Workspace model (personal + team workspaces)
   - JWT-based API auth

9. **Authorization** (RBAC)
   - Owner: all permissions
   - Member: create sessions, view own
   - Viewer: read-only on shared sessions

10. **Multi-tenant isolation:**
    - Every session scoped to workspace_id
    - Memory retrieval scoped to workspace
    - No cross-workspace data leakage (enforced at query layer)

### Billing Requirements

11. **Stripe integration:**
    - Subscription model: base plan + per-session usage
    - Studio quick: $500/session
    - Studio standard: $1000/session
    - Studio deep: $2000/session
    - Usage metering via Pi-Mono (real cost captured, customer billed marked up)
    - Monthly invoices with full session breakdown

12. **Free trial:**
    - 1 free Studio quick session per new workspace (marketing funnel)
    - No credit card required for trial
    - Convert to paid after first result

13. **Credit system:**
    - Pre-paid credit pools (alternative to per-session billing)
    - $500 / $2000 / $10000 credit packs
    - Used for Studio sessions at standard rates

### Onboarding Requirements

14. **Signup flow (< 3 minutes):**
    - Clerk OAuth (1 click)
    - Workspace name
    - Skip: no team invites, no billing yet

15. **First session flow (< 5 minutes from signup):**
    - Onboarding checklist: "Run your first Studio session"
    - Sample questions provided (3 examples from Tokonomics-style analyses)
    - OR paste your own question
    - Free trial applies automatically
    - Confetti + "Here's what Praxis analyzed for you"

16. **Second session onboarding:**
    - Prompt: "Connect billing to run more sessions"
    - Stripe checkout flow
    - Show credit packs vs subscription options

### Async & Notifications

17. **Webhook delivery** for completed sessions:
    - POST to customer-configured webhook URL
    - Signed HMAC for verification
    - Retry with exponential backoff

18. **Email notifications:**
    - Session complete (with result link)
    - Usage threshold alerts
    - Monthly invoice

### Non-Functional Requirements

19. **Time-to-first-result:** < 10 minutes from landing page to Studio
    session output for new user.

20. **Uptime target:** 99.5% for POV phase (can tighten later).

21. **Security:**
    - HTTPS everywhere
    - API keys never logged
    - Customer data encrypted at rest
    - SOC 2 Type 1 prep for future (not required for POV)

22. **Observability:**
    - Error tracking (Sentry)
    - Metrics (Grafana + OpenTelemetry from engine)
    - User analytics (privacy-respecting, e.g., Plausible)

23. **Test coverage:** >= 75% (UI + integration, lower gate than engine
    components — UI is more iteratively tuned).

## RISK CONTEXT

Stage 7 risks are customer-facing and trust-destroying if mishandled:

- **Billing errors:** Double-charging, incorrect cost tracking → destroyed
  trust. Pi-Mono must be the ground truth. Reconciliation against Stripe.
- **Session failures without refund:** If MAC fails mid-session, customer
  paid but got nothing. Need automated retry + refund protocol.
- **Data leakage across workspaces:** Catastrophic. Scoping must be
  enforced at query layer, not trusted to application code.
- **Slow time-to-first-result:** If signup → first result takes > 10 min,
  conversion drops. Onboarding must be ruthlessly optimized.
- **Unclear cost preview:** Customer runs a session, surprised by the
  cost. Preview must be accurate (within Pi-Mono's ±20% prediction).
- **Dissent smoothing:** Output formatting hides the dissenting views
  that are Praxis's differentiation. Must be prominently displayed.
- **Third-party dependency risk:** Clerk, Stripe down → all signups
  blocked. Have degraded mode.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **UI Information Architecture**
   - Page hierarchy (marketing + app)
   - Route structure (Next.js App Router)
   - Component composition strategy (shadcn/ui)

2. **Visual Design Specification**
   - Color palette (Forest + Midnight per Sally's brand work in Business Session)
   - Typography (Inter + JetBrains Mono)
   - Key components (Studio intake, Live view, Results view)
   - Wireframes or component sketches

3. **Backend API Design**
   - Endpoint specifications (OpenAPI)
   - Authentication middleware (Clerk JWT validation)
   - Authorization middleware (workspace scoping enforcement)
   - Error response format

4. **Authentication & Authorization**
   - Clerk integration approach
   - Workspace + user model
   - RBAC implementation
   - API key strategy (for webhook/programmatic access)

5. **Billing & Metering Design**
   - Stripe product/price catalog
   - Metering flow (Pi-Mono → Stripe usage records)
   - Invoice generation
   - Trial and credit pack mechanics

6. **Onboarding Flow Design**
   - Signup sequence (Clerk OAuth → workspace → first session prompt)
   - Sample questions library
   - First session experience (confetti, result delivery)
   - Second session billing upsell

7. **Session Lifecycle Management**
   - Start session API flow
   - Live progress streaming (SSE)
   - Result persistence and sharing
   - Webhook delivery mechanism
   - Email notification triggers

8. **"Built With Praxis" Public Dashboard Design**
   - Data sources (Pi-Mono aggregates, privacy-safe)
   - Visual design (hero metrics + breakdowns)
   - Update cadence (real-time vs daily)
   - Privacy safeguards

9. **Multi-Tenant Isolation**
   - Query layer enforcement
   - Workspace scoping rules
   - Cross-workspace data leakage prevention

10. **Integration Contracts**
    - With Pi-Mono (usage metering)
    - With Memory (workspace-scoped retrieval)
    - With MAC (workflow execution + SSE streaming)
    - With Studio (template invocation)

11. **Observability Setup**
    - Error tracking (Sentry config)
    - Metrics exporters
    - User analytics
    - Dashboard for operational health

12. **Deployment Architecture**
    - Next.js app (Vercel)
    - FastAPI backend (container on ECS Fargate or Railway)
    - Postgres (managed, RDS or Neon)
    - Engine (runs alongside FastAPI)
    - Secrets management

13. **Testability Notes for Murat**
    - E2E test scenarios (signup → first session → billing)
    - Workspace isolation tests
    - Billing reconciliation tests
    - Webhook delivery reliability tests
    - Load tests for live view streaming

14. **Launch Checklist**
    - Pre-launch: domain, SSL, Stripe activation, Clerk setup
    - Launch day: marketing copy, pricing page live, landing page hero
    - Post-launch: customer feedback collection, iteration pipeline

15. **Open Questions**
    - Pricing tier decisions needing stakeholder input
    - Trial policy decisions

## CONSTRAINTS

- Do NOT write implementation code (Amelia + frontend developer's job)
- Do NOT over-engineer the UI (this is POV, not production-scale)
- Do NOT add features beyond what's needed for first POV
- DO prioritize "time to first result" above all else
- DO make billing bulletproof (reconciled against Pi-Mono)
- DO keep the "Built With Praxis" dashboard as the hero marketing asset

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\shell\architecture.md

## AFTER YOU FINISH

Signal readiness for Murat (E2E + billing reconciliation test design), then
Amelia + any frontend support for implementation.

After Stage 7 completes, Praxis is ready for first POV delivery. The POV
playbook (in praxis-build-plan.md Part 9) takes over from there.
```

---

## PRE-SALES CHECKPOINT — THE LAUNCH

After Stage 7, everything is in place:

1. **Engine:** Proven multi-agent reasoning with measurable quality improvement
2. **Measurement:** Self-demonstrating savings across 12 weeks of build data
3. **UI:** Customer can go signup → first result in < 10 minutes
4. **Billing:** Pi-Mono-reconciled Stripe metering
5. **Marketing asset:** "Built With Praxis" public dashboard

**Launch announcement (paraphrased from build plan Part 8):**

> "We built Praxis using Praxis. For the entire build cycle, every line of
> code was orchestrated through the same multi-agent system you can buy today.
> Total cost: $X. Savings: Y% vs baseline. Quality improvement: Z% vs
> single-agent on blind eval. Praxis is now available. First POV: 5-day
> delivery."

This is where you go from "building" to "selling."
