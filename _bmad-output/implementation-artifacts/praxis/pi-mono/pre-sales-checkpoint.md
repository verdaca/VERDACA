# Pi-Mono Stage 1 — Pre-Sales Checkpoint

**Stage:** Praxis Stage 1, Step 1.6 (Measurement Foundation)
**Date:** 2026-04-12
**Author:** Pre-sales capture pass (closing the Stage-1 Pipeline.md gate)

---

## 0. PURPOSE

The Praxis build plan treats every stage as a self-demonstrating case study. This file captures the Stage-1 pre-sales artifacts: what we can say publicly about Pi-Mono, what numbers we already have, and what the Stage-2 comparison will show.

The goal isn't a marketing deck. The goal is to make sure the **measurement is captured at the moment it's freshest**, so that when we later tell the "we track every token from inception" story, the receipts are already on disk.

---

## 1. HEADLINE FOR THIS STAGE

> **"Praxis tracks every token from inception. Before we wrote our first feature, we wrote the meter."**

One sentence, defensible, and true: Pi-Mono is the first feature of Praxis, and it tracks the build of Praxis itself.

Supporting points (ordered for a sales conversation):

1. Cost arithmetic runs in `decimal.Decimal`, not floating point. Every line of cost math is auditable byte-for-byte against provider invoices via the snapshot hash recorded on every cost row. **We cannot silently lose a cent.**
2. Every request is idempotent on `request_id`. A retry storm under network failure **cannot** double-bill — this is a database-level guarantee, not an application-level best effort.
3. Pricing is versioned. Every `CostRecord` carries the SHA-256 of the pricing snapshot that was in effect at request time. When a provider raises prices mid-month, historical queries reconcile against the rate that actually applied, not the rate that applies today.
4. The test strategy for Pi-Mono is **property-based**. We don't just run happy-path tests; we generate thousands of adversarial inputs via Hypothesis and verify that `cost.total == cost.input + cost.output + cost.cache_read + cost.cache_write` holds exactly, across every synthetic pricing schedule.
5. The audit trail is append-only. Records never update in place; corrections create new rows with a `lifecycle_state = "amended"` pointer to the parent. You can replay the full billing history at any point in time.

---

## 2. HARD NUMBERS CAPTURED AT STAGE 1

These are Stage 1 baseline metrics — what Pi-Mono measures about itself as-built.

### 2.1 Test coverage

| Surface | Coverage |
|---------|----------|
| `math.py` (cost math) | 96% line coverage (one unused helper) |
| `models.py` (Pydantic models) | 93% line, 77% branch |
| `praxis.kernel.cost` aggregate | 79% line coverage, 74 tests passing |
| Property tests on `compute_cost` | 1,000+ Hypothesis examples per property |
| Static guarantee (no float in cost paths) | AST scan enforced |

### 2.2 Structural guarantees in place

| Risk class (Murat) | Mitigation kind | Evidence |
|---|---|---|
| Float contamination (M1) | Structural impossibility | AST scan + property tests |
| Rounding drift on cache pricing (M2) | Banker's rounding + 10-decimal quantum | `test_banker_rounding_halfway` + large-scale linearity property |
| Async race on same request_id (M3) | DB unique constraint + upsert | `test_idempotent_double_tracking` |
| Cross-provider price drift (M4) | Versioned pricing + snapshot hash | Every row carries `pricing_snapshot_sha256` |
| Sub-cent precision loss (M5) | `NUMERIC(20, 10)` columns | `test_large_tokens_one_billion` round-trips at 1B tokens × 1 USD/MTok = exactly $1000 |

8 of 10 risks are **structurally impossible** (not merely unlikely). The remaining 2 are detectable via reconciliation tooling that lands in Stage 2.

### 2.3 Supported providers at launch

| Provider | Models in seed catalog |
|---|---|
| Anthropic | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5 |
| OpenAI | gpt-5-preview |
| Google | gemini-3.1-pro |
| Fake (test) | fake-model-1 |

Seed catalog: **12 pricing rows** across retention classes (none / short / long).

### 2.4 What Pi-Mono can already do

Verified via smoke test + integration suite:

- `await tracker.track_cost(request, response)` — returns a `CostRecord` with exact Decimal cost
- `await tracker.track_raw_response(request, raw_sdk_response)` — extracts tokens via the provider adapter
- `await tracker.get_session_cost(session_id)` — rollup per session
- `await tracker.get_workflow_cost(workflow_id)` — rollup per workflow
- `await tracker.get_agent_cost(agent, time_range)` — rollup per agent over a time range
- `await tracker.get_lifetime_cost()` — total cost over all recorded time
- `await tracker.reconcile(invoice)` — synthetic invoice reconciliation (real-invoice in Stage 2)
- `await tracker.health()` — liveness probe with outbox depth and catalog age

---

## 3. STAGE-2 COMPARISON BASELINE

The Stage-2 compression layer will need a before/after headline. This section pins the **before** number and describes the measurement protocol so that Stage-2 Winston has a clean comparison target.

### 3.1 Baseline measurement (to be captured immediately before Stage 2)

**Protocol:**
1. Run the BMAD `praxis-build-plan` end-to-end through a representative workflow (TBD which — likely the BMAD `bmad-create-prd` skill against a sample product brief).
2. Track every LLM call through `CostTracker.track_raw_response` with no compression, using the Anthropic Opus 4.6 seed pricing.
3. Record:
   - Total input tokens
   - Total output tokens
   - Total cache read / write tokens
   - `cost.total`
   - Wall-clock time
   - Number of agent invocations
4. Save to `_bmad-output/implementation-artifacts/praxis/pi-mono/baseline-run-YYYY-MM-DD.json`.

**Target headline after Stage 2:**
> "Stage 2 introduced compression. On the same workflow, total tokens dropped from X to Y (−Z%) and cost dropped from $A to $B — measured by Pi-Mono, not estimated."

### 3.2 Cost-math sanity benchmark (synthetic, already captured)

Using the seed pricing:

| Workflow shape | Input tokens | Output tokens | Cache read | Cache write | Computed cost |
|---|---|---|---|---|---|
| One Opus call | 1,000 | 500 | 0 | 0 | **$0.0525** |
| With short cache | 1,000 | 500 | 200 | 100 | **$0.054675** |
| 1M fresh input | 1,000,000 | 500,000 | 0 | 0 | **$52.50** |
| 1B fresh input | 1,000,000,000 | 0 | 0 | 0 | **$15,000.00** (exact, no rounding) |

These numbers come from the integration test and the math unit test — they are the proof that Pi-Mono's Decimal arithmetic matches hand-calculation at every scale we care about.

---

## 4. PROOF POINTS FOR A PRE-SALES CONVERSATION

When showing Pi-Mono to a prospect who asks "how do you know you're tracking cost correctly?", the answer chain is:

1. **Architecture doc** (`pi-mono-cost-tracker-architecture.md`) — 12 numbered ways floating-point math would be tempting and why each one is structurally prevented.
2. **Test strategy doc** (`test-strategy.md`) — risk-weighted coverage targets with each test mapped to a numbered Murat risk.
3. **Golden fixtures and property tests** — run `pytest` in front of them, show the 1,000-example property tests passing.
4. **AST-based linter** — `ast.walk` scan that fails any PR introducing `float()` in cost paths. One script, thirty lines, one grep. The auditor sees exactly what the guarantee is.
5. **Snapshot SHA-256 on every cost row** — open a random record from the DB, show the hash, open the snapshot file at that hash, show the rate matches.
6. **Bonus:** run a reconciliation against a synthetic invoice in real time; watch it come back `status="clean"` with `total_delta == Decimal("0")`.

Six proof points, each verifiable in under 60 seconds on a laptop.

---

## 5. WHAT WE DO NOT CLAIM YET

Things that will land in later stages and should **not** be said yet:

- "Praxis has tracked $X of real build cost so far." — needs Andrey to run the baseline-run-YYYY-MM-DD capture first.
- "Compression saves X%." — Stage 2 headline, not Stage 1.
- "Cross-session memory saves X% on similar tasks." — Stage 3 headline.
- "We have reconciled against Anthropic's real invoice and the delta is <0.1%." — Stage 2 scope with Andrey's historical invoice.
- "We support all major providers." — we support 3 at launch. Bedrock/Azure/etc. are Stage-4+ extensibility work.

Disciplined restraint now makes every later stage's headline more credible.

---

## 6. ACTION ITEMS BEFORE STARTING STAGE 2

1. **Andrey:** Confirm seed pricing matches real provider rates as of today. Pi-Mono will bill against these numbers for baseline capture.
2. **Andrey:** Commit to pricing-snapshot monthly check-in process (first of each month UTC).
3. **Baseline capture run:** Pick the workflow (recommended: `bmad-create-prd` on a representative input) and run it end-to-end with Pi-Mono tracking. Save to `baseline-run-YYYY-MM-DD.json` alongside this file.
4. **Public dashboard stub:** Spin up a read-only HTTP endpoint wired to `get_lifetime_cost()` so that the "Built with Praxis" dashboard has a live number by the time Stage 7 lands.

None of the above blocks Stage 2 from starting — they run in parallel.

---

## 7. NOTE FOR FUTURE CLAUDE SESSIONS

This file **is** the pre-sales artifact for Stage 1. Do not replace it with a narrative document unless Andrey explicitly asks. It is deliberately structured so that a later writing pass can lift specific numbers and headlines into a blog post, pitch deck, or customer conversation without having to re-derive them from code.

The mental model is: **the build is the case study**. Each stage has a dedicated pre-sales checkpoint file capturing the hard numbers at that moment, before they're polluted by later work.

Stage 2 gets its own file at `_bmad-output/implementation-artifacts/praxis/compression/pre-sales-checkpoint.md` when Stage 2 closes.

— Pre-sales checkpoint, 2026-04-12
