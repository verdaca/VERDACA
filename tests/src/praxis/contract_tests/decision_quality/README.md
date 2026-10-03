# Decision-Quality (T7) Test Tier

The **Governance & Decision-Quality (T7)** contract-test tier operationalizes
the reusable assessment approaches from the Verdaca literature review
(`_bmad-output/planning-artifacts/Verdaca/verdaca-literature-review.md`,
§"Assessment Approaches to Carry Forward for Murat") into concrete Verdaca
tests.

**This directory holds the HERMETIC subset** (4 of the 12 T7 fixtures): no
creds, no live LLM/memory backends. They drive the real
`VerdacaGatewayService.execute` / `MemoryPort` / `SqliteSessionIndex` through
the Stage 11 contract fakes (`..ports.gateway_contract_fakes`) and assert on
the real DTOs, ledger, and SessionIndex.

## Discipline

- **NO `@pytest.mark.no_waiver`** on any test here. The ratified pin is
  **14/9/23**; T7 is decision-quality coverage, not a new ratified invariant.
  Adding a no_waiver marker is a ratification action and would break the count
  gates (`test_stage1{2,3,4}_no_waiver_count.py`). Plain tests only.
- Hermetic — passes with no creds in CI.

## Fixtures in this directory

| Fixture | File | Literature source | PASS / FAIL criteria |
|---|---|---|---|
| **T7.6 Deliberation surface** | `test_t7_6_deliberation_surface.py` | Ma et al. (2025) human-AI deliberation; Lee et al. (2025) critical-thinking survey | **PASS:** `AnalysisResult` exposes all four affordances — alternatives (`cited_tradeoffs`), uncertainty/disagreement channel (`dissent_frames`), inspectable evidence (`artifacts` with resolvable refs), and a contestable `recommendation`. **CONDITIONAL:** 3/4 present (documented degradation). **FAIL:** ≤2/4. |
| **T7.9 Cost governance** | `test_t7_9_cost_governance.py` | Chen, Zaharia & Zou (2023) FrugalGPT | **PASS:** an over-budget virtual key REJECTS via `BudgetExhaustedError` on the auth-first spine *before* any LLM cost is burned (no `llm.calls`, no `cost.records`), AND a within-budget run records exactly one scoped cost ledger event and emits a non-null `cost_usd` summary. **FAIL:** over-budget run burns cost, or within-budget run records no cost / emits no summary. |
| **T7.10 Memory hygiene** | `test_t7_10_memory_hygiene.py` | Zhong et al. (2024) MemoryBank | **PASS:** store/query/promote/revoke round-trips across the full `MemoryPort` Protocol surface; stored entries carry provenance (correlation id + source span); entries under distinct workspace/channel pairs stay distinguishable by provenance (no cross-channel leak); the gateway writes session+workspace-scoped provenance. **FAIL:** any Protocol hop drops its DTO, provenance missing, or workspace boundaries merge. |
| **T7.11 Audit reconstructability** | `test_t7_11_audit_reconstructability.py` | Mokander et al. (2023) three-layered LLM audit | **PASS:** after one run, all eight audit dimensions + final result are reconstructable from `SessionIndex` + recorded seams — session ID, caller, channel, auth path (OIDC authenticate + nonce check fired), evidence artifacts, model calls, cost, gate outcome (`status == "completed"`), and the final recommendation. **FAIL:** any dimension is not queryable. |

## The other 8 T7 fixtures (NOT in this pass)

The remaining fixtures need the live LLM path up (LiteLLM + DIAL creds) and are
**live-only** / partly-hermetic. They are out of scope for this hermetic pass.
Each must `pytest.skip` when creds are absent (mirror the `DIAL_API_KEY` idiom
in `..ports/test_stage14_live_smoke.py` and the
`require_production_profile` fixture in `..ports/conftest.py`).

| Fixture | Literature source | Why not hermetic |
|---|---|---|
| T7.1 Abstention (5 classes) | AbstentionBench (Kirichenko 2025); Wen 2025; Kamath 2020; Yin 2023 | Scores model behavior on answerable/ambiguous/no-evidence/contradicted/policy-escalate — needs a real model to elicit (non-)abstention. |
| T7.2 Evidence faithfulness | Context-faithful prompting (Zhou 2023) | Inject evidence conflicting with the model prior; requires a live model to test cite-or-explain-rejection. |
| T7.3 RAG robustness (4 fixtures) | RGB (Chen 2024); Gao 2023 survey | Distractor / no-answer / multi-doc / conflicting — scores citation precision against live generation. |
| T7.4 Hallucination | CoVe (Dhuliawala 2024); CRITIC (Gou 2023) | Unsupported-claim rate needs live model output to verify. |
| T7.5 Critique independence | Valmeekam VAL (2023); MAD (Tian 2024) | Partly hermetic — deterministic oracle possible, but separate generator/critic/judge roles need live calls to measure surfaced disagreement. |
| T7.7 Flawed-directive resistance | Sycophancy / ambiguity (Ozturk Birim 2026) | Flawed + vague prompts; expects clarifying questions — live model required. |
| T7.8 Compression integrity | LLMLingua (Jiang 2023); Li 2023 | Same fixture uncompressed/compressed/budget-constrained — partly hermetic; evidence-retention scoring wants live generation. |
| T7.12 Brevity governance | Brevity-constraint (Hakim 2026) | Concise/normal/verbose policies scored on accuracy + token cost — live model required. |

## Running

```sh
# This hermetic subset (no creds):
uv run pytest tests/src/praxis/contract_tests/decision_quality/ -q

# Full suite (confirms the 14/9/23 count gates still pass):
uv run pytest tests/ -q -p no:cacheprovider
```
