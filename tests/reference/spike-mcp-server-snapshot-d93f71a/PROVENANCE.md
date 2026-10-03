# FROZEN REFERENCE — DO NOT IMPORT

Reference only. See `adapters/mcp_server/` for live Verdaca implementation (lands at Stage 11 Phase C via E2 executor — `[E2-H#2]` ports `FINDINGS.md` from this snapshot; `[E2-H#3]` mirrors `src/server.ts` / `src/tools.ts` patterns; `[E2-H#4]` mirrors `src/http.ts`; `[E2-H#5]` mirrors `src/stdio.ts`).

## Provenance

| Field | Value |
|-------|-------|
| Origin path | `C:\Users\AndreyPopov\Documents\LHHP-COAC\spike-mcp-server` |
| Captured SHA (full) | `d93f71afee88fb411dd0094cc87fbc6638d1f654` |
| Captured SHA (short) | `d93f71a` |
| Capture date | `2026-05-24` |
| Captured by | Stage 11 H#1 advisor (Claude Opus 4.7 1M, party-mode session) |
| Captured into | Verdaca branch `stage-11.0-mcp-gateway` (cut from `main @ f181a7e`) |
| Triggering authority | Round 2 advisor roundtable Item 2 (Winston / Cleo / Vera / Murat unanimous — snapshot, not pin-alone) per master handover `docs/stage-10-11-implementation-executor-handover.md` §4.0.PRE |
| Spike repo state at capture | Clean working tree (`git status --short` empty); HEAD on initial commit |

## Snapshot contents

```
tests/reference/spike-mcp-server-snapshot-d93f71a/
├── PROVENANCE.md           (this file — locks origin SHA + capture provenance)
├── FINDINGS.md             (CAI spike lessons — ported line-for-line by E2 at [E2-H#2])
├── README.md               (spike's top-level overview)
├── package.json            (TS spike dependencies — informational; Verdaca uses Python `mcp` SDK)
└── src/
    ├── coaching-data.ts    (CAI domain helpers — reference for tool shape patterns)
    ├── http.ts             (Streamable HTTP transport — mirrored by adapters/mcp_server/http.py)
    ├── index.ts            (entry point)
    ├── server.ts           (FastMCP factory — mirrored by adapters/mcp_server/server.py)
    └── stdio.ts            (stdio transport — mirrored by adapters/mcp_server/stdio.py)
```

## Drift policy

If the source spike repo (`C:\Users\AndreyPopov\Documents\LHHP-COAC\spike-mcp-server`) advances past `d93f71a` post-snapshot, **this snapshot does NOT auto-update**. The snapshot is intentionally frozen at capture time for test-fixture locality (Murat Round 2 Item 2 — fixtures cannot float on external SHAs).

To consume a newer spike state in future Stage 11.x work:
1. Re-snapshot under a new sibling directory: `tests/reference/spike-mcp-server-snapshot-<new-sha>/`
2. Author a new `PROVENANCE.md` with the new SHA + capture date
3. Update downstream references (master handover §4.0.PRE example SHA, E2 handover §1.5 / §4 / §9 references)
4. Do NOT mutate this snapshot. The old snapshot remains for diff comparison and audit.

## Import discipline

**This directory is reference material. Never `import` from it in production code paths.**

Allowed consumers:
- `tests/fixtures/mcp_jsonrpc_golden/*.jsonl` — JSON-RPC trace captures derived from running `node tests/reference/spike-mcp-server-snapshot-d93f71a/src/stdio.ts` in stateless mode
- `[E2-H#2]` — reads `FINDINGS.md` for line-for-line port
- `[E2-H#3-H#5]` — reads `src/*.ts` files as shape reference for the Python port (the Python files live at `adapters/mcp_server/src/praxis/adapters/mcp_server/*.py`)

Forbidden:
- Any `from tests.reference.spike_mcp_server_snapshot_d93f71a import ...` in production code (`praxis.*`, `adapters.*`, `kernel.*`, `shell.*`)
- Modifying any file in this directory (use re-snapshot procedure above instead)
- Treating the snapshot as the live implementation (Verdaca's live MCP server is `adapters/mcp_server/`, which lands at Phase C)

A future `[tool.importlinter]` contract `spike-snapshot-not-importable` will encode this discipline at Stage 11 H#1 (per master handover §4.0.PRE import-linter rule). Pending Stage 11 H#1 dispatch.

## Cross-references

- Master handover (Stage 10/11 executor): `docs/stage-10-11-implementation-executor-handover.md` §4.0.PRE
- E2 executor handover: `docs/stage-11-e2-inbound-mcp-transport-executor-handover.md` §1 step 5 (preload availability check), §1 step 10 (entry precondition row), §4 `[E2-H#2]` (FINDINGS port source), §9 references
- Round 2 advisor roundtable disposition: party-mode session 2026-05-24
- Triggering A7 closure context: `docs/stage-10-voc-gate.md` (A7 closed 2026-05-24 via team-lead override; commit `f181a7e`)
