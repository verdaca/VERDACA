# Stage 9.4.6 — A.1-JOHN-1 Retro-DTO-PINNING Audit Report

**Audit cycle:** Pre-A.1 gate clearance for Stage 9.4.6 (Forge CompactionPort) launch
**Executor:** E1 (Audit work-stream; disjoint from E2 G-1 license audit)
**Predecessor SHA:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff, 2026-05-12)
**Chain at audit:** 24-SHA, unchanged at hand-back (ZERO commits this cycle)
**Date:** 2026-05-13
**Status:** GAP_FOUND_PORT_SERIALIZATION → 9.4.6 launch BLOCKED pending corrigendum

---

## §1 Scope

Per Q-9.4.5-17 locked at Stage 9.4.5 Phase A.1 (commit `de365ff`): retroactive DTO PINNING audit across Stage 9.1 ports — `memory`, `cost_meter`, `serialization`, `common`.

**Audit question:** Are all DTOs in those 4 ports explicitly PINNED in the corresponding ADR's §3, with corrigendum-DTO additions and schema-overlap composition documented?

**Out-of-scope (executor 2 territory):** Forge upstream substrate identity, G-1 license audit, Docker-on-Windows readiness probe. These are tracked in E2's parallel audit and the Phase A.1 sub-charter.

---

## §2 Methodology

### §2.1 Substrate resolution (corrected at E1-H1)

Per A-E1-H1-{1,2,3,4} amendments locked at H#1 advisor disposition:

| Layer | Substance source |
|---|---|
| ADR substance (primary) | `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` (gitignored at `.gitignore:30` per `_bmad-output/` rule) |
| Authoritative on divergence | Corrigendum commit-message bodies, fetched via `git log -1 --format=%B <SHA>` — discipline declared verbatim in `de365ff` commit body: *"in case of divergence between local files and this commit body, this commit body is the authoritative corrigendum-of-record"* |
| Port code | `ports/src/praxis/ports/{memory,cost_meter,serialization,common}.py` (tracked) |
| Ports architecture (reference only) | `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` (gitignored, secondary substrate) |

**Note on handover path-drift:** Original handover §3.1 + §10 cited tracked `docs/adr-9.1.*.md` and `docs/ports-architecture.md` paths. Both paths return zero files. Substance lives at the gitignored `_bmad-output/` paths above. Surfaced as F-9.4.6-HANDOVER-PATH-DRIFT-1 (cosmetic; handover-template lineage).

### §2.2 Port → ADR mapping (corrected at E1-H1 per A-E1-H1-1)

| Port | Port file | ADR / section | Corrigendum lineage SHAs |
|---|---|---|---|
| memory | `ports/src/praxis/ports/memory.py` | port-contracts.md §1 / ADR-9.1.2-1 | `685ecb0` (open), `f843d44` (substance close), `4b0a829` (port-file convergence) |
| cost_meter | `ports/src/praxis/ports/cost_meter.py` | port-contracts.md §5 / ADR-9.1.2-5 | `b0c333c` (OPENS-and-CLOSES F-9.4.4-COST-DTO-01) |
| serialization | `ports/src/praxis/ports/serialization.py` | port-contracts.md §2 / ADR-9.1.2-2 | NONE — section never corrigendum'd; Status: *"PROPOSED. No v0.2 amendment."* |
| common | `ports/src/praxis/ports/common.py` | port-contracts.md §0 Cross-Cutting Conventions (NOT a numbered ADR; §0.1 errors / §0.2 VerdacaDTOMixin / §0.3 deprecation / §0.4 OTEL) + Message DTO sibling-add per A.1-WINSTON-1 | `de365ff` (Message DTO §3.7 sibling-add of ADR-9.1.2-6 with class body in `common.py`) |

### §2.3 DTO enumeration approach

For each port `.py` file, grep pattern set (Python conventions per port-contracts.md §0.2 mandate of Pydantic BaseModel via VerdacaDTOMixin + frozen + `extra="forbid"`; errors use `@dataclass(kw_only=True)`):

- `^class \w+\(VerdacaDTOMixin\):` — DTO classes (primary)
- `^class \w+\(BaseModel\):` — DTO classes (fallback; should be empty per §0.2)
- `^@dataclass` followed by `^class` — error-hierarchy dataclasses
- `^class \w+\(.*Enum\):` — Enum-shaped DTOs
- `^class \w+\(NamedTuple\):` — NamedTuple DTOs (none expected)

Each found class cross-referenced against port-contracts.md ADR §3 (or §0 for common) for class-name presence + field-by-field body match + corrigendum SHA reference + `extra="forbid"` discipline (inherited from VerdacaDTOMixin).

### §2.4 Corrigendum commit-body cross-reference

Per A-E1-H1-4 (executor MUST cross-reference local file against authoritative commit body): fetched 5 corrigendum commit bodies verbatim via `git log -1 --format=%B <SHA>` for SHAs `685ecb0`, `f843d44`, `4b0a829`, `b0c333c`, `de365ff`. Field-by-field comparison against local file substance. Zero divergence between local file and any commit body across all 4 ports.

### §2.5 Schema-overlap composition (advisor F2 §0.2 invariant sample)

For common-port audit, sampled 2 downstream DTOs that inherit VerdacaDTOMixin:
- `MemoryEntry` (memory.py:41) — fields content/metadata/confidence/source_span_id
- `CostReport` (cost_meter.py:135) — fields entries/total_usd/query/pricing_table_versions

Composition check: both inherit schema_version + correlation_id + idempotency_key from VerdacaDTOMixin; field-name namespace is collision-free; `extra="forbid"` propagates structurally. CLEAN.

---

## §3 Per-port findings

### §3.1 memory port — **CLEAN**

| Field | Value |
|---|---|
| Port file | `ports/src/praxis/ports/memory.py` (249 lines) |
| ADR | port-contracts.md §1 / ADR-9.1.2-1 |
| Doc version at audit | v0.2.1 (§1 ADR header line 128) |
| DTOs in port code | 9: MemoryEntry, MemoryHit, PromotionTier, PromotionRationale, StoredMemory, MemoryQuery, PromotedMemory, RevokedPromotion, MigrationReport |
| Errors in port code | 2: PromotionContractViolation, PromotionRevocationFailed |
| DTOs PINNED in §3 (base 4) | MemoryEntry, MemoryHit, PromotionTier, PromotionRationale — bodies at port-contracts.md lines 153–173 |
| DTOs PINNED in §3.6 (corrigendum 5) | StoredMemory, MemoryQuery, PromotedMemory, RevokedPromotion, MigrationReport — bodies at port-contracts.md lines 252–275 |
| Errors PINNED in §3.4 | Both errors at port-contracts.md lines 181–189 |
| §3.6 section | PRESENT as *"Result + Query DTOs (v0.2.1 NEW — F-9.4.3-MEM-DTO-01 close)"* |
| §3.7 section | N/A (memory has no §3.7) |
| Commit-body cross-reference | `685ecb0` (open) + `f843d44` (Amendment C = §3.6 substance) + `4b0a829` (port-file 5-DTO field-spec landing) — port-code field-by-field byte-equivalent to f843d44 Amendment C verbatim text |
| Disposition | **CLEAN** |
| Notes | Zero divergence between local file, commit bodies, and port code. PINNING discipline complete |

### §3.2 cost_meter port — **CLEAN**

| Field | Value |
|---|---|
| Port file | `ports/src/praxis/ports/cost_meter.py` (245 lines) |
| ADR | port-contracts.md §5 / ADR-9.1.2-5 |
| Doc version at audit | v0.2.2 (§5 ADR header line 660) |
| DTOs in port code | 7: BudgetScope, CostEvent, CostBreakdown, CostLedgerEntry, BudgetStatus, CostQuery, CostReport |
| Errors in port code | 2: PricingTableMismatch, ParityDrift |
| DTOs PINNED in §3 (base 5) | BudgetScope, CostEvent, CostBreakdown, CostLedgerEntry, BudgetStatus — bodies at port-contracts.md lines 682–711 |
| DTOs PINNED in §3.6 (corrigendum 2) | CostQuery, CostReport — bodies at port-contracts.md lines 763–779 |
| Errors PINNED in §3 (taxonomy block) | Both errors at port-contracts.md lines 716–727 |
| §3.6 section | PRESENT as *"Result + Query DTOs (v0.2.2 NEW — F-9.4.4-COST-DTO-01 close)"* |
| §3.7 section | N/A |
| Commit-body cross-reference | `b0c333c` (Amendment C = §3.6 substance) — port-code field-by-field byte-equivalent to commit-body authoritative text |
| Disposition | **CLEAN** |
| Notes | Cost-meter has explicit *"zero no_waiver allow-list entries"* discipline per port code line 25 + §3.4 enforcement-gate-only narrative. Pricing-table-version field load-bearing for cross-port parity audit (ParityDrift surface) |

### §3.3 serialization port — **GAP_FOUND**

| Field | Value |
|---|---|
| Port file | `ports/src/praxis/ports/serialization.py` (193 lines) |
| ADR | port-contracts.md §2 / ADR-9.1.2-2 |
| Doc version at audit | v0.2 (§2 Status: *"PROPOSED. No v0.2 amendment."* — line 317) |
| DTOs in port code | 3: SerializablePayload, EncodedBytes, **RoundtripFuzzReport** |
| Type aliases in port code | 1: **JsonValue** (PEP 695 recursive type, port code line 50) |
| Errors in port code | 2: SchemaEvolutionFailure, RoundtripDriftDetected |
| DTOs PINNED in §3 | SerializablePayload (port-contracts.md lines 336–338), EncodedBytes (lines 340–343) — **only 2 of 3 DTOs in code** |
| DTOs MISSING from §3 (DIV) | **`RoundtripFuzzReport`** — referenced only as return type at port-contracts.md line 334 (`def fuzz_roundtrip(...) -> RoundtripFuzzReport: ...`); **zero class body in §3 Decision**. Port code introduces 4 fields (sample_count, seed, samples_passed, encoding_format) without ADR §3 pinning |
| Type aliases MISSING from §3 (DIV) | **`JsonValue`** type alias — port code line 50 declares novel PEP 695 recursive type: `type JsonValue = bool \| int \| float \| str \| None \| list[JsonValue] \| dict[str, JsonValue]`. Cited in port-code comment (lines 44–50) as *"port-contracts.md v0.2 §2.3 line 305"* but only appears as inline comment in §3 Decision code block (port-contracts.md line 337: `# JsonValue = recursive primitive type`), NOT as a typed declaration |
| Errors PINNED in §3 | SchemaEvolutionFailure, RoundtripDriftDetected — bodies at port-contracts.md lines 349–358 |
| §3.6 section | NOT PRESENT — serialization §2 has never been corrigendum'd |
| §3.7 section | N/A |
| Commit-body cross-reference | NONE — no corrigendum commits for §2 |
| **Disposition** | **GAP_FOUND** |
| **F-class declared** | **F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01** (DECLARED at [E1-H3 → E1-H4]) — hard DTO PINNING gap; parallel to F-9.4.3-MEM-DTO-01 / F-9.4.4-COST-DTO-01 / F-9.4.5-LLM-DTO-01 precedent pattern |
| **F-class declared (secondary)** | **F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01** (DECLARED at [E1-H3 → E1-H4]) — secondary type-alias PINNING gap; sibling to F-FUZZREPORT-01; both close in same Stage 9.1.2-2 corrigendum (advisor authoring decision at corrigendum sub-charter) |

### §3.4 common port — **CLEAN_CONVENTIONAL**

| Field | Value |
|---|---|
| Port file | `ports/src/praxis/ports/common.py` (175 lines) |
| ADR | port-contracts.md §0 Cross-Cutting Conventions (NOT a numbered ADR) |
| Doc version at audit | v0.2.3 (doc-level, port-contracts.md line 4) |
| Errors in port code (§0.1) | 6: VerdacaPortError, TransientError, ContractViolation, UpstreamUnavailable, BudgetExceeded, IdempotencyViolation |
| DTOs in port code (§0.2 + §3.7-sibling) | 2: VerdacaDTOMixin, **Message** |
| §0.1 PINNED | All 6 errors at port-contracts.md lines 54–87 — verbatim field-name + type match |
| §0.2 PINNED | VerdacaDTOMixin at port-contracts.md lines 96–101 — all 3 fields + frozen + `extra="forbid"` present |
| §0.3 Deprecation Policy | PRESENT — port-contracts.md lines 106–118; port code aligns via `schema_version` + `API_VERSION` discipline (cross-ref `ports-architecture.md` §6 per docstring line 11) |
| §0.4 OTEL Trace Context | PRESENT — port-contracts.md lines 120–122; port code carries `correlation_id` via VerdacaDTOMixin |
| Message DTO sibling-add (§3.7-equivalent) | Body at port code lines 133–156; substance-of-record at port-contracts.md §6 ADR-9.1.2-6 §3.7 + `de365ff` commit body Amendment D — **byte-equivalent** to commit-body authoritative text |
| Schema-overlap composition (§2.5 sample) | CLEAN — MemoryEntry + CostReport sampled; both inherit VerdacaDTOMixin without field collision; `extra="forbid"` propagates structurally |
| Commit-body cross-reference | `de365ff` (Message DTO §3.7 sibling-add) — port code byte-equivalent to commit-body Amendment D |
| **Disposition** | **CLEAN_CONVENTIONAL** |
| **Minor anomaly (NOT hard gap)** | Port-code docstring lines 16–19 label Message DTO as *"§0.5 Message DTO ... per port-contracts.md v0.2.3 §3.7 corrigendum at SHA `de365ff`"*. Port-contracts.md §0 contains only §0.1–§0.4 (no §0.5 section heading). Substance IS pinned (in §3.7 + de365ff body); only the port-code-internal section label is the cross-reference inconsistency. Per advisor F2 disposition class: conventional-discipline gap, NOT hard PINNING violation |
| **F-class candidate (cosmetic)** | F-9.4.6-A1J1-COMMON-MSG-XREF-COSMETIC-01 (CANDIDATE; advisor will decide carry-forward at close memo) |

---

## §4 Disposition summary

| Port | Status |
|---|---|
| memory | **CLEAN** |
| cost_meter | **CLEAN** |
| serialization | **GAP_FOUND** (1 hard DTO gap + 1 secondary type-alias gap) |
| common | **CLEAN_CONVENTIONAL** (with 1 cosmetic docstring-cite anomaly) |

**Overall:** `GAP_FOUND_PORT_SERIALIZATION` (single-port gap class per handover §3.3).

### §4.1 Stage-level implications

9.4.6 Phase A.1 (Forge CompactionPort) is **BLOCKED** on Stage 9.1.2-2 serialization-port §3 corrigendum landing. Per handover §3.3 disposition mapping: `GAP_FOUND_PORT_X` (single port) → corrigendum window opens at Stage 9.1.X; 9.4.6 launch blocked until gap closes.

Expected corrigendum substance (advisor authoring, NOT this audit's scope):

1. Expand port-contracts.md §2 §3 with `RoundtripFuzzReport` class body (4 fields per port-code body lines 89–103 or equivalent) — closes F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01
2. Pin `JsonValue` PEP 695 type alias in §3 (inline code-block declaration OR §3.6/§3.7 addition) — closes F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01
3. Doc-version bump: §2 v0.2 → v0.2.1 (serialization first corrigendum); doc-level v0.2.3 → v0.2.4 likely
4. Paired sweep per `feedback_corrigendum_paired_sweep` across `test-strategy.md` + `ports-architecture.md` + `pipeline-stage9.md` per cite-bump analysis (advisor responsibility post-cycle)

---

## §5 Recommendations

### §5.1 BLOCKING — 9.4.6 launch gate

- Open Stage 9.1.2-2 serialization §3 corrigendum window
- Land F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 close
- Land F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01 close
- Paired-sweep landing per `feedback_corrigendum_paired_sweep` (advisor scope)

### §5.2 COSMETIC — close-memo §F-docket carry-forward

- F-9.4.6-HANDOVER-PATH-DRIFT-1 (CANDIDATE; handover-template lineage; surfaced at E1-H1)
- F-9.4.6-HANDOVER-§3.6-FRAMING-DRIFT-1 (CANDIDATE NEW at [E1-H3 → E1-H4]; sibling handover-template lineage)
- F-9.4.6-A1J1-COMMON-MSG-XREF-COSMETIC-01 (CANDIDATE; docstring §0.5 vs §3.7 label mismatch)

### §5.3 NON-BLOCKING OBSERVATIONS — for 9.4.6 Phase A.1 sub-charter context

- **cost_meter `zero no_waiver allow-list entries` discipline** (port code line 25 + §3.4 enforcement-gate-only narrative) — useful reference for 9.4.6 CompactionPort allow-list scope decision
- **common port VerdacaDTOMixin invariant composition** is clean across sampled ports (MemoryEntry + CostReport) — confirms §0.2 discipline stability for any 9.4.6 CompactionPort DTOs that will inherit the mixin

---

## §6 Provenance

| Field | Value |
|---|---|
| Predecessor SHA | `5b7019f` (Stage 9.4.5 RATIFIED close-handoff, 2026-05-12) |
| Audit cycle | Pre-A.1 gate clearance for Stage 9.4.6 (Forge CompactionPort) launch |
| Audit executor | E1 (this session); concurrent disjoint E2 G-1 license audit + WS-δ Docker readiness probe |
| Cycle write budget | 1 untracked report file (this file); ZERO commits, ZERO stages, ZERO memory writes |
| Chain at hand-back | 24-SHA, unchanged at HEAD `5b7019f` |
| Working-tree at hand-back | 4 baseline `??` (preserved verbatim from predecessor) + 1 new audit-report `??` = 5 untracked |
| Advisor disposition trail | E1-H1 (preload + path-drift findings 1–3 → ACCEPT with A-E1-H1-1..4) → E1-H2 (audit plan + 8 expectations → ACCEPT) → E1-H3 (audit execution + GAP_FOUND surface → ACCEPT with 4 confirmations + 2 F-class DECLARED + 4 amendments A-E1-H3-1..4) → E1-H4 (this file write) |
| Substrate-source resolution | Local gitignored `_bmad-output/.../port-contracts.md` + corrigendum commit-body-of-record on divergence (per `de365ff` body discipline); zero divergence found this cycle |
| Date of audit | 2026-05-13 |

Working-tree state at audit close: 7 `??` = 4 baseline (`epam-security-clearance-email-draft.md` + `openclaw-setup-guide.md` + `stage-9.4.6-handover-advisor.md` + `stage-9.4.6-handover-executor.md`) + 1 audit-stream landing (this report) + 2 concurrent scout-stream landings (`stage-9.4.6-g1-license-audit.md` + `stage-9.4.6-docker-readiness.md`, authored by E2 work-stream in disjoint cycle). Drift expected per concurrent-cycle design; no F-class declared per [E1-H4 → E1-H5] advisor disposition.

---

## §7 F-class ledger

### §7.1 DECLARED (hard PINNING gaps; 9.4.6 launch blockers)

**F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01** — DECLARED at [E1-H3 → E1-H4].

> Stage 9.1.2-2 serialization ADR §3 Decision section declares `def fuzz_roundtrip(...) -> RoundtripFuzzReport: ...` at port-contracts.md line 334 but provides zero class body for `RoundtripFuzzReport`. Port code at `ports/src/praxis/ports/serialization.py` lines 89–103 introduces a 4-field DTO body (sample_count, seed, samples_passed, encoding_format) without ADR §3 anchor. Class: hard DTO PINNING gap; parallel to F-9.4.3-MEM-DTO-01 / F-9.4.4-COST-DTO-01 / F-9.4.5-LLM-DTO-01 precedent pattern. Open at this audit; close-target = Stage 9.1.2-2 §3 corrigendum landing (advisor authoring at separate cycle).

**F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01** — DECLARED at [E1-H3 → E1-H4].

> Stage 9.1.2-2 serialization port code line 50 declares novel PEP 695 recursive type alias `type JsonValue = bool | int | float | str | None | list[JsonValue] | dict[str, JsonValue]`. Cited as "port-contracts.md v0.2 §2.3 line 305" in port-code comment but appears in port-contracts.md only as an inline comment in §3 Decision code block (line 337: `# JsonValue = recursive primitive type`), NOT as a typed declaration. Class: secondary type-alias PINNING gap; sibling to F-FUZZREPORT-01; both close in same Stage 9.1.2-2 corrigendum (likely; advisor authoring decision at corrigendum sub-charter).

### §7.2 CANDIDATE (cosmetic; advisor disposition pending at close memo)

**F-9.4.6-HANDOVER-PATH-DRIFT-1 (CANDIDATE)**

> Stage 9.4.6 executor handover §3.1 + §10 cited tracked `docs/` paths (`docs/adr-9.1.*.md`, `docs/ports-architecture.md`) for substance that actually lives at gitignored `_bmad-output/implementation-artifacts/verdaca/stage9/` paths. Class: handover-template lineage (analogous to AM-C-1 class, but at handover-template surface, not pipeline-line surface). Disposition recommendation: surface in close memo §F-docket; propose carry-forward to future port-touching handovers (handover authors must NOT cite tracked `docs/` paths for substance that lives in `_bmad-output/`).

**F-9.4.6-HANDOVER-§3.6-FRAMING-DRIFT-1 (CANDIDATE)**

> Stage 9.4.6 executor handover §3.1 step 4 described "§3.6 schema-overlap invariant" as the §3.6 role, but actual §3.6 in port-contracts.md is "corrigendum-DTO additions" slot (per memory §3.6 + cost_meter §3.6 evidence). Schema-overlap invariant is a §0.2 VerdacaDTOMixin property, sampled correctly at common-port audit. Class: handover-template lineage (sibling to F-9.4.6-HANDOVER-PATH-DRIFT-1). Audit-trail anchor: surfaced at E1-H3 §2.1 memory port notes; locked at [E1-H3 → E1-H4] advisor disposition; carry-forward to future port-touching handovers.

**F-9.4.6-A1J1-COMMON-MSG-XREF-COSMETIC-01 (CANDIDATE)**

> `ports/src/praxis/ports/common.py` docstring lines 16–19 label Message DTO as "§0.5 Message DTO ... per port-contracts.md v0.2.3 §3.7 corrigendum at SHA `de365ff`". Port-contracts.md §0 contains only §0.1–§0.4 (no §0.5 section heading exists). Substance IS pinned (in §6 ADR-9.1.2-6 §3.7 + de365ff commit body Amendment D); only the port-code-internal section label is the cross-reference inconsistency. Class: cosmetic docstring-cite mismatch; not a blocker. Advisor disposition pending at close memo; possible close mechanism = port-code docstring patch (relabel "§0.5" → "§3.7 sibling-add per common.py host").

---

## §8 Q-9.4.6-* slate

**Q-9.4.6-1** — gitignore-caveat substance-source resolution for A.1-JOHN-1 audit substrate (port-contracts.md + ports-architecture.md both gitignored).
> Status: **RESOLVED** at E1-H1 disposition. Substance = local gitignored file + commit-message-of-record authoritative on divergence (per `de365ff` body discipline; `feedback_preload_tracking_status_verification` firing at 9.4.6). Carry-forward: handover-template improvement per F-9.4.6-HANDOVER-PATH-DRIFT-1.

**Q-9.4.6-2** — 9.4.6 Phase A.1 corrigendum target: gitignored port-contracts.md (with commit-message-of-record discipline) OR propose promoting port-contracts.md to a tracked `docs/` path?
> Status: **FORWARD** to Phase A.1 sub-charter (advisor scope; out of this audit's scope).

**Q-9.4.6-3** (NEW at E1-H3) — serialization §3 corrigendum timing: open as dedicated Stage 9.1.2-2 corrigendum cycle BEFORE 9.4.6 Phase A.1, OR bundle into 9.4.6 Phase A.1 as pre-substance step?
> Status: **FORWARD** to advisor close synthesis. Initial lean (advisor): dedicated cycle for substance purity (corrigendum is Stage 9.1.2 substance, not 9.4.6); decided at synthesis after both E1 + E2 gate-clearance reports land.

---

*End of A.1-JOHN-1 audit report.*
