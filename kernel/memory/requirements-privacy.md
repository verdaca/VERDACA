# Stage 3 — Memory & Learning Layer: Privacy Requirements (Round 1 Draft)

**Status:** Draft v0.2 — Round 1 elicitation output (BEFORE Winston)
**Pipeline step:** 3.0.1 — `/bmad-advanced-elicitation`
**Method applied:** Stakeholder Round Table (collaboration #1) — per Pipeline.md Section 4.5 Quick Reference
**Pattern:** perspectives → synthesis → alignment
**Next step:** 3.0.2 — `/bmad-cis-problem-solving` (Dr. Quinn) red-teams this doc
**Binding on:** Winston's Stage 3 architecture draft (`memory/architecture.md`)
**Supersedes:** v0.1 (first-principles + pre-mortem draft). Substantive recommendations preserved; re-derived through multi-persona debate.

---

## How to Read This Document

Each of the four focus questions convenes six stakeholders around a virtual table. Each persona speaks once per question from their own frame. After all six speak, a synthesis section extracts the load-bearing agreements and records the unresolved tensions for Round 2 (Dr. Quinn) or Andrey to break.

The six personas are:

| # | Persona | Frame | Primary concern |
|---|---------|-------|-----------------|
| 1 | **Priya — Enterprise CISO** | Security / compliance | Non-bypassable isolation, audit trails, DPA-ready posture |
| 2 | **Marco — SMB Founder / Solo Consultant** | Speed / friction | Zero-config onboarding, low cost, instant value |
| 3 | **Lena — GDPR/DPO Legal Counsel** | Regulatory | Right-to-erasure cascades, embedding derivatives, residency |
| 4 | **Ravi — Revenue / GTM Lead** | Sales | First-session value, deal-blocker risks, pricing compatibility |
| 5 | **Sam — Praxis Platform Engineer** | Implementation | Enforcement-by-construction, operational cost, failure modes |
| 6 | **Dr. Ito — Memory-Systems Researcher** | Technical risk | Poisoning, retrieval quality, decay, library half-life |

Each persona is stable across all four questions so their viewpoints compose into a coherent character. The synthesis at the end of each question is *my* aggregation, not one of theirs.

Everything below is a *recommendation to Winston* — Winston can raise objections back per Pipeline.md Section 4.5 rule 3, but cannot silently override.

---

## Question 1 — SMB vs Enterprise Tenancy Posture

**The question:** Is Praxis v1 single-tenant-per-deployment (SMB-style isolation), multi-tenant-shared with row-level scoping (Enterprise SaaS), or both modes pluggable behind the unified Memory interface?

### Round Table

**Priya (Enterprise CISO):** "I've spent ten years rejecting vendors whose data isolation story was 'trust us, the WHERE clause is always correct.' A missing scope filter in one query is all it takes to ship a cross-tenant leak, and the retrieval path in a memory system runs on *every* task — there's no low-traffic corner where a bug hides harmlessly. If Praxis wants to close enterprise deals later, it needs structural isolation now. My preference: one Postgres per customer, deployed into our VPC, keys we own, audit log we can subpoena. Anything shared is a multi-year procurement fight I won't have for a startup."

**Marco (SMB Founder):** "I don't care about any of that. I'm one person who wants to ask Praxis a strategic question at 11pm and get an answer. If signup takes more than 3 minutes or I have to 'provision an instance', I'm gone. I'd happily live on shared infrastructure because I trust you more than I trust myself to configure a database. The moment single-tenant means 'wait 48 hours for your sandbox' I've already bought something else."

**Lena (DPO Counsel):** "From a pure compliance standpoint, tenancy is a means, not an end. What I care about is: when a data subject exercises their right to erasure, can you prove you deleted everything *within a reasonable time window*, and is your default residency defensible under Schrems II? Single-tenant makes that provably easy — the deletion scope is the instance. Shared tenancy makes it possible but harder to evidence. I'll sign off on either if the audit trail is clean, but the single-tenant paperwork is shorter."

**Ravi (GTM Lead):** "The question I care about is 'what's the first question a prospect asks that kills the deal?' For enterprise prospects, that question is 'where does my data live and who else can see it' — single-tenant answers it in one sentence. For SMB prospects, the question is 'how fast can I try it' — and a 'managed single-tenant' model (we host one instance per customer) answers both if onboarding is automated. The trap is shared multi-tenant SaaS where the enterprise ask requires rebuilding the isolation model. Don't build that twice."

**Sam (Platform Engineer):** "The unified Memory API needs a `tenant_id` parameter regardless of which mode we pick, because that's how we'll audit every call site. What I'd push back on is *building* the shared-tenant backend in v1. We'll write scoping bugs. Every memory system I've seen with row-level tenancy has leaked at least once in its first year. Ship single-tenant-per-deployment as the only backend, pin tenant_id at deploy time, hard-fail startup if more than one tenant_id shows up in the database. The API surface leaves the door open for a shared backend later, but v1 doesn't walk through it."

**Dr. Ito (Researcher):** "There's a subtlety nobody's mentioned: the experience library's compounding advantage is *stronger* in a deeply-scoped environment than in a shared one, because task similarity is highest when all tasks come from the same customer's narrow domain. Shared multi-tenant dilutes the retrieval pool with tasks that look similar but aren't. Single-tenant-per-deployment is *technically better* for the compound advantage claim, not just safer. Don't apologize for it — lean into it."

### Synthesis

Five of six personas converge on **single-tenant-per-deployment as the v1 backend**, for different reasons:
- Priya: structural isolation removes scoping bugs by construction
- Lena: deletion cascade and residency become trivially provable
- Ravi: answers enterprise and SMB objections if onboarding is automated ("managed single-tenant")
- Sam: eliminates the class of bug he's seen most often
- Dr. Ito: retrieval quality is actually higher when the pool is tightly scoped

Marco's objection (friction) is real but is an *onboarding* problem, not a tenancy problem — it's solved by automated instance provisioning, not by shared infrastructure. The team inherits the onboarding problem as a Stage 7 POV Harness task.

### Recommended Default

**Ship single-tenant-per-deployment as the only supported mode in v1. Design the unified Memory API to accept `tenant_id` as a required parameter from day one so Phase 2 shared-multi-tenant is a backend swap rather than a retrofit.**

### Load-Bearing Assumptions for Winston

- Unified Memory API takes `tenant_id` as a **required** parameter on every store/retrieve/delete call. v1 backends MUST reject any call where `tenant_id` does not match the deployment's pinned tenant identity.
- Beads worktrees, Mem0 collections, and Atelier decision records inherit `tenant_id` from the Memory facade's deployment config — **never** from the caller. Callers cannot pass tenant_id through as a query-builder parameter.
- Deployment manifest pins tenant_id at install time. Drift at runtime is a configuration error that hard-fails the process, not a runtime warning.
- No Memory API surface exposes a raw query builder. All retrieval paths are named, typed methods on the facade (e.g., `retrieve_similar_tasks`, `retrieve_decisions`) — never `execute_sql(query)` or `mem0.search(filter_dict)` passthroughs.
- Cross-tenant retrieval is a **non-existent code path** in v1 — not a feature flag, not a gated API, literally no code that could do it.

### Tensions to Escalate

- **Marco's friction objection.** Single-tenant-per-deployment is the right answer *only if* Stage 7 delivers automated provisioning. If Stage 7 can't deliver one-click provisioning, Marco's segment churns at signup. Flag for Stage 7 prompt.
- **Priya's "keys we own" demand.** Single-tenant-per-deployment in *our* infrastructure isn't the same as single-tenant in *their* VPC with BYO keys. Enterprise buyers eventually demand the latter. Phase 2 is not just "shared SaaS" — it's also "customer-VPC deployment with customer-managed KMS." Log for later.

### Follow-Ups for Andrey

1. **Deployment posture for target early customer.** On-prem/VPC? Managed single-tenant (we host)? Shared SaaS? Pick one — it determines whether Phase 2 is ever needed and what Phase 2 looks like.
2. **Pricing compatibility.** Is single-tenant-per-deployment compatible with the Stage 7 pricing model you have in mind (per-seat, per-deployment, credit-pack)? Flag mismatches now.

---

## Question 2 — Cross-Customer Learning Opt-In

**The question:** Does the experience library EVER retrieve across tenant boundaries (e.g., anonymized pattern reuse), or is the compounding advantage strictly per-tenant? If strictly per-tenant, what do we tell Stage 6 customers whose first session has zero retrieval benefit?

### Round Table

**Priya (CISO):** "Never. Full stop. 'Anonymized cross-tenant learning' is one regex-failure away from leaking my deal names into a competitor's retrieval results. I don't care how the anonymization is described in the marketing copy — if there's a code path that reads another tenant's embeddings into my query, I will fail you in security review. Close the door entirely. I want to see a code review where the reviewer can prove no cross-tenant read is even *reachable*, not just 'disabled by config'."

**Marco (SMB Founder):** "Honestly? I'd love cross-tenant learning because my first session has nothing to retrieve against and I'd learn faster from what other solo consultants figured out. But I also know that if *my* strategy for a deal I'm working on shows up in somebody else's retrieval, I lose my competitive edge. So I want the benefit without the cost, which is impossible, so I'll take neither. If Praxis ships with some curated examples I can learn from on day one, that solves 80% of my problem."

**Lena (DPO Counsel):** "Cross-tenant retrieval in the literal sense is untenable for me — embeddings encode personal data, regulators have made this view consistent, and shared embeddings across tenant boundaries are a data-sharing event that needs a legal basis we don't have. However: a *frozen shared seed corpus* of content Praxis owns or licenses is legally a different thing. It's content Praxis provides to all customers equally, not customer content redistributed. I can write the DPA language for that easily."

**Ravi (GTM Lead):** "The empty-first-session problem is real for sales demos. A prospect sees an 'Experience Library: 0 results' screen and the compounding-advantage pitch collapses before we can explain it. The fix is to ship the seed corpus *and* be transparent about what's in it: 'Praxis comes with 500 curated strategy case studies; after 3–5 sessions, your own work dominates retrieval.' That's an honest line that also defuses the 'are you training on my data' question — no, here's exactly what we trained on."

**Sam (Platform Engineer):** "From my chair, a seed corpus is just a read-only Mem0 collection with a different `scope` enum value. Zero new infrastructure. The hard part is making sure no code path *writes* to it from a tenant context — that's a typed-method enforcement on the facade. Easy to build, easy to audit."

**Dr. Ito (Researcher):** "I'd add one nuance: the seed corpus should have a versioning discipline. If a retrieval today surfaces result X, and the same query tomorrow surfaces a different result because the seed was updated, your reproducibility story breaks. Pin `seed_version` in every retrieval audit entry. Also: the seed corpus *will* go stale — build in a curation cadence (quarterly?) and budget for it. It's not fire-and-forget."

### Synthesis

Unanimous agreement on the substantive answer: **per-tenant experience library, plus a frozen shared seed corpus**. The seed corpus is Praxis-owned content (public case studies, licensed strategy frameworks, public-domain PRFAQs) that every tenant can read but no tenant can write to. Cross-tenant retrieval in the literal sense is not a feature, not a config flag, and not a reachable code path.

Three implementation constraints surface from the discussion:
- **No-reachable-write enforcement** (Priya + Sam): closing the door must be structurally auditable, not just disabled
- **Legal framing** (Lena): the seed corpus is Praxis content provided equally to customers, not customer data redistributed — this is the language for the DPA
- **Versioning + curation cadence** (Dr. Ito): seed corpus has a `seed_version` hash recorded with every retrieval, and needs a quarterly refresh budget

Marco's opt-in-to-cross-tenant wish is explicitly rejected because the cost (Priya's leak risk + Lena's legal surface) dominates the benefit.

### Recommended Default

**Ship a per-tenant experience library plus a frozen, versioned, shared seed corpus. No cross-tenant retrieval code path exists.** First-session story: "Praxis ships with a curated seed library so your first session already has relevant context to reason against. After 3–5 sessions your own experience library dominates retrieval and the seed recedes into the background."

### Load-Bearing Assumptions for Winston

- Memory facade has a `scope` enum: `{TENANT, SEED_CORPUS}`. Writes always go to TENANT. Reads query both by default, with SEED_CORPUS results down-weighted after N tenant-local records exist (strawman N=25, to be calibrated in Stage 5).
- Seed corpus lives in its own Mem0 collection, distinct from tenant collections. It is read-only at the tenant layer — no Memory API method can mutate it from a tenant context. This is enforced by typed methods, not runtime config.
- Seed corpus is versioned in Beads. A `seed_version` hash is pinned per deployment and recorded in every retrieval audit log entry so results are reproducible and attributable.
- Seed corpus ingest pipeline is a **separate, offline tool** run by the Praxis operator — not an API exposed at runtime.
- No code path, anywhere, allows a tenant to write to SEED_CORPUS scope or read from another tenant's scope.
- Seed corpus refresh cadence is a named operational process owned by a specific role (strawman: quarterly; owner TBD with Andrey).

### Tensions to Escalate

- **Curation ownership.** Dr. Ito flagged that the seed corpus needs a named owner and refresh cadence. Who is that person? Is it a Stage 6 Studio task (content-heavy) or a Praxis-ops role?
- **First-N-sessions weighting.** The N=25 crossover is a strawman. Too low and the seed influences tenant results longer than useful; too high and tenants see stale seed content even after they've built their own library. Worth revisiting when real retrieval metrics exist.

### Follow-Ups for Andrey

1. **Does the seed corpus exist?** If yes, point Winston at its current location. If no, Winston specifies the ingest protocol + schema but content curation is a Stage 6 task, not Stage 3.
2. **Licensing clearance.** Who has sign-off authority on what enters the seed corpus? Some "public" strategy content is public-to-read but not public-to-redistribute-as-training-data.
3. **Segment check.** Is there any customer segment where cross-tenant learning would be a *required* feature (regulated industries, specific enterprise verticals)? If yes, the "close the door entirely" stance gets revisited. If no, Option C is clearly right.

---

## Question 3 — GDPR Posture (Right-to-Erasure + Data Residency)

**The question:** When a customer issues a deletion request, what is the cascade across Beads snapshots, Mem0 embeddings, Atelier decision records, and the experience library? Are embeddings considered derivative works (retained) or personal data (deleted)? What is the default residency story?

### Round Table

**Priya (CISO):** "Deletion has to be auditable end-to-end. I need to see: request came in at T, system returned 'deleted' at T+N, here's the list of stores touched, here's the record count per store, here's the hash of the pre-delete state, here's the hash of the post-delete state. Anything less and I can't tell my own board we're compliant. Residency-wise, I want to deploy Praxis into my region of choice, and 'the data lives wherever the Postgres instance lives' is a clean answer — better than a pluggable region config that nobody actually tests."

**Marco (SMB Founder):** "I don't ever want to think about GDPR. If I click 'delete my account,' everything associated with me should be gone within minutes and I should get a confirmation email. I won't read the DPA. I just need the button to work."

**Lena (DPO Counsel):** "Three things I need, listed in order of importance. **One**: deletion must cascade to embeddings. The 'embeddings are derivative works, not personal data' position is an engineering convenience, and every EU DPA has rejected it when tested. Treat them as personal data, delete on cascade. **Two**: I need an audit log that records the deletion, the criteria, the cascade, and the actor — retained for 2 years (strawman; some jurisdictions want longer). **Three**: the right to access (Article 15 — the customer asks 'what do you have on me') must be implementable with the same API. Retrofitting access queries is as painful as retrofitting deletion. Don't punt it."

**Ravi (GTM Lead):** "My concern is the DPA-template gap. First enterprise procurement will ask for a signed DPA. If we don't have one, the deal slips 3-6 weeks while legal drafts one. Either we ship the template in v1 (expensive, and probably wrong because we don't have real customer scenarios yet), or we accept 'DPA on demand, 1-2 week turnaround' and price that risk in. I can live with the latter if engineering confirms the *architecture* is compliant."

**Sam (Platform Engineer):** "Deletion cascade is a code path that must exist by design. Retrofitting it means walking every store to find orphans, and I've been the person doing that retrofit before. Don't make me do it again. It's also trivially cheap to build in day one: a single `delete(scope, criteria)` method on the Memory facade that dispatches to each backing store in a defined order. Embedding purge is synchronous within the delete call — no 'we'll regenerate embeddings later' path that leaves embeddings alive in the gap."

**Dr. Ito (Researcher):** "The academic consensus on embeddings-as-personal-data has shifted decisively in the last two years. A 2024 paper out of ETH Zurich showed embedding inversion can recover ~80% of original content tokens for sentence-length inputs. That's enough for regulators to say 'yes, this is personal data.' Any position that says otherwise is betting on a permissive regulator in every jurisdiction, which isn't a bet worth taking. Also — on the access side — the Article 15 query is much harder than the delete query, because 'what do you have on me' requires reconstructing the content, not just deleting rows. Budget for it."

### Synthesis

Unanimous: **deletion cascade is architectural day-one work**; **embeddings are personal data for purposes of delete**; **residency handled by deployment location** (trivial consequence of Q1's single-tenant-per-deployment answer).

Lena adds the Article 15 access-query requirement, which hadn't been in the original question framing but is a known GDPR gap that's expensive to retrofit. Bringing it into scope now costs little and avoids a painful retrofit later.

Ravi surfaces the DPA template gap as a sales risk rather than an architectural one — recoverable in weeks, not months. Recommended posture: GDPR-ready architecture, deferred certification, budget 1–2 weeks to produce the DPA when first enterprise prospect asks.

Dr. Ito's embedding-inversion citation strengthens the "embeddings are personal data" stance from "cautious" to "evidence-backed."

### Recommended Default

**GDPR-ready architecture, deferred certification.** Deletion cascade exists from day one. Embeddings are purged as personal data. Article 15 access queries are a first-class API method even if v1 exposes them only via CLI. Residency = deployment location (automatic consequence of single-tenant-per-deployment). No DPA template, no SOC2 attestation in v1; produce on-demand when first enterprise prospect requests.

### Load-Bearing Assumptions for Winston

- Unified Memory API has a `delete(scope, criteria)` method that cascades across Beads snapshots → Mem0 vectors → Atelier decision records → experience library tuples that reference the deleted items. Cascade order is deterministic and audit-logged.
- Deletion is **audit-logged**: initiator, timestamp, criteria, matched IDs, touched stores, pre/post hashes. Audit log has its own retention policy (strawman: 2 years; configurable).
- User-facing `delete()` is synchronous for the primary cascade (Beads + Mem0 + Atelier). Experience library rewrites (which may touch many records) can be async with a confirmation callback.
- **Embedding purge is synchronous within the delete call** — no "regenerate embeddings later" path that leaves embeddings alive in the gap between delete and rebuild.
- Default residency = "wherever this deployment is installed." No cross-region replication, no automatic backups to other regions. Backup policy is an operator decision at deployment time.
- **Right-to-access** (`export(scope, criteria)` or similar) is a first-class Memory API method from day one, even if only CLI-exposed in v1. Retrofitting access queries is as expensive as retrofitting delete.
- DPA template and SOC2 attestation are NOT deliverables for Stage 3 — they are documents produced on-demand by Andrey + legal when the first enterprise prospect requires them.

### Tensions to Escalate

- **Audit log retention.** Strawman 2 years; some jurisdictions (financial services, healthcare in parts of EU) may want 5+. Configurable default is the right answer, but defaults matter.
- **Access-query output format.** "Here's everything we have on you" — what format? JSON dump? Markdown report? This is a Stage 6 Studio concern more than a Stage 3 concern, but the API surface has to exist now.

### Follow-Ups for Andrey

1. **Accept the DPA gap?** V1 ships without DPA template or SOC2. First enterprise customer will ask. OK to defer, or block Stage 7 on legal-driven doc production?
2. **Audit log retention default.** 2 years? 5 years? Configurable is easy; picking the default for the shipped config is a business call.
3. **Embedding-as-personal-data stance.** Above I've recommended treating embeddings as personal data. This costs retrieval quality on partial deletions but avoids a legal trap. Confirm you want the safer stance.
4. **Article 15 access-query exposure in v1.** CLI-only is cheapest. Do we need a programmatic API for Stage 6 Studio to call later?

---

## Question 4 — Experience Library Poisoning Governance

**The question:** A bad outcome written to memory causes future similar tasks to inherit the bad approach. What quality gate governs write-back (MAC score? human ratification? auto-rollback)? Who has authority to flag/remove a poisoned entry after the fact?

### Round Table

**Priya (CISO):** "Less my domain, but I'll note: the ability to *quarantine* an entry is also a deletion-adjacent capability, and it needs to be audited the same way. If I can't prove who quarantined what when, I can't defend the system in an incident response."

**Marco (SMB Founder):** "I don't want a human reviewer between me and the library. I'll stop using it within a week if there's any rubber-stamping step. Just *work*. If a bad entry slips in, show me a 'this felt wrong, flag it' button and I'll clean it up when it annoys me."

**Lena (DPO Counsel):** "Quarantine has to be reversible (it's a state change) and distinct from deletion (which is a data subject right). Don't conflate them. An entry can be quarantined *and* later deleted, or quarantined *and* later restored, or deleted without ever being quarantined. Three different operations, three different audit trails."

**Ravi (GTM Lead):** "The compounding-advantage pitch relies on the library getting *better* over time. If the library has a visible quality-drift problem — customers noticing retrievals get less useful — that's a pitch-killer. I want to know at Stage 7 demo time that our memory is measurably trending better, not randomly oscillating. Some kind of telemetry on retrieval quality is as important as the quarantine mechanism itself."

**Sam (Platform Engineer):** "Three separable concerns here: (1) what lets an entry in, (2) how much an entry influences retrieval, (3) what happens when a bad entry is found post-hoc. Most memory systems I've seen conflate all three, and the bugs live in the conflation. Design them independently: an admission gate tied to MAC quality_score, a retrieval weighting formula that honors a state field (tentative / confirmed / quarantined), and an admin API to flip state. Three APIs, not one magic function."

**Dr. Ito (Researcher):** "Sam's decomposition is exactly right, and I'd add the SiriuS-paper nuance: the experience library's value is strongest when the *promotion* from tentative to confirmed is driven by *downstream reuse success*, not by an independent quality gate. The MAC quality_score gets you in the door, but reuse is what proves the approach generalizes. So tentative → confirmed transitions on 'retrieved AND reused in a downstream task whose own quality_score was high.' And no auto-rollback on downstream failure — one failed reuse is too noisy a signal. That's human-in-loop territory."

### Synthesis

The round-table converges on Sam's three-layer decomposition, with Dr. Ito's SiriuS-derived promotion rule layered on top:

1. **Write-side gate (MAC-driven):**
   - `quality_score >= 0.8` → admit as CONFIRMED
   - `0.5 <= quality_score < 0.8` → admit as TENTATIVE (half-weight)
   - `quality_score < 0.5` → reject, log
2. **Read-side weighting formula:**
   ```
   retrieval_score = semantic_similarity
                   × recency_decay(age)
                   × state_weight(state)   # CONFIRMED=1.0, TENTATIVE=0.5, QUARANTINED=0.0
                   × quality_score ^ alpha # alpha ≈ 0.5, tune empirically
   ```
3. **Promotion rule (SiriuS):** tentative → confirmed when the entry is retrieved AND reused in a downstream task whose own `quality_score ≥ 0.8`.
4. **Quarantine API:** `flag_and_quarantine(entry_id, reason)` — reversible state change, NOT deletion (Lena's distinction). Audit-logged (Priya's constraint).
5. **Retrieval-quality telemetry:** expose a dashboard metric so operators can watch library health over time (Ravi's concern).

Dependency on Stage 5: if MAC quality_score ships late, Memory v1 ships with **all entries admitted as TENTATIVE** (safest default). No entries rejected in MAC-absent mode — collect everything, let Stage 5 re-score retroactively when it lands.

### Recommended Default

**MAC-gated admission into a tentative→confirmed state machine, with admin quarantine as an escape hatch and telemetry on library health.** Quarantine and deletion are distinct operations, each with its own audit trail. No automatic rollback based on downstream failure.

### Load-Bearing Assumptions for Winston

- Every experience library entry has a `state` field: `{tentative, confirmed, quarantined}`. Retrieval joins `state_weight` into the score formula. State is a first-class column, not a flag derived from metadata.
- Quality threshold values (0.8 / 0.5) are **placeholders pending Stage 5 calibration**. Winston designs the mechanism; thresholds become configuration. Hard-coding them is a bug.
- Promotion from tentative to confirmed is deterministic and triggered by a successful downstream reuse event. The MAC publishes a "reuse-successful" signal that Memory subscribes to.
- `flag_and_quarantine()` is reversible (state transition, NOT deletion). Audit trail records every state change with actor, timestamp, reason.
- **Quarantine and GDPR deletion are distinct operations.** Quarantine keeps the record for audit (Lena). Deletion removes it entirely (Q3 cascade). Both emit audit events.
- Retrieval-quality telemetry is a **named deliverable**, not a wishlist item. Emit metrics for: admission rate, rejection rate, tentative-to-confirmed conversion rate, retrieval score distribution over time, p99 retrieval latency. Wire into Pi-Mono's observability plane.
- MAC is a **hard dependency** of full-functionality Memory. If MAC is not deployed yet, Memory runs in a degraded "all tentative" mode with explicit logging of the degradation.
- Retrieval weighting formula is stated explicitly in architecture.md — not buried in code comments. Formula is tunable per deployment via config but has sane defaults.

### Tensions to Escalate

- **Async promotion lifecycle.** If a tentative entry is retrieved today and the downstream outcome isn't known for 7 days (long strategic workflow), the transition waits 7 days. Is that acceptable, or does the UX need an interim signal?
- **Telemetry exposure.** Retrieval-quality metrics are engineering-internal, but Ravi wants them for sales demos. Who owns the dashboard — operator-facing, customer-facing, or both?

### Follow-Ups for Andrey

1. **Threshold calibration.** The 0.8/0.5 numbers are strawmen. Dedicated brainstorming round in Stage 5 for real thresholds, or Winston uses 0.8/0.5 as starting point and Stage 5 re-tunes?
2. **Admin surface.** Who is the "tenant admin" who calls `flag_and_quarantine` in v1? Single-tenant-per-deployment (Q1) means the customer's own admin user. CLI/API in v1, or is there a UI requirement? (UI feels like Stage 6.)
3. **Reuse-success signal latency.** Confirm 7-day async lifecycle is acceptable for tentative→confirmed transitions.
4. **Library-health dashboard ownership.** Operator-facing only, or also customer-facing for the "our memory is getting smarter" pitch?

---

## Cross-Question Synthesis (What All Four Recommendations Assume Together)

The four recommended defaults compose into a coherent v1 posture:

1. **v1 = single-tenant-per-deployment** (Q1) → tenant boundary is structural, not query-layer.
2. **Per-tenant experience library + shared read-only seed corpus** (Q2) → first-session value without cross-tenant legal exposure.
3. **GDPR-ready architecture, DPA on-demand** (Q3) → deletion cascade exists from day one; residency = deployment location because of (1); embeddings are personal data; Article 15 access is a first-class API.
4. **MAC-gated admission + tentative→confirmed state machine + admin quarantine + health telemetry** (Q4) → poisoning bounded by construction.

**Consistency check:** If Round 2 (Dr. Quinn) or Andrey overrides any of (1)–(4), the others need re-checking. Specifically:
- Flipping Q1 to shared multi-tenant invalidates the trivial-residency assumption in Q3 and makes Q4's write-side scoping load-bearing in a way it isn't under single-tenant.
- Loosening Q2 to allow cross-tenant reads invalidates Priya's "no reachable cross-tenant code path" assurance.
- Softening Q3's embeddings-are-personal-data stance invalidates Dr. Ito's embedding-inversion citation.
- Removing Q4's tentative state flattens the promotion story and makes MAC-absent mode unsafe.

### Memory's Persona Scorecard

Informally, the round-table revealed which stakeholders are *primary* for each question:

| Question | Primary voice | Secondary voice | Why |
|----------|---------------|-----------------|-----|
| Q1 tenancy | Priya + Sam | Dr. Ito | Security + implementation drive the answer; researcher confirms it's also better for retrieval |
| Q2 cross-tenant | Lena + Priya | Marco + Ravi | Legal and security set the hard floor; business/sales define the fallback (seed corpus) |
| Q3 GDPR | Lena | Sam + Dr. Ito | DPO drives; engineer and researcher shape the execution |
| Q4 poisoning | Sam + Dr. Ito | Ravi + Lena | Engineer and researcher drive the mechanism; business wants telemetry; legal enforces quarantine/delete distinction |

Marco (SMB friction) is never the primary voice but is the *veto vote* on anything that adds human-in-loop friction to Marco's experience. This is useful for Stage 7 onboarding design.

---

## What Winston Should Read Before Drafting `architecture.md`

1. **This document** — the four recommendations + load-bearing assumptions + tensions.
2. **Round 2 output** at `memory/requirements.md` (once `/bmad-cis-problem-solving` runs in step 3.0.2). Round 2 may harden, override, or add risk items.
3. **Stage 1** (`pi-mono/architecture.md`) for the CostEvent contract — deletion cascades must emit CostEvents of type `retention_action` so operators can see the cost of compliance operations; library-health telemetry must wire into Pi-Mono's observability plane.
4. **Stage 2** (`compression/architecture.md`) §3.3 for the RTK polyglot boundary — Forge compaction of Beads state must respect the same subprocess-wrapper contract.
5. **Stage 2 alignment review** §6 for integration contracts — `tenant_id` propagation through the compression layer is new work that needs a contract.

---

## Questions Still Outstanding (Cannot Resolve in Round 1)

Collected from each question's "Follow-Ups for Andrey":

| # | Question | Blocks |
|---|----------|--------|
| Q1-a | Target early customer posture: on-prem, managed single-tenant, or shared SaaS? | Phase 2 roadmap |
| Q1-b | Single-tenant-per-deployment compatible with Stage 7 pricing? | Stage 7 prompt |
| Q2-a | Does the seed corpus exist? Who curates it? | Winston's seed corpus section |
| Q2-b | Seed corpus licensing sign-off authority | Operator-facing ops |
| Q2-c | Any segment where cross-tenant is a required feature? | Rules out Option B conclusively |
| Q3-a | Accept DPA gap for Stage 7? | Stage 7 sales posture |
| Q3-b | Audit log retention default (strawman 2 years) | Deployment defaults |
| Q3-c | Confirm embedding-as-personal-data stance | Mem0 delete cascade design |
| Q3-d | Article 15 CLI-only in v1, or programmatic API for Stage 6? | API surface scope |
| Q4-a | Threshold brainstorm timing (Stage 5 calibration round?) | Stage 5 prompt |
| Q4-b | Admin UI vs CLI for quarantine in v1 | Stage 6 Studio prompt |
| Q4-c | Reuse-success signal async lifecycle OK (7-day transitions)? | MAC → Memory contract |
| Q4-d | Library-health dashboard: operator-only or customer-facing? | Stage 6 + Stage 7 |

None of these block Winston from drafting `architecture.md`. All of them need an answer before Stage 3 completes.

---

**End of Round 1 draft.** Proceed to step 3.0.2 (`/bmad-cis-problem-solving`, Dr. Quinn) which will red-team this document against retention/governance risks via Failure Mode Analysis + Risk Matrix (per Pipeline.md Section 4.5 Quick Reference) and produce the consolidated `memory/requirements.md`.
