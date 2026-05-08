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
9.6 Cleo supply-chain    uv.lock SHA pinning + dependency monitoring + CI automation
  ↓
9.9 Test-strategy ratification  2 gaps: Q-B3-7 Tier 4 marker + Q-B3-17 ContractViolation vocabulary
```

---

## Stage 9.6 — Cleo Supply-Chain (Expanded Scope)

Original scope: uv.lock SHA pinning for `mem0ai==1.0.11` + `letta-client==1.10.3`.

**Expanded 2026-05-08:** add full dependency monitoring + CI automation so pins stay current automatically after ratification.

| Deliverable | File | Purpose |
|---|---|---|
| SHA pin policy | `uv.lock` + `pyproject.toml` version bounds | Lock `mem0ai` + `letta-client` to exact SHAs; Cleo W-2 license audit |
| Dependency monitoring config | `.github/renovate.json` (preferred over Dependabot — native uv workspace support) | Weekly scan of all `adapters/*/pyproject.toml` + `shell/package.json`; opens PRs per bump; patch → auto-merge label, minor/major → review label |
| CI contract-test gate | `.github/workflows/contract-tests.yml` | Triggers on PRs touching `adapters/**` or `uv.lock`; runs `uv run pytest tests/`; all 40+ contract tests must pass before merge |
| Weekly security audit | `.github/workflows/audit.yml` | Cron Monday 09:00; runs `pip-audit --require-hashes -r uv.lock` + `npm audit` in `shell/`; opens GitHub issue on CVE hit |
| Auto-merge policy | Renovate config + branch protection rules | Patch bumps auto-merge if contract-test CI green; minor/major require Winston review + Andrey explicit go |

**Bump-type policy (binding after 9.6 ratification):**
- `PATCH` (1.0.11 → 1.0.12): Renovate auto-merge if all contract tests pass. Zero human involvement.
- `MINOR` (1.0.x → 1.1.0): Renovate opens PR labeled `dependency:minor`. Winston reviews API surface delta against MemoryPort/CostMeterPort contract. Executor updates adapter if needed.
- `MAJOR` (1.x → 2.0): Full halt-cycle. Adapter rewrite may be required. Stage gate + Andrey go.

**Who owns ongoing operation after 9.6:**
- Renovate Bot — detection + PR creation
- CI — contract test gate
- Amelia — adapter code changes for minor/major bumps
- Winston — API delta review on minor/major
- Murat — confirms contract test catalog covers updated adapter
- Andrey — approves major version bumps; any no_waiver allow-list changes

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

### 9.6 done when
- [ ] `uv.lock` SHA-pinned for mem0ai + letta-client (Cleo W-2 satisfied)
- [ ] `.github/renovate.json` committed + Renovate app installed on repo
- [ ] `.github/workflows/contract-tests.yml` green on main
- [ ] `.github/workflows/audit.yml` green on first scheduled run
- [ ] Auto-merge policy tested: one patch bump merged end-to-end without human touch
- [ ] Bump-type policy documented in `docs/dependency-policy.md`
- [ ] Andrey explicit "continue" go to 9.9

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
| 9.5 arch review + 9.6 + 9.9 | 4–5 sessions |
| **Total Stage 9 remaining** | **~12–16 sessions** |

---

## Quick Reference: What the Next Executor Needs

**For 9.4.4 Phase A.2 (next work):**
- HEAD = `1a42896`; working tree clean (2 untracked docs only: `docs/epam-security-clearance-email-draft.md`, `docs/openclaw-setup-guide.md`)
- Authorized file: `ports/src/praxis/ports/cost_meter.py` (new file)
- 7 DTOs from A.1 ADR corrigendum — read A.1 commit body for verbatim field definitions
- API_VERSION = "1.0.0" (new port, first version)
- §9.C check: `isinstance(PiMonoNativeAdapter(), CostMeterPort) == True` must hold after B
- Halt discipline: no `adapters/`, no `tests/`, no `kernel/` touches in Phase A.2
