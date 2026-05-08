# Verdaca Stage 9.4.3 close-handoff — Memory port dual-adapter shipment + 18-MAC-T behavioral conformance

Lands the 9.4.3 sub-stage close-handoff at
`_bmad-output/planning-artifacts/Verdaca/session-handoff-20260507-stage9.4.3-close.md`.

Scope: 9.4.3 ran 6 phases over 2026-05-02 → 2026-05-04 — step-1
substance (`685ecb0`) + Phase A.1 corrigendum (`f843d44`) + Phase A.2
port-file convergence (`4b0a829`) + Phase B.1 Mem0 primary adapter
(`34a4eca`) + Phase B.2 Letta substitute adapter (`b14285b`) + Phase
B.3 18-MAC-T contract test catalog (`ae1c806`). Plus 2026-05-04
housekeeping: brand-comparison file relocated to `docs/_archive/`
(`8590720`).

Sub-stage ratification gate clears: F-9.4.3-MEM-DTO-01 closed at
A.1 (`f843d44` substance) + A.2 (`4b0a829` port-file convergence).
Behavioral conformance gate closes at B.3 (`ae1c806`) — 18 MAC-Ts
shipped under Option α runner; 28 PASSED · 2 SKIPPED · 0 FAILED on
parametric `[mem0, letta]` matrix.

Phase B → COMPLETE (B.1 + B.2 + B.3 all closed). Sub-stage 9.4.3 → RATIFIED.

---

## §2 F-dockets

**Lifecycle commits (3 SHAs):**

  - F-9.4.3-MEM-DTO-01: ADR-1 §3 enumerated 9 DTOs but pinned only 4
    at Stage 9.3 ratification; the remaining 5 DTOs (`StoredMemory`,
    `MemoryQuery`, `PromotedMemory`, `RevokedPromotion`,
    `MigrationReport`) referenced by §3.1 method signatures had no
    field bodies.
      - OPENED at `685ecb0` (Stage 9.4.3 step-1 substance commit)
      - CLOSED at `f843d44` (Phase A.1 ADR-1 §3 corrigendum;
        substance authority via Option D-refined commit body —
        `_bmad-output/implementation-artifacts/` is gitignored at
        `.gitignore:29`; commit body wins on divergence)
      - CLOSED at `4b0a829` (Phase A.2 port-file convergence; 5 DTOs
        pinned in `ports/src/praxis/ports/memory.py` per §3.6
        corrigendum substance verbatim; Path-β skeleton language
        stripped)
    Sub-stage ratification gate cleared. F-class blocker LIFTED.

**Informational citation commits (4 SHAs; D1 ACCEPT continued):**

  - `34a4eca` — Phase B.1 Mem0 adapter close commit body cites the
    docket for "F-9.4.3-MEM-DTO-01: NOT REINTRODUCED" assertion +
    grep-verification narrative. Lifecycle untouched.
  - `b14285b` — Phase B.2 Letta adapter close commit body, same
    assertion pattern. Lifecycle untouched.
  - `ae1c806` — Phase B.3 contract test catalog close commit body,
    with amended grep contract: "lifecycle UNTOUCHED" framing per
    advisor self-correction at B.2 #5 close (SHA-count predicates
    deprecated). Lifecycle untouched.
  - `<C-SHA>` — this commit (Phase C close-handoff). Informational
    citation in §2 above + post-commit verification narrative.
    Lifecycle untouched.

Grep contract: `git log --grep="F-9.4.3-MEM-DTO-01" --oneline` returns
**7 SHAs at HEAD post-Phase-C** (3 lifecycle + 4 informational).
Lifecycle-untouched is the binding predicate per Phase B advisor
self-correction at B.2 #5 close.

**No other F-classes opened during 9.4.3.** Q-MIGRATE-1 was
dispositioned as M.1 at B.1 close (`34a4eca`) — adapter-internal
migrator registry; no Protocol-level migrator parameter; no
F-9.4.3-MEM-MIGRATE-01 docket opened. M.2 path (Protocol-level
migrator) was the only alternative that would have required a new
docket; M.1 disposition keeps the docket count at 1.

---

## §3 Carry-forward (parked items)

**7 deferred probes (live-server orchestration):**

  - Probe 1 — default model resolution under live Letta (Sub-1 (c)
    caveat)
  - Probe 2 — `sha256(api_key)[:8]` collision behavior (Sub-1 (c))
  - Probe 3 — auto-create failure mode under deliberately-invalid
    model (Sub-1 (c))
  - Probe 7 — server auto-archive-management (Sub-2 verification)
  - Probe 8 — sidecar-passage search-leak end-to-end (Amendment A;
    partial-closed in mocked-mode at QUERY-01[letta])
  - Probe 9 — single-text `passages.create()` cardinality (Amendment E)
  - Probe 10 NEW — workspace-pytest collection of
    `test_memory_contract.py` under naked pytest (gated on Cleo 9.6
    workspace registration)

  Probes 1/2/3/7/8/9 → Stage 9.4.5 RTK adapter (`ports/llm_proxy.py`
  Protocol) live-server verification anchor.
  Probe 10 → Stage 9.6 Cleo supply-chain review.

**2 test-strategy gaps (carry to next ratification cycle / Stage 9.9):**

  - Q-B3-7 — No formal Memory-port Tier 4 marker minted in
    `test-strategy.md` v0.2 §3.2/§5.3 for M-T-MEM-QUERY-04. Coverage
    doc-only via test docstring + module docstring citing §3.1 row 308.
    Adapter has no authority to mint markers on initiative
    (marker-registration halt-class).
  - Q-B3-17 — §2.2.1 row 142 "ContractViolation" wording covers
    DTO-boundary contract-failure semantic class; Pydantic v2 emits
    `ValidationError` at construction. Inline bridge comment in B.3
    test body documents equivalence.

**6 NEW Q-B3-15..20 dispositions inherited (informational; in `ae1c806`):**

  - Q-B3-15: duck-typed plain-Python fakes
  - Q-B3-16: parametrize-on-function for PROMO-02 (preserves
    4-marker invariant)
  - Q-B3-17: `pytest.raises(ValidationError)` at MemoryEntry
    construction
  - Q-B3-18: trust-proxy + module-level `_tracer` rebind
    belt-and-braces
  - Q-B3-19: `APIConnectionError` requires `httpx.Request` kw-only
  - Q-B3-20: Mem0 fake `search()` signature (`limit=None` default +
    `**_` kwargs)

**5 B.2 Amendments (informational; in `b14285b` + adapter docstring):**

  - Amendment A — `query()` filters sidecar passages
  - Amendment B — `_encode_tag()` raises on `=` or `:` in str values
  - Amendment C — promotion-state cache rehydrate at on_init
  - Amendment D — AP-9 ConfidenceScaleNormalizer collapses to
    default-1.0 only (per-hit on Letta)
  - Amendment E — `store()` asserts `len(response) == 1` single-passage
    cardinality

**10 Q-B2-Sub-* dispositions (informational; in `b14285b`):**

  Sub-1 (c) hybrid singleton-agent provisioning + Sub-2 trust-default
  archive + Sub-3 Option γ tag encoding + Sub-4 Pydantic v2 + Sub-5
  unconditional `health()` + Sub-6 env-var only + Sub-7 passage-uuid
  passthrough + Sub-8 source_span_id via tag + Sub-9 server pre-1.0
  caveat + Sub-10/Sub-10b NO migrate span emission.

**2 SDK survey discrepancies (Discoveries 1+2; in `b14285b`):**

  - Discovery 1: native-confidence claim FALSIFIED (Result type has
    no `score`)
  - Discovery 2: single-Passage create FALSIFIED
    (`PassageCreateResponse = List[Passage]`)

**Letta fake `search()` ranking note (B.3 informational; zero
halt-class impact):**

  Test-file-internal tuning at B.3 #3 — fake updated to rank
  `verdaca.kind=user:str` ABOVE sidecar-tagged passages (stable within
  rank); approximates real Letta embedding-based ranking. Adapter
  behavior unchanged; no source/spec edits.

**F11/F12/F13 inherited UNTOUCHED** per `9fd420e` —
marker-registration paper-only status preserved at
`tests/pyproject.toml`; verdaca/stage9 enforcer is spec-only;
landing remains paired with enforcer at next Amelia stage.

**Brand-comparison file disposition CLOSED at `8590720`:**

  Originally parked untracked at
  `docs/brand-comparison-verdaca-vs-nuagio.md` through 9.4.3 phase
  chain (preserved baseline through A.1 / A.2 / B.1 / B.2 / B.3
  close cycles). Relocated to
  `docs/_archive/brand-comparison-verdaca-vs-nuagio.md` as user-side
  housekeeping during B.3 advisor session close-out. Substance
  unchanged. Carry-forward CLOSED.

**Workspace registration deferred to Cleo 9.6:**

  - repo-root `pyproject.toml` `[tool.uv.workspace]` members update
    (add `praxis-adapter-mem0` + `praxis-adapter-letta`)
  - `tests/pyproject.toml` `[project.dependencies]` update
  - `uv.lock` sha256 generation for `mem0ai==1.0.11` +
    `letta-client==1.10.3`
  - Carries Probe 10 NEW dependency.

---

## §4 Next-scope opening

9.4.3 RATIFIED ⇒ following items unblock:

  - **Stage 9.4.4** — Pi-Mono reimplement (`ports/cost_meter.py`
    Protocol + `adapters/pi_mono_native/` 200-LOC pricing math
    reimplementation + snapshot test against original TS output +
    ADR documenting NOT bridging TS) per
    `pipeline-stage9.md:275–279`
  - **Stage 9.4.5** — RTK adapter (`ports/llm_proxy.py` Protocol +
    Docker sidecar wiring + cost-meter ownership ADR) per
    `pipeline-stage9.md:280–283`. Orchestration anchor for Probes
    1/2/3/7/8/9 live-server verification (Sub-1 (c) hybrid + Sub-2
    archive + Amendment A sidecar-filter end-to-end + Amendment E
    single-passage cardinality).
  - **Stage 9.5** — architectural review eligibility (if
    `pipeline-stage9.md` schedules a review at 9.5)
  - **Stage 9.6** — Cleo supply-chain review:
      - `uv.lock` sha256 generation for `mem0ai==1.0.11` +
        `letta-client==1.10.3`
      - repo-root `pyproject.toml` workspace members update
      - `tests/pyproject.toml` dependencies update
      - Probe 10 NEW workspace-pytest collection unblock
  - **Stage 9.9** — next test-strategy ratification cycle:
      - Q-B3-7 Tier 4 marker formalization
      - Q-B3-17 ContractViolation/ValidationError vocabulary clarity
        for STORE-02

---

## §5 Provenance

| Field | Value |
|---|---|
| HEAD at write | `8590720b684225b1d374f7c829398d082b908ec2` (parent SHA; close-handoff commit itself does not yet exist at write time per 9fd420e + 5f34ae7 precedent) |
| Lockfile sha256 | `A3362CB3CD8D0A5E8FA39F920B3639CB4A2BEFA7FB2CA12E78AE0B3B28D119CB` (`uv.lock` at HEAD `8590720`; PowerShell `Get-FileHash -Algorithm SHA256 uv.lock` at preload) |
| Executor JSONL | `C:\Users\AndreyPopov\.claude\projects\C--Users-AndreyPopov-Documents-Anthropic\8695203d-bc7c-4711-883a-9daf7b3e48d3.jsonl` |
| Advisor JSONL | `C:\Users\AndreyPopov\.claude\projects\C--Users-AndreyPopov-Documents-Anthropic\8db2a552-297f-4b06-87bc-15b65d41b82c.jsonl` |
| Working dir | `C:\Users\AndreyPopov\Documents\Anthropic` |
| Model | `claude-opus-4-7[1m]` (Opus 4.7, 1M context) |
| Date | `2026-05-07` |

---

## §6 Handoff to next scope

**Q-MIGRATE-1 = M.1 (locked at B.1 `34a4eca`; reaffirmed at B.2
`b14285b`):**

  Adapter-internal migrator registry pattern. No Protocol-level
  migrator parameter on
  `MemoryPort.migrate(from_version, to_version) -> MigrationReport`.
  Both `Mem0Adapter` + `LettaAdapter` ship with
  `__init__(*, migrators=None)` kwarg (Q-B1-Sub-7) accepting
  per-version-pair `Callable[[dict], dict]` migrators. Protocol
  surface stays minimal; adapter internals carry the registry.
  Rationale: avoids fresh ADR-1 §3 corrigendum; aligns with
  ADR-9.2-V1 substitute-readiness clause.

**F-docket lifecycle-untouched binding predicate (locked at B.2 #5;
reaffirmed at B.3):**

  Future grep contracts specify "lifecycle untouched (no new
  open/close/amend/reopen)" rather than SHA-count predicates.
  Informational citations (D1 ACCEPT continued) accumulate as commit
  bodies cite the docket; lifecycle integrity is the load-bearing
  claim, not grep cardinality.

**Option α runner contract for Memory port contract tests (pre-Cleo
invocation):**

```
PYTHONPATH='adapters/mem0/src;adapters/letta/src' \
  uv run --with mem0ai==1.0.11 --with 'letta-client>=1.10,<2.0' \
         --package praxis-contract-tests \
         pytest tests/src/praxis/contract_tests/ports/test_memory_contract.py -v
```

  Naked `pytest` unblocks at Cleo 9.6 (Probe 10 NEW gate).

**Stamp-shape decision (carry-forward from 9.4.2-internal step-7
close-handoff at `9fd420e`):**

  Single docs commit per precedent. 9.4.3 follows the same pattern +
  Q-C-2 paired `docs/pipeline-stage9.md` flip bundled (resolves Step
  2/3/4/5 + C-4 closure pipeline-vs-HEAD inconsistency in same commit).

**Convention finding (Q-C-7 precedent verification):**

  `_bmad-output/planning-artifacts/Verdaca/` close-handoff session-docs
  ARE force-added (Option Z) per established precedent at `9fd420e`
  + `5f34ae7`. Distinct from `_bmad-output/implementation-artifacts/`
  Option D-refined commit-body-of-record convention for ratified
  specs. Convention disposition for
  `_bmad-output/implementation-artifacts/` long-term (D.1/D.2/D.3)
  remains open in team-lead queue.

---

## §7 Memory update note (already complete — no fresh authorization needed)

Memory file `project_verdaca_stage9_4_3.md` + `MEMORY.md` index line
ALREADY UPDATED 2026-05-04 per team-lead authorization at B.3
close-acknowledgment.

**Memory file updates landed 2026-05-04:**

  - Frontmatter description refreshed to incorporate B.3 + 6-SHA
    chain + 18-MAC-T catalog + 7-probe ledger + 2 test-strategy gaps
  - Body Phase B.3 section appended (Phase B status + structural
    shape + fakes + OTel fixture + 6 NEW Q-B3-15..20 + Option α
    runner results + Letta fake ranking note + 7-probe ledger + 2
    test-strategy gaps + F-docket grep deviation + workspace
    registration deferral + 6-SHA chain)
  - Phase C launch-eligibility note appended pointing to advisor +
    executor handovers at
    `session-handoff-20260505-stage9.4.3-phase-c-*.md`

**`MEMORY.md` index line refreshed 2026-05-04:**

  - From: "A.1+A.2+B.1+B.2 COMPLETE 2026-05-04 (5 SHAs end b14285b);
    both pypi adapters substitute-readiness-verified
    (mem0ai==1.0.11 + letta-client==1.10.3); B.3 + 9.4.5 eligible;
    6 probes deferred to live-server"
  - To: "A.1+A.2+B.1+B.2+B.3 COMPLETE 2026-05-04 (6 SHAs end ae1c806);
    Phase B done; 18-MAC-T contract test catalog ships; 7 probes to
    Phase C"

**§7 is INFORMATIONAL** — captures already-written status, NOT a
fresh write proposal. Per `feedback_memory_authorization`: memory
writes require explicit team-lead authorization; that authorization
was issued at B.3 close 2026-05-04; the writes landed; Phase C
closes the sub-stage and confirms memory state at HEAD.

No further memory writes proposed at Phase C launch.

---

**End of close-handoff.**
