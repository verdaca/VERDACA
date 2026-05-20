# Stage 4 — Tool Library Requirements (4.0.1 Elicitation Output)

**Session:** Praxis Stage 4 / Step 4.0.1 — Tool Library Curation
**Facilitator:** Carson (Elite Brainstorming Specialist)
**Date:** 2026-04-13
**Output contract owner:** Andrey
**Downstream consumer:** Winston (Architect), Stage 4.1 `architecture.md` §6 Tool Library Catalog
**Authority:** This document is binding input to Winston per Pipeline.md Section 4.5. Winston MUST anchor §6 on this catalog; exclusions and additions require rationale tied to this file.

---

## 1. Session Frame & Method Summary

### Frame (locked)
- **Goal:** Produce a prioritized (P0/P1/P2) catalog of MCP-ecosystem tools that Winston will anchor Stage 4 `architecture.md` §6 on, so Winston does not invent the tool library from scratch.
- **Constraint:** MCP ecosystem only — per `stage-4-winston-prompt.md` "Do NOT invent new tools — use MCP ecosystem."
- **Scope boundary:** Curation & justification round, not engineering. Tool *implementation*, sandbox mechanism design, MCP SDK choice, and intake-protocol mechanics are Winston's job. I supply the catalog and the criteria; Winston designs the enforcement.
- **Hard rule:** No tool enters this file without an explicit (persona, hat) anchor.
- **Compliance envelope:** Every tool must be traceable against Memory Part A–E requirements (especially R11 cross-tenant, R30 zero-retention, R31 tenant-scoped keys, R36 residency, R53 telemetry allowlist, R57 Pi-Mono CostEvents).

### Method
- **Primary:** Role Playing — 5 customer personas (buyers of Praxis who direct the 16 BMAD agents)
  1. **Strategic Advisor** — PINNED to single-client-engagement mode (one deployment per client engagement) to respect R11
  2. **SMB Founder** — 10–50 person company, lean ops, no internal strategy team
  3. **Enterprise COO** — 500–5000 person company, SSO-mandatory, audit-heavy
  4. **DevOps Engineer** — Platform/infra engineer deploying Praxis inside a host org
  5. **Compliance Officer** — GRC function; SOC2/ISO27001/GDPR/HIPAA posture
- **Secondary:** Six Thinking Hats overlay — **W → Y → B → G → Blue** (Red dropped: evidence round, not feelings round)
  - **White** — known/proven tools already in persona's daily workflow
  - **Yellow** — strong candidates with clear value
  - **Black** — risk pass (security, auth, egress, compliance blast radius, Memory-req violations)
  - **Green** — non-obvious tools the persona wouldn't request but should get
  - **Blue** — curation meta-policy (persona-independent; consolidated across all five personas)
- **Loop:** 5 personas × 5 hats = 25 logical cells. Blue cells consolidate into a single persona-independent section.

### Persona ↔ Agent Mapping (who each persona directs among the 16 BMAD agents)
| Persona | Primary BMAD agent directs |
|---|---|
| Strategic Advisor | Mary (Analyst), Victor (Innovation), John (PM), Sophia (Storyteller), Caravaggio (Presentation) |
| SMB Founder | Mary, Victor, John, Bob (SM), Sally (UX) |
| Enterprise COO | Mary, Winston, Murat, Dr. Quinn, Victor |
| DevOps Engineer | Amelia (Dev), Murat, Quinn (QA), Winston, Barry (Quick Flow) |
| Compliance Officer | Paige (Tech Writer), Murat, Dr. Quinn, (observer over all) |

---

## 2. Matrix Coverage Table

**Methodology transparency** — which cells produced material vs. were collapsed, with rationale.

| Persona ↓ / Hat → | White | Yellow | Black | Green | Blue (meta) |
|---|---|---|---|---|---|
| Strategic Advisor | ✅ 5 items | ✅ 4 items | ✅ 4 items | ✅ 4 items | ⇢ consolidated |
| SMB Founder | ✅ 5 items | ✅ 4 items | ✅ 4 items | ✅ 4 items | ⇢ consolidated |
| Enterprise COO | ✅ 5 items | ✅ 6 items | ✅ 5 items | ✅ 5 items | ⇢ consolidated |
| DevOps Engineer | ✅ 5 items | ✅ 8 items | ✅ 6 items | ✅ 5 items | ⇢ consolidated |
| Compliance Officer | ✅ 5 items | ✅ 5 items | ✅ 5 items | ✅ 4 items | ⇢ consolidated |

**Structural collapse disclosure:** The Blue column is consolidated into §5 (a single persona-independent meta-policy) rather than produced per-persona. Rationale: meta-policy (inclusion criteria, versioning, auth, intake) is definitionally persona-independent; forcing 5 separate Blue cells would produce artificial differentiation. This is a *structural* collapse known at session start, not a post-hoc political trim.

**Genuine collapses:** None. Every White/Yellow/Black/Green cell produced material on genuine attempt. No cell was collapsed for convenience.

**Novel architectural questions surfaced** (for Winston decision, not Carson decision): 2, both documented in §6 Winston Handoff. Neither triggered a mid-session pause because both were *surfacing* decisions (route to Winston), not *deciding* them.

---

## 3. Prioritized Tool List

### P0 — Table Stakes (Launch-Binding, 8 tools)

Tools that appear in ≥3 personas' White or Yellow passes, survive Black Hat scrutiny, exist in the MCP ecosystem, and cover the minimum research → synthesize → produce → verify/observe loop for every persona.

1. **Filesystem (Read / Write / Edit, workspace-bounded)** — `fs-mcp`
2. **Tavily** — `tavily-mcp` (search, extract, crawl, research)
3. **GitHub MCP** — `github-mcp`
4. **Context7 MCP** — `context7-mcp` (library/API docs)
5. **Playwright MCP** — `playwright-mcp` (browser automation, screenshots, UI testing)
6. **PostgreSQL MCP** — `postgres-mcp` (read-only default; write via explicit per-agent allowlist)
7. **Subprocess / Python Sandbox** — `subprocess-mcp` + `python-sandbox-mcp` (split per §6 collision #8)
8. **OpenTelemetry Exporter** — `otel-exporter-mcp`

### P1 — Strong Candidates (Stage 4.3 Amelia if capacity, else early post-launch — 15 tools)

Tools named by ≥2 personas, survive Black Hat with guardrails, MCP ecosystem has a mature server.

1. **Jira MCP** — `jira-mcp`
2. **Confluence MCP** — `confluence-mcp`
3. **Slack MCP (read + webhook)** — `slack-mcp` (Winston §5 lists webhook only; see collision report)
4. **Kubernetes MCP** — `k8s-mcp` (read-only default; destructive ops gated)
5. **Datadog / Grafana / Prometheus MCP** — `observability-mcp` (read-path counterpart to OTel exporter write-path)
6. **Docker MCP** — `docker-mcp`
7. **Stripe MCP** — `stripe-mcp`
8. **Notion MCP** — `notion-mcp`
9. **GitLab MCP** — `gitlab-mcp` (alternative to GitHub for GitLab shops)
10. **PagerDuty MCP** — `pagerduty-mcp`
11. **Semgrep / Trivy / Snyk MCP** — `security-scanner-mcp` (bundle or separate)
12. **HashiCorp Vault MCP (read-only)** — `vault-mcp`
13. **SEC EDGAR MCP** — `sec-edgar-mcp`
14. **Google Workspace MCP (Drive / Sheets / Gmail)** — `google-workspace-mcp`
15. **OpenTelemetry Collector MCP (write-side)** — `otel-collector-mcp`

### P2 — Deferred (Stage 5+ Reassess, 22 tools)

Named by only one persona OR high Black Hat red flags OR requires infrastructure Stage 4 hasn't built yet.

1. **Salesforce MCP** — P1 + P3 demand, but cross-engagement/cross-tenant pressure makes R11 compliance fragile; defer until MAC (Stage 5) asymmetry enforcement is proven
2. **Microsoft 365 / Graph MCP** — P3 only; massive OAuth scope; phased rollout via SharePoint subset first
3. **SAP / Oracle ERP MCP** — P3 only; enterprise deal-gate; very complex auth and schemas
4. **Workday MCP** — P3 only; HR data = high-sensitivity blast radius
5. **Okta / Azure AD MCP** — P3 only; directory read (org chart for coordination) is useful but not launch-critical
6. **ServiceNow MCP** — P3 only; large-enterprise gate
7. **Tableau / PowerBI MCP** — P3 only; embedded-PII-in-dashboard risk breaks R53 cleanly
8. **HubSpot MCP** — P2 only; CRM PII
9. **QuickBooks MCP** — P2 only; financial sensitivity
10. **Shopify MCP** — P2 only; ecommerce niche
11. **Terraform MCP** — P4 only; destructive power requires human-in-loop workflow not yet designed at Stage 4
12. **AWS / GCP / Azure CLI MCP** — P4 only; same destructive-blast-radius concern
13. **Ansible MCP** — P4 only
14. **SIEM (Splunk / Sumo Logic) MCP** — P5 only; often air-gapped, enterprise-gated
15. **Vanta / Drata / Secureframe MCP** — P5 only; niche attestation platforms
16. **DLP Scanner MCP** — P5 only; regulated-data handling, needs consent trail
17. **arXiv / Google Scholar MCP** — P1 only; research tier enhancement
18. **News RSS MCP** — P1 only; signal tier enhancement
19. **dbt / LookML Metadata MCP** — P3 only; data catalog niche
20. **LocalStack MCP** — P4 only; dev-environment testing helper
21. **OpenSCAP / CIS Benchmark MCP** — P5 only; compliance scan niche
22. **Discord Webhook** — P2 only; superseded by Slack for core workflow (see collision #3)

---

## 4. Per-Tool Cards (P0 Full Depth, P1 Summary, P2 Deferred Headers)

### 4.1 P0 Full Cards

#### P0-1. Filesystem (Read / Write / Edit)
- **MCP provenance:** Official Anthropic MCP filesystem server (`mcp-server-filesystem`), production-mature
- **Primary BMAD callers:** Amelia, Barry, Paige, Winston, Quinn, Sophia, Caravaggio (effectively all 16 via their output paths)
- **Customer personas that surfaced it:** P1 (White), P2 (White), P3 (White), P4 (White), P5 (White) — **5/5 personas, White Hat unanimous**
- **Hats:** White (all personas) + Yellow (P1, P5 — foundational) + Black (all personas)
- **Risk notes (Black Hat):**
  - Workspace sandbox must bound reads/writes to a per-deployment tenant-scoped directory (R36 residency, R11 no cross-tenant path)
  - Must NOT read from `.env`, `.ssh/`, `credentials.*`, or any secret path (Winston §12 explicit)
  - Write operations require per-agent allowlist (Winston §9); some agents are read-only
- **Memory-reqs compliance flags:** R11 ✅ (per-deployment path scope) · R36 ✅ (deployment-local by construction) · R53 ⚠️ (file contents must not leak to central observability — enforce at telemetry layer not tool layer)
- **CostEvent:** Negligible; file I/O emits token-denominated events only when file contents enter an LLM context

#### P0-2. Tavily (Search / Extract / Crawl / Research)
- **MCP provenance:** Tavily official MCP server, production mature (widely deployed)
- **Primary BMAD callers:** Mary (market/competitive research), Victor (disruption signals), John (PM competitive analysis), Dr. Quinn (root cause external research), Sophia (narrative research)
- **Customer personas that surfaced it:** P1 (White + Yellow — research IS the deliverable), P2 (White — lean competitive intel), P3 (White — external market intel), P5 (White — regulatory research). **4/5 personas.**
- **Hats:** White (P1, P2, P3, P5) + Yellow (P1 elevated — "research is the deliverable") + Black (rate limits, cost spikes)
- **Risk notes (Black Hat):**
  - Rate limits + cost spikes during deep-research bursts — Pi-Mono R57 CostEvent emission MANDATORY with hard budget cap per task
  - API key is tenant-scoped per R31 (one Tavily key per Praxis deployment)
  - Tavily results include third-party content — anti-hallucination: results must flow into agent context, never be cached in Memory as "tenant facts"
- **Memory-reqs compliance flags:** R31 ✅ (tenant key) · R57 ✅ (CostEvent hard requirement) · R53 ⚠️ (search queries must NOT leak to central obs; query text is telemetered as hash-only)
- **CostEvent:** HIGH — every search is $0.001–$0.01; Pi-Mono integration non-negotiable

#### P0-3. GitHub MCP
- **MCP provenance:** Official GitHub MCP server (`github/github-mcp-server`), production mature
- **Primary BMAD callers:** Amelia, Barry (code), Quinn (test artifacts), Murat (CI integration), Winston (reference repo reads), Bob (issue/story management), Paige (docs repos)
- **Customer personas that surfaced it:** P1 (tech-heavy engagements, M&A diligence), P2 (technical founders), P3 (eng org visibility), P4 (White — bread and butter), P5 (audit reads). **5/5 personas.**
- **Hats:** White (P2, P3, P4, P5) + Yellow (P4 elevated) + Black (write surface, secret scanning)
- **Risk notes (Black Hat):**
  - Write operations (PR create, merge, branch delete) require explicit per-agent allowlist — default read-only
  - Private repos: tenant-scoped PAT/GitHub App credentials per R31 (no shared Praxis GitHub org account)
  - Auto-merge / auto-close surfaces are P4 red flags — Winston §9 privilege-prevention must gate these
  - Secret scanning: GitHub MCP must NOT return repo files containing detected secrets; DLP layer at tool boundary
- **Memory-reqs compliance flags:** R11 ✅ (per-deployment GitHub App) · R31 ✅ (tenant-scoped creds) · R53 ⚠️ (repo contents MUST NOT flow to central obs; only aggregate metrics)
- **CostEvent:** LOW per call, but high frequency; track aggregate per workflow

#### P0-4. Context7 MCP
- **MCP provenance:** Official Context7 MCP server (Upstash), production mature
- **Primary BMAD callers:** Winston (library docs during architecture), Amelia (API syntax during impl), Quinn (framework docs for test scaffolding), Barry (Quick Flow spec-and-build), Paige (doc standards)
- **Customer personas that surfaced it:** P1 (tech-engagement reference), P3 (enterprise eng org docs), P4 (daily infra library docs). **3/5 personas.**
- **Hats:** White (P1, P3, P4) + Yellow (P4 — reduces hallucinated API calls materially) + Black (content provenance)
- **Risk notes (Black Hat):**
  - Content provenance: Context7 returns third-party library documentation — agents must not cache these as "tenant knowledge" in Memory
  - Rate limits on free tier; P3 enterprise persona needs paid tier + tenant-scoped key per R31
  - Version mismatch: library version returned may differ from version in deployment's `requirements.txt` — agents must pass version pin explicitly
- **Memory-reqs compliance flags:** R31 ✅ (per-tenant API key) · R57 ✅ (per-query CostEvent emission) · R53 ✅ (doc lookups are not tenant data)
- **CostEvent:** LOW — library docs are cheap; batch queries amortize

#### P0-5. Playwright MCP
- **MCP provenance:** Microsoft official Playwright MCP server (`@playwright/mcp`), production mature
- **Primary BMAD callers:** Quinn (E2E test generation + execution), Sally (UX — screenshot capture, accessibility audit), Mary (competitor UX + pricing page capture), Murat (E2E test architecture, visual regression), Barry (Quick Flow UI verification)
- **Customer personas that surfaced it:** P1 (competitor capture), P2 (founder UX analysis), P4 (test authoring for Quinn). **3/5 personas.**
- **Hats:** White (P1, P2, P4) + Yellow (P4 — Quinn/Murat need it) + Black (egress, headless browser blast radius)
- **Risk notes (Black Hat):**
  - Headless browser egress: Playwright can POST to third-party sites visited — data exfiltration surface for regulated-industry P3/P5 deployments
  - Credential capture: browser can log into sites with stored creds → must be tenant-scoped credential vault per R31
  - Network egress policy: must be configurable per deployment (allowlist of domains) for compliance-heavy personas
  - Screenshot storage: images may contain PII → must hit R53 allowlist (screenshots NEVER go to central obs, only aggregate metrics)
- **Memory-reqs compliance flags:** R31 ✅ (tenant browser creds) · R36 ✅ (no cross-region egress by default) · R53 ⚠️ (screenshot/page-content allowlist enforcement at telemetry boundary)
- **CostEvent:** MEDIUM — browser time + memory, emit per session

#### P0-6. PostgreSQL MCP
- **MCP provenance:** Official Postgres MCP server (multiple available; recommend Crystal DBA MCP for read-only + explicit query-builder MCP for authored writes)
- **Primary BMAD callers:** Amelia (schema queries), Quinn (test data), Mary (product analytics), Barry (rapid impl)
- **Customer personas that surfaced it:** P2 (product analytics DB), P3 (enterprise data warehouse), P4 (database ops). **3/5 personas.**
- **Hats:** White (P2, P3, P4) + Yellow (P4, P3 — enterprise data ops) + Black (query surface, PII, write blast radius)
- **Risk notes (Black Hat):**
  - READ-ONLY default — write operations require explicit per-agent, per-table allowlist (Winston §9)
  - No raw query builder exposed to agents (parallels Memory R8 facade discipline — typed query methods only)
  - PII in query results must NOT flow to central obs (R53); hash-only telemetry
  - Connection pool sizing: parallels Memory NR-SC-R2 strawman; Winston must define for Runtime-owned connections
  - SQL injection via agent-composed queries: parameterized queries only; agents cannot construct raw SQL strings
- **Memory-reqs compliance flags:** R8 (facade) — echoed in tool design · R11 ✅ (per-deployment DB credentials) · R31 ✅ · R53 ⚠️ (query result content allowlist)
- **CostEvent:** LOW per query; aggregate-heavy usage → session-level events

#### P0-7. Subprocess + Python Sandbox (split per collision #8)
- **MCP provenance:** Multiple (no single canonical); recommend `python-sandbox-mcp` (containerized Python execution) + `subprocess-mcp` (tightly bounded binary allowlist wrapper)
- **Primary BMAD callers:**
  - **Python sandbox (broad):** Amelia, Barry, Quinn, Murat, Mary (data munging), Paige (doc generation scripts)
  - **Subprocess (narrow):** Amelia, Barry, Quinn ONLY — for running `pytest`, `ruff`, `mypy`, `npm test`, etc.
- **Customer personas that surfaced it:** P4 (White — daily tool), all others via proxy (agents use it under the hood)
- **Hats:** White (P4) + Yellow (P4 — table stakes for DevOps tier) + Black (single highest-risk tool in library)
- **Risk notes (Black Hat) — CRITICAL:**
  - This is the single highest-risk tool in the library — sandbox escape = full host compromise
  - Winston §9 sandboxing is NON-OPTIONAL; subprocess without sandbox is an automatic P2 defer
  - Per-agent, per-binary allowlist: e.g., Amelia can run `pytest`, `ruff`, `mypy`, `python`, `pip` but NOT `curl`, `ssh`, `nc`, `/bin/sh`
  - Network isolation: Python sandbox must default to no-network; subprocess commands inherit no-network unless explicit opt-in
  - Resource caps: CPU-time, memory, wall-time bounded by Pi-Mono budget enforcement (R57)
  - Filesystem scope: tied to P0-1 filesystem bounds
- **Memory-reqs compliance flags:** R11 ✅ (no cross-tenant filesystem path) · R31 ✅ (no secret access) · R57 ✅ (MUST emit CostEvent for execution time)
- **CostEvent:** HIGH variance — a runaway loop can burn budget; hard time/memory/cost caps non-negotiable

#### P0-8. OpenTelemetry Exporter
- **MCP provenance:** OTel official exporter patterns wrapped as MCP tool
- **Primary BMAD callers:** ALL 16 agents via framework integration (not direct invocation); Murat for observability test strategy
- **Customer personas that surfaced it:** P4 (White — operational backbone), P5 (Yellow — audit trail emission), implicit for P1–P3 via Pi-Mono R57 integration
- **Hats:** White (P4) + Yellow (P5 — compliance depends on trace emission) + Black (R53 leakage vector)
- **Risk notes (Black Hat):**
  - THIS TOOL IS THE R53 EXPOSURE POINT — if not strictly configured, raw content leaks to central observability
  - Configuration MUST use field allowlist at emit time (mirrors Memory R51 TelemetryEvent schema)
  - NO raw query content, NO retrieval results, NO embeddings, NO tenant-data field values — only numeric/aggregate metrics + allowlisted structured fields
  - Backend must be configurable per deployment (default: tenant-local sink; central obs opt-in only after allowlist verification)
- **Memory-reqs compliance flags:** R51 ✅ (schema allowlist discipline mirrored) · R53 ✅ (hard gate — tool is the enforcement point) · R54 ✅ (tenant-local sink support)
- **CostEvent:** This tool EMITS CostEvents for other tools; self-cost is the collector infrastructure, not per-call

### 4.2 P1 Summary Cards

Each P1 tool has (personas, hats, top risk, top BMAD caller). Full cards deferred to Stage 4.1 Winston expansion.

1. **Jira MCP** — personas P3 + P5 · hats W+Y · risk: SSO/SAML required for enterprise · caller: Bob, Murat, Paige
2. **Confluence MCP** — personas P3 + P5 · hats W+Y · risk: large content egress; R53 allowlist at tool boundary · caller: Paige, Mary, Dr. Quinn
3. **Slack MCP (full, not just webhook)** — personas P2 + P3 · hats W+Y+B · risk: DM/channel privacy, per-channel allowlist · caller: Bob, Mary, John
4. **Kubernetes MCP** — persona P4 · hats W+Y+B · risk: destructive ops, requires tiered permission · caller: Amelia, Murat, Winston
5. **Datadog / Grafana / Prometheus MCP (read-path)** — personas P4 + P5 · hats W+Y · risk: dashboards may contain PII, R53 at tool boundary · caller: Murat, Dr. Quinn
6. **Docker MCP** — persona P4 · hats W+Y · risk: image pull from untrusted registries · caller: Amelia, Quinn, Barry
7. **Stripe MCP** — persona P2 · hats Y+B · risk: PCI-adjacent, customer PII · caller: Mary, Victor
8. **Notion MCP** — persona P2 · hats Y+G · risk: broad workspace access · caller: Paige, Mary, Sally
9. **GitLab MCP** — persona P4 · hats W (alternative to GitHub) · caller: same as GitHub MCP
10. **PagerDuty MCP** — persona P4 · hats Y · risk: incident data sensitivity · caller: Murat, Dr. Quinn
11. **Security Scanner MCP (Semgrep / Trivy / Snyk)** — personas P4 + P5 · hats Y+G · risk: false positives generating noise · caller: Murat, Amelia
12. **Vault MCP (read-only)** — persona P4 · hats Y+B · risk: extreme — mis-config = total compromise · caller: Amelia, Barry ONLY
13. **SEC EDGAR MCP** — persona P1 · hats G · risk: none significant (public data) · caller: Mary, Victor
14. **Google Workspace MCP** — persona P2 · hats Y+B · risk: OAuth scope sprawl; data egress surface · caller: Mary, John, Paige
15. **OTel Collector MCP (write-side)** — persona P4 · hats G · risk: same R53 concerns as exporter · caller: Murat (infra instrumentation)

### 4.3 P2 Deferred Headers Only

See §3 P2 list for the 22 deferred tools with one-line rationale each. Full cards are produced at the Stage 5+ reassessment ceremony when those tools promote to P1.

---

## 5. Blue Hat — Consolidated Meta-Policy

This section is the persona-independent meta-policy consolidating all five personas' Blue Hat input into a single unified curation framework.

### 5.1 Inclusion Criteria (gates for any tool entering the registry)

A tool may enter the Praxis tool library ONLY if it passes all seven gates:

1. **MCP ecosystem gate** — Tool is served via an official or high-quality community MCP server
2. **Persona anchor gate** — Tool is named by at least one customer persona in a White or Yellow pass
3. **Black Hat survival gate** — Tool survives Memory-reqs compliance check (R11, R30, R31, R36, R53 specifically) with no architectural waiver required
4. **Per-agent allowlist gate** — Tool can be gated per-agent via Winston §9 allowlist mechanism (no "available to all agents by default")
5. **CostEvent gate** — Tool emits or can be wrapped to emit Pi-Mono CostEvents per R57 — no silent-cost tools admitted
6. **Read/write separation gate** — Tool supports read-only mode; if write-capable, must expose a capability descriptor distinguishing read vs. write so P0 tier can default to read-only
7. **Sandbox compatibility gate** — Tool runs within Winston §9 sandbox boundary; tools that require breaking sandbox (raw shell, root privileges, host network) are auto-P2 at best

### 5.2 Versioning Cadence

- Each Praxis release pins tools to specific MCP server versions in a `tools-lock.toml` file (parallel to Python's `poetry.lock`)
- Upgrades trigger a regression test against affected-persona workflows before merging
- Breaking upstream MCP change → stage the old version for one release cycle while migrating
- Security advisory on a pinned version → emergency upgrade path with expedited Black Hat re-check

### 5.3 Auth Model

- **Tenant-scoped credentials only** (R31) — no shared Praxis-org accounts across deployments
- **Credential flow:** deployment config → tool initialization at startup → in-memory for runtime, never persisted in Memory
- **Secret storage:** Vault-backed in production; `.env` with `DEPLOYMENT_SECRETS_PATH` env var in dev, redacted from all logs
- **OAuth scopes:** minimum-scope principle — each agent's allowlist includes only the OAuth scopes it needs (e.g., Mary doesn't need GitHub write scopes)
- **API-key rotation:** handled by deployment operator via config reload — Runtime MUST support hot-reload of tool credentials without process restart
- **Enterprise tier escalation:** P3 persona tools additionally require SSO/SAML support; OAuth-only tools are P2-capped for enterprise deployments

### 5.4 Intake Protocol (Carson's criteria; Winston designs the mechanics)

Criteria for adding a tool to the registry post-launch:

1. **Request trigger:** New tool request from customer, persona evolution, or MCP ecosystem maturation
2. **Gate pass:** Tool passes all seven §5.1 inclusion gates
3. **Black Hat re-pass:** Run current Memory-reqs + Winston §9 security model against the tool — full card produced
4. **Persona + Hat anchor:** Assign at least one persona and at least one hat that surfaced it
5. **P2 incubation:** Add to P2 for minimum one Praxis release cycle of observation and telemetry
6. **P1 promotion:** Promote to P1 if adoption metrics positive AND zero security incidents AND 2+ personas find it valuable
7. **P0 promotion:** Promote to P0 only if evidence of universal foundational need from ≥3 personas AND operational maturity (defined as: ≥2 release cycles at P1, zero unpatched vulnerabilities, upstream MCP server in active maintenance)

### 5.5 P0 Count Defense

**The P0 count is 8.** Defense:

This is the minimum set that gives every one of the 5 customer personas at least 3 tools covering their primary workflow loop (research → synthesize → produce → verify/observe) without exceeding Stage 4.4 Murat's testable security surface. Persona coverage breakdown:

| Persona | P0 tools covering them | Loop coverage |
|---|---|---|
| Strategic Advisor | fs, Tavily, GitHub, Context7, Playwright | 5/8 — full research + produce loop |
| SMB Founder | fs, Tavily, GitHub, Playwright, PostgreSQL | 5/8 — full loop incl. product analytics |
| Enterprise COO | GitHub, Context7, PostgreSQL | 3/8 — foundational only; specialty P1 |
| DevOps Engineer | GitHub, subprocess, PostgreSQL, OTel | 4/8 — foundational only; specialty P1 |
| Compliance Officer | fs, GitHub, Tavily, Context7, OTel | 5/8 — full audit + research loop |

**Going below 8:** Starves either P3 (enterprise) or P4 (devops) of their minimum viable surface — enterprise personas would lack GitHub + Context7 for eng org visibility; devops would lack subprocess for their core CI workflow. Either starvation makes those personas unsellable at launch.

**Going above 8:** Each incremental P0 tool absorbs ~3–5 Stage 4.4 Murat security test specs (sandbox boundary, allowlist enforcement, error handling, cost attribution, privilege escalation). At 8 tools, Murat's security test burden is ~32 specs; at 12 tools, it's ~50 specs. Stage 4's sandbox architecture has not yet proven itself under load; inflating the P0 surface beyond 8 demands architectural proof that Stage 4 hasn't yet delivered.

**Why not 6 or 7?** Dropping Playwright (→7) starves P1 + P2 of UX/competitor capture and Quinn of E2E testing. Dropping Context7 (→6) forces Amelia/Winston into hallucinated library API calls, contradicting Winston §9 "LLM must select from whitelist, not generate names" principle at the *doc* layer.

**Why not 9 or 10?** The first candidate for a 9th P0 tool is Jira MCP (from P3 + P5 demand). But Jira is persona-specific (enterprise-biased); no P2/P4 White Hat named it. Promoting it to P0 privileges enterprise over SMB/advisor, which is a business decision not a curation decision — explicitly out of scope for this session. Same logic for Slack, Confluence, and Kubernetes.

**Conclusion:** P0 = 8 is the point where additional tools cost more in security-test burden than they gain in persona coverage. The line holds.

### 5.6 Blast Radius Classes (informs Winston §9 sandbox tiering)

Consolidated Blue Hat output from Black Hat passes across all 5 personas. Winston should tier sandbox policies according to this blast-radius classification:

| Class | Blast radius | Example tools | Default mode |
|---|---|---|---|
| **Class A** — Inert | Read-only, no egress beyond request scope | Context7, Tavily (read), SEC EDGAR | Broadly allowlisted |
| **Class B** — Scoped egress | Read + network egress to known public APIs | GitHub read, Jira read, Confluence read | Per-agent allowlist, rate-limited |
| **Class C** — Tenant data surface | Read/write within tenant-scoped datastores | PostgreSQL, Filesystem, Notion | Per-agent allowlist, read-write separation mandatory |
| **Class D** — Destructive / escalation-capable | Write to external state, can cause real-world change | Kubernetes, Terraform, Vault write, subprocess | Per-agent allowlist + per-operation approval (human-in-loop if destructive) |
| **Class E** — Unbounded | Sandbox-escape capable if mis-configured | Raw shell, root privilege subprocess | **Not admitted; auto-P2 at best** |

---

## 6. Winston Handoff — §5 Collision Report & Decision Escalations

This section is the highest-value output for Winston. Collisions with his Stage 4 §5 seed list, and two decisions that only Winston should make.

### 6.1 Agreements (8/10 of Winston's seed list → P0)

Winston's seed list overlaps P0 at 8 tools: **fs, Tavily, GitHub, Context7, Playwright, PostgreSQL, subprocess (split), OTel exporter**. High structural alignment — Winston's architectural instinct is well-calibrated to the persona evidence.

### 6.2 Collision #1 — Slack: DEMOTE to P1, ELEVATE from webhook to full MCP

- **Winston's seed:** Slack webhook
- **This session's placement:** P1 Slack MCP (read + write)
- **Rationale:** Webhook is write-only; personas P2 and P3 both need agents to *read* Slack (Mary synthesizing team discussions, Bob preparing sprint status from sprint-planning channels, Dr. Quinn ingesting incident threads for root cause analysis). Webhook-only is insufficient. Full Slack MCP upgrades the capability but requires per-channel allowlist (agent cannot read DMs or channels without explicit opt-in from deployment config).
- **Recommendation for Winston §6:** Replace "Slack webhook" entry with "Slack MCP (read + webhook write)" and add a per-channel allowlist design requirement in §6 sub-point.

### 6.3 Collision #2 — Discord: DROP to P2 (deferred)

- **Winston's seed:** Discord webhook
- **This session's placement:** P2 deferred
- **Rationale:** Only P2 (SMB Founder) named Discord, and even then as community-tribe adjacent rather than core workflow. Slack dominates the enterprise and mid-market segment; Discord's customer overlap with Praxis's target personas is thin. Defer; reassess at Stage 6 if SMB motion generates Discord demand.
- **Recommendation for Winston §6:** Drop Discord webhook from the launch catalog. Note in §12 Open Questions as "Stage 6 re-evaluation trigger: SMB customer traction."

### 6.4 Collision #3 — ADD Jira MCP at P1

- **Winston's seed:** Not listed
- **This session's placement:** P1
- **Rationale:** P3 (Enterprise COO) and P5 (Compliance Officer) BOTH named Jira as central to their workflows. Enterprise personas cannot function without a ticketing integration. Jira MCP exists in the ecosystem, is production-mature, and maps cleanly to Bob (SM), Murat (test findings → Jira tickets), and Paige (docs-to-tickets traceability).
- **Recommendation for Winston §6:** Add Jira MCP as a named entry. Note that SSO/SAML support is required for P3 tier.

### 6.5 Collision #4 — ADD Confluence MCP at P1

- **Winston's seed:** Not listed
- **This session's placement:** P1
- **Rationale:** Same as Jira — P3 + P5 both named Confluence. Enterprise knowledge bases run on Confluence; omitting it means P3 deployments cannot retrieve internal policy or engineering docs via Memory-free agent paths.
- **Recommendation for Winston §6:** Add Confluence MCP as a named entry. Highlight R53 allowlist at tool boundary (Confluence pages may contain large amounts of content that must NOT flow to central observability).

### 6.6 Collision #5 — ADD Kubernetes MCP at P1

- **Winston's seed:** Not listed
- **This session's placement:** P1
- **Rationale:** P4 (DevOps Engineer) is a primary Praxis customer persona, and their core workflow depends on cluster observation, rollout inspection, and pod-level diagnosis. Kubernetes MCP exists; omitting it means P4 deployments cannot do DevOps work through Praxis agents.
- **Recommendation for Winston §6:** Add Kubernetes MCP as a named entry. BUT — elevated sandbox requirements: default mode is read-only; destructive operations (pod delete, deployment apply, namespace create) require Class D approval pattern per §5.6.

### 6.7 Collision #6 — ADD Datadog/Grafana/Prometheus MCP (observability READ-path) at P1

- **Winston's seed:** OTel exporter (write-path)
- **This session's placement:** Additional P1 entry for the READ-path complement
- **Rationale:** Winston covers the emit side (agents emit telemetry via OTel). He does not cover the read side (agents query observability for diagnosis). P4 and P5 both named observability read as central. Without a read-path, Murat cannot execute observability-informed test strategy and Dr. Quinn cannot do ops-anchored root cause analysis.
- **Recommendation for Winston §6:** Pair every OTel exporter with an observability read-path tool; document the read/write symmetry explicitly.

### 6.8 Collision #7 — CLARIFICATION on Python sandbox vs. subprocess split

- **Winston's seed:** "Python sandbox, subprocess wrapper" (appears as one item)
- **This session's placement:** P0 with explicit split into two tools with distinct allowlists
- **Rationale:** Bundling these into one conceptual tool obscures a critical asymmetry. Python sandbox (containerized Python execution with no-network default) is relatively broad-use — Mary can run data munging, Paige can run doc generators. Subprocess (arbitrary binary execution) is narrow-use and tightly bounded — only Amelia/Barry/Quinn can run `pytest`, `ruff`, etc., with per-binary allowlists. Treating them as one tool creates an incentive for agents to use subprocess where Python sandbox would suffice, inflating risk.
- **Recommendation for Winston §6:** Split into two explicit tool entries in §6. Assign Python sandbox to Class C (tenant data surface); assign subprocess to Class D (destructive/escalation-capable). Per-agent allowlist rules differ.

### 6.9 Novel Architectural Decisions Requiring Winston (not Carson)

Two decisions arose during the matrix that I am *surfacing*, not *deciding*. These are escalations to Winston:

#### Decision Escalation #1 — Default read/write mode for P0 tools

**Question:** Should P0 tools (fs, PostgreSQL, GitHub, Playwright) default to read-only mode across all agents, with write mode requiring explicit per-agent allowlist? Or should read/write be per-agent from the start, with no global default?

**Why it matters:** Read-only default gives operators a more conservative security posture and aligns with Class C/D discipline from §5.6 — but may create friction for Amelia/Barry whose jobs inherently require write operations. Per-agent from the start is more operationally flexible but shifts the "safe default" burden onto every deployment's configuration.

**My bias (surfacing, not deciding):** Read-only default + per-agent write allowlist aligns with the Memory R8 facade discipline precedent ("no raw query builder; all retrieval paths are named typed methods"). But Winston owns this decision because it shapes §9 security model.

**Where it lands:** Winston §9 Security Model + §6 Tool Library Catalog default-mode specification.

#### Decision Escalation #2 — Human-in-loop approval for Class D destructive operations

**Question:** Stage 4 has a "destructive action" blast radius category (Class D in §5.6 — Kubernetes write, Terraform apply, Vault write, etc.). Does Stage 4 include a human-in-loop approval workflow for these operations, or is destructive-op approval deferred to a later stage (POV harness Stage 7?) while Stage 4 simply keeps those tools P2-deferred?

**Why it matters:** If Stage 4 includes the workflow, Class D tools (Kubernetes write, Terraform, Vault write) can be P1 with the workflow as their safety mechanism. If Stage 4 does not include the workflow, Class D tools MUST be P2 until the workflow ships, which defers P4 DevOps persona value. My current P1 placements for Kubernetes MCP and Vault (read-only) assume Kubernetes write is P2 and Vault write is P2 until the workflow lands — but I need Winston to confirm this architectural framing.

**My bias (surfacing, not deciding):** The human-in-loop approval workflow is architecturally substantial — probably a full Stage 4 sub-component with its own §section, or a deferred Stage 5/7 concern. Winston must choose.

**Where it lands:** Winston §4 (Spawner design — approval-workflow lifecycle?) OR §12 Open Questions → pinned to a specific later stage.

### 6.10 Summary of Winston's §6 Diff vs. Winston's §5 Seed

Winston's `architecture.md` §6 Tool Library Catalog must reflect:

- **Ratified from §5 (8 tools → P0):** fs, Tavily, GitHub, Context7, Playwright, PostgreSQL, subprocess/Python sandbox (split), OTel exporter
- **Demoted from §5 (1):** Slack webhook → P1 Slack MCP (read + write)
- **Dropped from §5 (1):** Discord webhook → P2 deferred
- **Added at P1 (5 new):** Jira MCP, Confluence MCP, Kubernetes MCP, Observability read-path MCP, OTel collector MCP
- **Open decisions (2):** Read/write default mode; human-in-loop approval workflow scope

Winston is free to challenge any collision, but challenges must cite which persona evidence they are overriding and why.

---

## 7. Deferred-With-Rationale Appendix (Holdback Capture)

Tools that personas wanted but hit a hard DO-NOT line (R11 cross-tenant or non-MCP). Logged for future-Carson at Stage 6 reassessment when the seed corpus / benchmark library / MAC federation conversations open.

### 7.1 R11 Violations (Cross-Tenant Requests)

#### A1. Strategic Advisor — "Cross-engagement framework reuse"
- **Request:** Access to strategic frameworks / patterns used in previous client engagements so a new engagement can bootstrap from accumulated know-how.
- **Violation:** R11 (cross-tenant retrieval is a non-existent code path; single-tenant-per-deployment pin).
- **Why it was tempting:** This is the highest-value feature for Strategic Advisor persona — "learning advisory firm" is the obvious ChatGPT-for-consultants positioning.
- **Stage 6 reassessment trigger:** Curated, *anonymized*, *attested* "strategic patterns seed corpus" per Memory Part B (seed corpus = separate read-only Mem0 collection, versioned, license-attested per R14–R20). This is a BMAD+Tokonomics analogue: the Praxis team curates an anonymized strategic-pattern corpus, licensees bundle it at deployment, and Strategic Advisors read it on their engagement without breaching tenant isolation.
- **Future-Carson note:** This is probably the single highest-value Stage 6 conversation for Strategic Advisor conversion. The frame to use: "What is the BMAD equivalent of a 'strategic patterns library'?"

#### A2. SMB Founder — "Peer founder learning"
- **Request:** "What tools / approaches did other Praxis-using founders find valuable?"
- **Violation:** R11.
- **Why it was tempting:** Network-effect story for SMB persona — "Praxis gets smarter as more founders use it."
- **Stage 6 reassessment trigger:** Industry-tagged seed corpus (parallel to A1 but for founder playbooks). Same Memory Part B contract.
- **Future-Carson note:** Lower priority than A1 — founders are less sophisticated consumers of cross-tenant patterns and the litigation risk of bad advice is asymmetric for smaller customers.

#### A3. Enterprise COO — "Subsidiary federation"
- **Request:** One Praxis instance auditing / orchestrating across multiple subsidiary deployments.
- **Violation:** R11 + R4 (signed manifest drift rule — each deployment has a pinned tenant identity).
- **Why it was tempting:** Genuinely real enterprise requirement — large enterprises have 5–50 subsidiaries and genuinely want cross-sub insights.
- **Stage 5+ reassessment trigger:** NOT a Memory-layer solution. This is a **MAC-level federation overlay** — a higher-tier orchestrator that talks to N Praxis deployments via their public APIs without violating per-deployment tenant isolation. Architectural conversation, not tool-library conversation.
- **Future-Carson note:** Escalate this to Stage 5 Winston as a Stage 5 MAC Engine requirement: "Does MAC support multi-deployment orchestration patterns?" This is the P3 persona's deal-breaker at enterprise scale.

#### A4. Compliance Officer — "Cross-deployment audit roll-up"
- **Request:** Single-pane-of-glass audit view across regulated deployments.
- **Violation:** R11 (and implicitly R37 two-tenant access isolation).
- **Why it was tempting:** Legitimate compliance need — GRC functions genuinely want aggregated audit visibility.
- **Stage 7 reassessment trigger:** POV Harness tier may support a read-only reporting aggregator with strict numeric/allowlisted-field compliance (parallel to R53 for telemetry but for audit logs). This is NOT Memory, not Runtime — it's a Stage 7 reporting overlay.
- **Future-Carson note:** This is P5's parallel to A3 but with stricter read-only contract. Fold into the Stage 5/7 federation conversation, but with explicit audit-only framing.

### 7.2 Non-MCP Ecosystem Requests

#### B1. Enterprise COO — "Microsoft Teams direct protocol"
- **Request:** Native Teams integration (bidirectional messaging, channel reads, meeting transcripts).
- **Violation:** Teams MCP is immature / non-existent at Stage 4 launch (2026-04-13).
- **Stage 6 reassessment trigger:** Microsoft Graph MCP maturity. When Graph MCP can stably read Teams channels with per-channel allowlisting and OAuth scopes, promote to P1.
- **Future-Carson note:** Slack MCP covers ~80% of the workflow for now; Teams holds the enterprise gap. Watch ecosystem.

#### B2. DevOps Engineer — "Raw bash shell tool"
- **Request:** Unconstrained shell execution for diagnostic flexibility.
- **Violation:** Winston §9 sandboxing + §5 subprocess discipline + §5.6 Class E (unbounded = not admitted). Architectural regression.
- **Stage 6 reassessment trigger:** NONE. Raw shell is structurally incompatible with Praxis security posture. Use subprocess with expanded per-binary allowlists if the workflow genuinely needs a broader tool surface.
- **Future-Carson note:** Do not reopen this. It's the one request that should stay permanently closed — raw shell is the canonical sandbox-escape vector.

#### B3. Compliance Officer — "Physical document PII redaction (scan + OCR + redact)"
- **Request:** Workflow tool for redacting PII from physical documents (scanned forms, paper policies).
- **Violation:** Outside MCP ecosystem; specialized OCR + redaction is not currently served by a production MCP server.
- **Stage 6 reassessment trigger:** MCP ecosystem maturation — document AI tools are emerging and may produce MCP-compatible servers.
- **Future-Carson note:** Low urgency — physical document workflows are a small minority of compliance work. Track but don't prioritize.

---

## 8. Session Metrics

- **Personas explored:** 5 / 5
- **Hats applied:** 5 / 6 (Red dropped per Andrey-locked method)
- **Cells produced material:** 20 / 20 (White/Yellow/Black/Green; Blue consolidated)
- **Political collapses:** 0
- **Structural collapses:** 1 (Blue cells consolidated — disclosed in §2)
- **Tools on final catalog:** 45 (8 P0 + 15 P1 + 22 P2)
- **Tools in deferred appendix:** 7 (4 R11 violations + 3 non-MCP)
- **Winston §5 collisions surfaced:** 8 (1 agreement cluster + 2 demotions + 5 additions)
- **Novel architectural escalations to Winston:** 2 (read/write default mode, human-in-loop approval workflow scope)
- **Halt conditions triggered:** 0
- **R11 invocations:** 4 (logged to §7)
- **Non-MCP invocations:** 3 (logged to §7)

---

## 9. Winston Handoff Checklist

For Winston to reference this document during Stage 4.1 `architecture.md` §6 drafting:

- [ ] §6 Tool Library Catalog names the 8 P0 tools explicitly
- [ ] §6 incorporates the 5 P1 additions (Jira, Confluence, Kubernetes, observability read-path, OTel collector)
- [ ] §6 splits Python sandbox and subprocess into two entries with distinct allowlist policies (collision #7)
- [ ] §6 replaces Slack webhook with Slack MCP (read + write) per collision #1
- [ ] §6 drops Discord webhook or documents it as P2 per collision #2
- [ ] §9 Security Model resolves Decision Escalation #1 (read/write default mode)
- [ ] §4 Spawner OR §12 Open Questions resolves Decision Escalation #2 (human-in-loop approval workflow scope)
- [ ] §9 Security Model incorporates §5.6 blast-radius classes (Class A–E) as sandbox tiering
- [ ] §6 Tool intake protocol incorporates §5.4 inclusion gates
- [ ] §10 Observability Hooks coordinates with §5.1 gate #5 (CostEvent emission requirement)
- [ ] Deferred-with-rationale appendix (§7) referenced in §12 Open Questions for future-stage pickup

---

## 10. Session Closure

**Status:** Complete. File landed. No halt conditions triggered.
**Next step per Pipeline.md:** 4.1 Winston (Architect) — `/bmad-agent-architect` — Winston reads this file before designing, per Pipeline.md Section 4.5 rule.
**Pre-4.1 Andrey task:** Before Winston begins 4.1, Andrey writes the "Stage 3 deferred findings — Stage 4 must absorb" brief (F-1 CostEvent wiring, F-3 durable jobs table) per Pipeline.md Section 4.7 commitment.

Carson out. 🎭
