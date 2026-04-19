# Rename: Praxis → Verdaca (Stage 7 brand cutover)

**Effective:** Stage 7 kickoff, 2026-04-17
**Decision owner:** Andrey (ratified via BMAD party-mode roundtable — 7 agents, 7 rounds)

---

## Summary

**"Praxis" was the internal codename through Stages 1-6.**
**The product ships as "Verdaca" from Stage 7 onward.**

- All new work and customer-facing surfaces use Verdaca.
- Ratified pre-Stage-7 artifacts stay verbatim as historical record.
- The Python namespace package `src/praxis/` remains the internal module name (like `google3/` — never customer-visible).

---

## Why we renamed

Six Praxis-adjacent domains were already taken (`usepraxis.ai`, `getpraxis.ai`, `praxis.studio`, `praxisengine.com`, `withpraxis.com`, `praxis.run`). A deeper sweep surfaced **three direct-category competitors** operating under the same name:

| Competitor | Positioning | Collision |
|---|---|---|
| **MyPraxis.ai** | "AI Atelier for Founders, Custom Multi-Agent Systems" | CRITICAL — near-identical pitch |
| **praxis-ai.com** (Praxis AI) | EdTech AI-agent middleware, funded (AWS Accelerate '24, GSV Cup '25) | HIGH — owns SEO + TM |
| **praxis-systems.ai** | Enterprise agentic AI | MEDIUM — adjacent buyer |

Plus seven more active Praxis-branded businesses (`praxis.tech` fintech, `praxis.co` venture ecosystem, Praxis Ventures, Praxis Group, PraxisFlow, Praxis Works, Praxis International). Launching "Praxis" = permanent SERP handicap + trademark exposure.

Six coined replacement candidates were stress-tested. Five died on trademark, competitor, or religious-baggage collisions (Kairon, Koros, Veridia, Deliber, Sanhedra). **Verdaca** emerged as the sole survivor:

- `verdaca.com` + `verdaca.ai` AVAILABLE
- Zero SERP footprint, zero LinkedIn companies, zero USPTO filings
- Intuitive CVCVCV spelling; canonical pronunciation **ver-DAH-kuh**
- Semantic echo: *verdict* + *advocate* (empty vessel, not semantic-loaded)

---

## What changes (customer-facing surfaces)

| Surface | Before | After |
|---|---|---|
| Product name | Praxis | **Verdaca** |
| Primary domain | (none registered) | `verdaca.ai` |
| Secondary domain | — | `verdaca.com` |
| Repo display | `praxis` | `verdaca` |
| Stripe products | Praxis Studio Quick/Deep | Verdaca Studio Quick/Deep |
| Canonical pronunciation | — | **ver-DAH-kuh, like *verdict*** |

---

## What does NOT change (internal preservation)

| Surface | Reason |
|---|---|
| Python namespace `src/praxis/` | Load-bearing module path across 250+ files, 1,937 references. Internal only — customer never sees it. |
| Ratified architecture docs (`kernel/*/architecture.md`, `*/test-strategy.md`) | Stage 1-6 provenance. Re-ratification cost > rename benefit. |
| `kernel/mac/tests/static/runtime/test_no_waiver_inventory.py` (16-entry allow-list) | Canonical IDs are MAC-T-prefixed, not praxis-prefixed. Untouched. |
| Stage 1-6 session handoffs + pipeline docs | Historical record. |
| All `pyproject.toml` package identifiers | Internal packaging only. |
| 215 MAC-T test catalog + 27 floor tests | Test IDs don't reference product name. |

---

## Six launch commitments

Derived from the roundtable (Victor, Mary, Sophia, John, Dr. Quinn, Sally, Maya):

1. Register `verdaca.com` + `verdaca.ai` (same day — before this decision leaks)
2. Register defensive typos: `verdica.ai`, `verdaca.co`, `verdaka.ai` (~$40/yr total)
3. Commission paid TM clearance search — USPTO classes 9/42, EU TMview ($500–1,500)
4. Canonical pronunciation baked into every demo open: **"Verdaca, ver-DAH-kuh, like *verdict*"**
5. Pair "Verdaca" with "deliberation engine" in every cold asset for first 6 months (force category association before Verkada phonetic gravity pulls recall)
6. SDR script pre-empts Verkada confusion: "*we're Verdaca, not Verkada — they make cameras, we make deliberation*" as pattern-interrupt line

---

## Outstanding blocker

Before Stage 7 customer-facing copy ships: answer **"who are the first 10 customers, and what 3 words do they say out loud describing what they need when they need you?"** (Maya, Round 1 — unanswered for 7 rounds.)

Stage 7 messaging copy has no ground truth without it.

---

## Forward scope

The rename executes phased, not wholesale:

**Done now (customer-visible surfaces):**
- `README.md`
- `shell/web/app/layout.tsx` (page metadata)
- `docs/sign-up.md` (registration checklist)
- `_bmad-output/planning-artifacts/Praxis/` → `_bmad-output/planning-artifacts/Verdaca/` (directory rename)
- `CLAUDE.md` (project section + directory paths)

**Deferred to Stage 7 execution (do when touched, not as a sweep):**
- Remaining `shell/web/app/**/*.tsx` UI strings
- `shell/api/` response strings
- `shell/messaging-and-onboarding.md`, `shell/pricing-strategy.md`, `shell/pre-sales-report.md`
- `docs/build-plan.md`, `docs/pipeline.md`, `docs/pipeline-stages.md`, `docs/methodology.md`, `docs/operations.md`, `docs/session-log.md` — add codename note as each is edited

**Never (intentional codename preservation):**
- `src/praxis/**` Python namespace
- All `kernel/*/architecture.md`, `kernel/*/test-strategy.md`, `kernel/*/code-review.md`, `kernel/*/alignment-review.md`
- All test files and test IDs
- Pre-Stage-7 session handoffs
