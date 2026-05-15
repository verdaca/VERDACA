# Stage 9.4.6 — G-1 Forge License Audit (Scout Cycle, Executor 2)

**Status:** SCOUT FINDINGS — pending advisor disposition at H#5 hand-back
**Predecessor SHA:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff, 2026-05-12)
**Probe wall-clock:** ~6 min (H#3 wave 1 + wave 2)
**Halt class:** READ-ONLY external license probes; ZERO commits this cycle

---

## §1 Scope

Per Stage 9.4.6 Executor 2 scout handover §3 Task 1 + advisor amendments A-E2-H1-2 (triangulated 5-pin), A-E2-H1-4 (NOTICE verbatim discipline), A-E2-H2-1 (5-cell pin matrix), and A-E2-H2-3 (F-9.4.6-FORGE-IDENTITY-DRIFT-1 candidate seeded).

Probed five license pins across the `antinomyhq/forge` ↔ `tailcallhq/forgecode` org transfer, verified byte-equality, swept root tree for vendored sub-licenses, and captured installer-distribution surface evidence to inform Stage 9.2 ADR-9.2-V6 G-1 BLOCKING GATE disposition + Phase A.1 sub-charter authoring.

## §2 Pin matrix (5 specified → 3 effective after collapse + 1 falsification)

| Pin | Spec | Resolved target | LICENSE HTTP | SPDX | sha256 | Status |
|---|---|---|---|---|---|---|
| α | antinomyhq/forge v2.12.14 (latest tag, legacy identity) | `raw.githubusercontent.com/antinomyhq/forge/v2.12.14/LICENSE` | 200 (11338 B) | Apache-2.0 | `3c9f9035…1c0663f9` | ✅ FETCHED |
| β | antinomyhq/forge main HEAD (legacy identity, via redirect) | `raw.githubusercontent.com/antinomyhq/forge/main/LICENSE` (HEAD SHA `65a1bb0d…992c894`) | 200 (11338 B) | Apache-2.0 | `3c9f9035…1c0663f9` | ✅ FETCHED — **COLLAPSES TO ε** (identical HEAD SHA) |
| γ | antinomyhq/forge @ `8a5edab282632443` (local-dump-filename SHA) | `raw.githubusercontent.com/antinomyhq/forge/8a5edab282632443/LICENSE` | 404 | — | — | ❌ **FALSIFIED — SHA is NOT a git commit on either repo** |
| δ | tailcallhq/forgecode v2.12.14 (current canonical tag) | `raw.githubusercontent.com/tailcallhq/forgecode/v2.12.14/LICENSE` | 200 (11338 B) | Apache-2.0 | `3c9f9035…1c0663f9` | ✅ FETCHED |
| ε | tailcallhq/forgecode main HEAD (current canonical) | `raw.githubusercontent.com/tailcallhq/forgecode/main/LICENSE` (HEAD SHA `65a1bb0d…992c894`) | 200 (11338 B) | Apache-2.0 | `3c9f9035…1c0663f9` | ✅ FETCHED |

**Effective pin count:** 3 unique-content + 1 falsified-spec — β and ε share git HEAD SHA `65a1bb0d755fd4867eff9568325323bba992c894` (verified via `gh api repos/{owner}/{repo}/commits/main --jq '.sha'` on both identities; GitHub repo transfer serves identical git tree under both names).

**Byte-equality across 4 effective pins:**
```
3c9f90350449325ae2b1355d6aae26df25be58f1cfcb8ed6a44b9c4b10c663f9  antinomyhq/forge/v2.12.14/LICENSE      [α]
3c9f90350449325ae2b1355d6aae26df25be58f1cfcb8ed6a44b9c4b10c663f9  antinomyhq/forge/main/LICENSE          [β = ε]
3c9f90350449325ae2b1355d6aae26df25be58f1cfcb8ed6a44b9c4b10c663f9  tailcallhq/forgecode/v2.12.14/LICENSE  [δ]
3c9f90350449325ae2b1355d6aae26df25be58f1cfcb8ed6a44b9c4b10c663f9  tailcallhq/forgecode/main/LICENSE      [ε]
```

→ Zero intra-identity SPDX drift; zero transfer SPDX drift; zero version drift between latest tag (v2.12.14) and main HEAD.

## §3 SPDX identification + copyright attribution (verbatim)

**SPDX identifier:** `Apache-2.0` (OSI-approved; non-copyleft)

**Copyright attribution line (from LICENSE Appendix at all 4 effective pins, verbatim):**
```
Copyright 2025 Tailcall
```

**LICENSE file size:** 11,338 bytes (Apache-2.0 standard form text + APPENDIX with project-specific copyright line)

**LICENSE source-of-truth (Phase B.1 reference — pick primary upstream identity per advisor disposition):**
- Current canonical (recommended): `https://raw.githubusercontent.com/tailcallhq/forgecode/v2.12.14/LICENSE`
- Legacy redirect (preserved for provenance): `https://raw.githubusercontent.com/antinomyhq/forge/v2.12.14/LICENSE`

## §4 NOTICE file probe (per A-E2-H1-4 attribution discipline)

| Pin | NOTICE URL | HTTP | Disposition |
|---|---|---|---|
| α | `antinomyhq/forge/v2.12.14/NOTICE` | 404 | NOT PRESENT |
| β | `antinomyhq/forge/main/NOTICE` | 404 | NOT PRESENT |
| δ | `tailcallhq/forgecode/v2.12.14/NOTICE` | 404 | NOT PRESENT |
| ε | `tailcallhq/forgecode/main/NOTICE` | 404 | NOT PRESENT |

**Disposition:** No NOTICE file exists at upstream. Apache-2.0 §4(d) NOTICE-redistribution requirement is INACTIVE — there is no NOTICE text to retain in `adapters/forge/`. Downstream attribution obligations reduce to:
- §4(a) include a copy of the LICENSE in derivative works
- §4(b) cause modified files to carry prominent notices stating modifications
- §4(c) retain copyright + patent + trademark + attribution notices from Source form

The `Copyright 2025 Tailcall` line is the project-specific attribution that Phase B.1 `adapters/forge/` MUST retain at adapter source root (per §4(c)). No further VERBATIM capture required.

## §5 Vendored sub-license sweep

**Root tree at v2.12.14** (per `gh api repos/antinomyhq/forge/contents/?ref=v2.12.14 --jq '.[].name'`):

```
.config, .devcontainer, .forge, .gitattributes, .github, .gitignore, .ignore,
.rustfmt.toml, AGENTS.md, Cargo.lock, Cargo.toml, Cross.toml, LICENSE, README.md,
_config.yml, benchmarks, clippy.toml, commands, crates, diesel.toml, docs,
flake.lock, flake.nix, forge.schema.json, insta.yaml, package-lock.json,
package.json, plans, renovate.json, rust-analyzer.toml, rust-toolchain.toml,
scripts, shell-plugin, templates, vertex.json
```

**Sub-license-directory presence check** (root grep on `vendor|third|dep|extern|sub`, case-insensitive): `[]` — no vendored sub-license dirs at top-level.

**crates/ contents** (24 first-party Rust crates):
```
forge_api, forge_app, forge_ci, forge_config, forge_display, forge_domain,
forge_embed, forge_eventsource, forge_eventsource_stream, forge_fs, forge_infra,
forge_json_repair, forge_main, forge_markdown_stream, forge_repo, forge_select,
forge_services, forge_snaps, forge_spinner, forge_stream, forge_template,
forge_test_kit, forge_tool_macros, forge_tracker, forge_walker
```

All 24 crates are first-party (forge_*-prefixed). No vendored upstream crates at root crates/ tree.

**OUT-OF-SCOPE for scout cycle:** transitive Cargo dependency licensing via `Cargo.lock` (would require `cargo-deny` / `cargo-license` run against the resolved dep graph). The Forge crate's TRANSITIVE Cargo dependency tree may include non-Apache-2.0 dependencies with their own retention obligations. Surfaced as Phase A.1 follow-on consideration (see §7).

## §6 Cross-check via ports-architecture.md grep (Q-S2 disposition)

Per advisor Q-S2 YES and A-E2-H1-3 targeted-grep allowance — applied to actual path `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` (handover-stated `docs/ports-architecture.md` path-corrected; gitignore caveat per de365ff precedent applies; commit-message-of-record authoritative on divergence).

**Grep tokens:** `Forge|G-1|compaction|version.{0,8}pin|antinomyhq|tailcallhq|forgecode`
**Context:** ±2 lines
**Findings (paraphrased — ports-architecture substance NOT audited):**

- §Executive Summary line 67 confirms verbatim: *"Forge license pre-audit (G-1) is a BLOCKING GATE at 9.4.6 start, not a hedge. Non-permissive audit → fall-through to ADR-4 §6 in-tree-stub fallback. This is codified in ADR-9.2-V6 below."*
- §ADR-9.2-V6 (referenced in headline at file top): "ADR-9.2-V6 Forge G-1 BLOCKING GATE — Forge license pre-audit is a BLOCKING GATE at 9.4.6 start … Verified verbatim via 9.2.5 Red Team stress-test (5 softening attacks defended). FAIL path → fall-through to `in_tree_compaction_stub` per port-contracts.md v0.2 ADR-9.1.2-4 §3 Substitute-readiness; UPSTREAM.md line *'Compaction: in-tree fallback active, Forge replacement in progress.'*"
- §2.4 Version-Pin Mechanics — generic `version_pin.py` discipline applies to Forge adapter if PASS, no specific Forge version pin pre-named at G-1 in spec.
- §Stage 10+ debt: "Forge in-tree-stub full productionization (if G-1 fires at 9.4.6) carries forward as Stage 10 work."

**Result:** ports-architecture.md does NOT name a specific Forge version pin under G-1 (consistent with memory `project_verdaca_stage9_2.md` grep at H#2). Cross-check γ-by-pin-spec was N/A even before SHA-falsification (§2 row γ). Stage 9.2 ADR-9.2-V6 G-1 gate is satisfied by ANY permissive license outcome on the substrate identity selected for Phase B.1.

## §7 G-1 DISPOSITION + F-class candidates

### G-1 disposition (primary G-1 audit outcome)

**G-1 BLOCKING GATE → CLEAR / PASSED** on license-permissiveness axis:
- Apache-2.0 across all effective pins (α, β=ε, δ)
- Non-copyleft (no GPL/LGPL/AGPL/SSPL anywhere in pin matrix)
- Byte-identical (`3c9f9035…1c0663f9`) confirming zero transfer drift and zero version drift
- Attribution-only requirements satisfiable by routine §4(a)/(c) discipline in `adapters/forge/`
- Vendored sub-licenses absent at root; transitive Cargo dep audit deferred (§7 carry-forward)

ADR-9.2-V6 G-1 PASS-path is unblocked on license axis. Substrate-FIT axis carries separate F-class candidates below (NOT license-axis blockers; substrate-fit re-anchor for advisor).

### F-class candidates (advisor disposition pending at H#5)

Per refined 5b7019f AM-C-1: F-tokens in report-body prose are ACCEPTABLE. All tokens below are CANDIDATE class — advisor disposes at H#5 hand-back or in Phase A.1 sub-charter authoring.

1. Surfaced as F-class candidate: **F-9.4.6-FORGE-IDENTITY-DRIFT-1** — pending advisor disposition.
   - **Evidence:** `https://github.com/antinomyhq/forge` → HTTP 301 redirect to `https://github.com/tailcallhq/forgecode`; canonical upstream README references `tailcallhq/forgecode` org throughout (CI workflow, releases page, CLA assistant); `forgecode.dev/cli` install vector; main HEAD SHA `65a1bb0d…992c894` identical on both repo identities (proves repo-transfer not fork-divergence).
   - **Surface:** Stage 9.2 ADR-9.2-V6 G-1 gate originally anchored on `antinomyhq/forge` identity (per memory `project_verdaca_stage9_2.md`). Identity-of-record needs re-anchor to `tailcallhq/forgecode` in Phase A.1 sub-charter. License continuity preserved through transfer (byte-identical LICENSE), so this is identity-axis only, NOT license-axis.

2. Surfaced as F-class candidate: **F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE** — pending advisor disposition.
   - **Evidence:** Upstream README install vectors: `curl -fsSL https://forgecode.dev/cli | sh` + Nix flake (`nix run github:tailcallhq/forgecode`) + ZSH plugin (`forge setup`). No `docker run`, no `docker pull`, no `ghcr.io/…`, no `docker.io/…` in install instructions. Docker Hub search (`docker search forgecode`, `docker search forge`) returns only 2 low-signal community/unofficial images for `forgecode` (`cromulentscientist/forgecode`, `jadshe/forgecode-extension`, both 0 stars) plus unrelated namespace squatters for `forge`.
   - **Surface:** Stage 9.2 ADR-9.2-V6 PASS path is "Docker sidecar adapter" (per memory grep) — assumes a canonical Docker substrate exists upstream. With no upstream Docker image, Phase B.1 substrate-fit options are: (a) wrap the curl-installed CLI binary as subprocess substrate, (b) build an in-house Docker image FROM the upstream installer (downstream packaging burden, version-pin discipline overhead), or (c) accept that the original Docker-sidecar framing is obsolete and re-frame the adapter. Substrate-fit re-examination for Phase A.1 sub-charter (advisor scope).
   - **Cross-axis falsification candidate:** This intersects with F-9.4.5 H2-falsification rescope pattern (RTK Docker substrate-fit rescope at `2043563`). G-1 license-axis PASS does NOT imply Docker-sidecar PASS — these are orthogonal axes per `feedback_preload_api_surface_verification`.

3. Surfaced as F-class candidate: **F-9.4.6-LOCAL-DUMP-SHA-NOT-GIT-REF** (NEW, surfaced at H#3) — pending advisor disposition.
   - **Evidence:** Local Forge reference dump filename at `_bmad-output/planning-artifacts/src/antinomyhq-forgecode-8a5edab282632443.txt` carries SHA `8a5edab282632443`. Both `gh api repos/antinomyhq/forge/commits/8a5edab282632443` and `gh api repos/tailcallhq/forgecode/commits/8a5edab282632443` return HTTP 422 "No commit found for SHA". `raw.githubusercontent.com` at this SHA returns 404 on both repos.
   - **Surface:** Local-dump SHA is NOT a git commit hash — most likely interpretation is a content/packing digest produced by a docs-extraction tool (e.g., gitingest, repomix, code2prompt). This invalidates Pin γ as a license-audit-by-SHA target and means the local dump's substantive content cannot be re-anchored to a specific upstream commit. Memory updates may want to add a note that local dumps' SHA-suffixes are docs-tooling digests, not git refs (advisor scope at post-cycle memory-write authorization per `feedback_memory_authorization`).

### F-class candidates that were FALSIFIED during H#3

- ~~F-9.4.6-FORGE-LICENSE-TRANSFER-DRIFT-1~~ (seeded at A-E2-H2-1) — **FALSIFIED:** byte-equality across legacy + canonical identities (sha256 identical on all 4 effective pins).
- ~~F-9.4.6-FORGE-LICENSE-DRIFT-*~~ (seeded at A-E2-H1-2 intra-identity divergence rule) — **FALSIFIED:** byte-equality across v2.12.14 tag + main HEAD on both identities.

### Phase A.1 sub-charter carry-forward (advisor scope, NOT scout to action)

For advisor Phase A.1 sub-charter authoring consideration:
- Re-anchor Stage 9.2 ADR-9.2-V6 G-1 gate identity to `tailcallhq/forgecode` (legacy identity preserved as redirect-of-record for provenance)
- Re-examine substrate-fit framing in light of F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE
- Schedule transitive Cargo dep licensing audit (`cargo-deny`/`cargo-license` against `Cargo.lock` at v2.12.14) — out-of-scope for scout, in-scope for B.1 substrate readiness if Forge adapter proceeds
- Pin selection for Phase B.1: recommend `tailcallhq/forgecode @ v2.12.14` (current canonical, latest stable tag)

### §7 footer retro-note — F-class disposition status update

Per **[E2-H4 → E2-H5] advisor disposition** (post-H#4 surface relay), F-class status retroactively updated. The "CANDIDATE — pending advisor disposition" framing in §7 bullets above is **superseded** by the dispositions below; original framing preserved verbatim for candidate-at-write-time provenance.

| F-class token | At-H#3 status | At-H#5 status | Class |
|---|---|---|---|
| F-9.4.6-FORGE-IDENTITY-DRIFT-1 | CANDIDATE | **DECLARED** | stage-level substrate-identity drift requiring Phase A.1 ADR-9.2-V6 re-anchor |
| F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE | CANDIDATE | **DECLARED** | substrate-fit assumption falsification at ADR-9.2-V6 PASS-path level; BLOCKS Phase A.1 sub-charter authoring until re-anchor disposition lands |
| F-9.4.6-LOCAL-DUMP-SHA-NOT-GIT-REF | CANDIDATE | **DECLARED (cosmetic-class)** | docs-tooling cosmetic finding (handover-template / reference-tooling axis lineage); NOT a blocker |

**GHCR deferral note:** GHCR community-image disambiguation deferred to Phase A.1 sub-charter authoring per [E2-H4 → E2-H5] advisor disposition. Substrate-fit conclusion (F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE DECLARED) holds on upstream-distribution evidence alone (forgecode.dev/cli installer + Nix flake + ZSH plugin install vectors + Docker Hub absence); GHCR result would add 4th data point without changing class.

## §8 Provenance

**Probe wall-clock:** ~6 min (H#3 wave 1 + wave 2)
**Tool surface:** `curl -sL` (LICENSE/NOTICE fetch), `curl -sI` (HEAD), `gh api` (commit SHA resolution + repo contents listing), `sha256sum` (byte-equality), `gh release list` (latest tag resolution)
**Probe artifact retention:** raw outputs captured in conversation transcript at H#3; structured findings tables in this report
**ZERO commits this cycle**; 24-SHA chain unchanged through hand-back
**Output file disposition:** UTF-8 explicit encoding; created as `??` (untracked); preserved for advisor read
