# Verdaca — Remaining Work to POV-Ready

**Compiled:** 2026-05-08 | **Current HEAD:** `1a42896` | **Stage:** 9.4.4 in-progress

---

## Immediate: Stage 9.4.4 Pi-Mono (In Flight)

| Phase | What | Status |
|---|---|---|
| A.1 | ADR corrigendum — pin 7 DTOs in `ports-architecture.md` | ✅ DONE |
| A.2 | Author `ports/cost_meter.py` (7 DTOs: `CostRecord`, `CostSummary`, `CostQuery`, `BillingEvent`, `UsageReport`, `ThrottleSignal`, `BudgetAlert`) | 🔄 NEXT |
| B | `adapters/pi_mono_native/` (200-LOC Python pricing math) + 8 M-T-COST-* contract tests + ADR | ⬜ BLOCKED on A.2 |
| C | 9.4.4 close-handoff + §provenance table | ⬜ BLOCKED on B |

---

## Stage 9 Sequence After 9.4.4

```
9.4.4 Pi-Mono    [IN FLIGHT]
  ↓
9.4.5 RTK        ports/llm_proxy.py + Docker sidecar + live-Letta orchestration (7 deferred probes)
  ↓
9.4.6 Forge      Forge adapter (implied by G-1 BLOCKING GATE)
  ↓
9.4.2 TONL       Deferred-work (authorized separate launch — not blocking sequence)
  ↓
9.4.7 Atomic PR  Delete 12 namespace markers + archive legacy _bmad-output/praxis/ tree (F9 audit included)
  ↓
9.4.8 Upstream bump workflow
  ↓
9.5 Architectural review  F10 praxis.kernel asymmetry + F11/F12/F13 coupled marker-registration landing
  ↓
9.6 Cleo supply-chain    uv.lock SHA pinning for mem0ai==1.0.11 + letta-client==1.10.3
  ↓
9.9 Test-strategy ratification  2 gaps: Q-B3-7 Tier 4 marker + Q-B3-17 ContractViolation vocabulary
```

---

## Stage 7 Debt Items That Gate Future Milestones

| Item | Blocks | Priority |
|---|---|---|
| **C-4** — Memory `mac.reuse_successful` promotion path | Production launch headline | HIGH — resolve before external demos |
| **A4** — Spearman ρ ≥ 0.6 human validation | Headline caveat removal | HIGH |
| **C-1..C-3, C-5** — arch contradictions | POV delivery quality | MEDIUM |
| W-1..W-7 Cleo WARNINGs | Code quality | MEDIUM |
| PDF + pptx export | Stage 7 completeness | LOW |
| "Built With Verdaca" dashboard badge | Pre-sales asset | LOW |

---

## Per-Stage Gate Criteria (What Must Be True Before Next Stage Opens)

### Before 9.4.5 starts
- [ ] 9.4.4 Phase C close-handoff complete
- [ ] §provenance table in close memo
- [ ] Andrey explicit "continue" go

### Before 9.6 starts
- [ ] Forge G-1 BLOCKING GATE cleared (Cleo W-2 license audit)
- [ ] 9.4.5 RTK close + 7 live-Letta probes resolved

### Before Stage 10 (if applicable)
- [ ] F10 architectural review complete at 9.5
- [ ] F11/F12/F13 coupled landing done
- [ ] 9.9 test-strategy ratification complete

---

## Rough Sequence Estimate (Sessions, Not Calendar Days)

| Work block | Sessions estimate |
|---|---|
| 9.4.4 A.2+B+C | 2–3 sessions |
| 9.4.5 RTK | 3–4 sessions |
| 9.4.6 Forge | 2–3 sessions |
| 9.4.7 atomic PR + 9.4.8 | 1 session |
| 9.5 arch review + 9.6 + 9.9 | 3–4 sessions |
| **Total Stage 9 remaining** | **~11–15 sessions** |

---

## Quick Reference: What the Next Executor Needs

**For 9.4.4 Phase A.2 (next work):**
- HEAD = `1a42896`; working tree clean (2 untracked docs only: `docs/epam-security-clearance-email-draft.md`, `docs/openclaw-setup-guide.md`)
- Authorized file: `ports/src/praxis/ports/cost_meter.py` (new file)
- 7 DTOs from A.1 ADR corrigendum — read A.1 commit body for verbatim field definitions
- API_VERSION = "1.0.0" (new port, first version)
- §9.C check: `isinstance(PiMonoNativeAdapter(), CostMeterPort) == True` must hold after B
- Halt discipline: no `adapters/`, no `tests/`, no `kernel/` touches in Phase A.2
