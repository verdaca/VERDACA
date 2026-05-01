# Changelog — praxis-adapter-beads

Adapter for `praxis.ports.versioned_state.VersionedStatePort`. Greenfield
in-tree implementation per ADR-9.2-V3 v0.5 corrigendum.

## v0.1.0 — 2026-04-28 — Initial greenfield in-tree adapter against `VersionedStatePort` contract per ADR-9.2-V3 v0.5 corrigendum. Verdaca-authored Python, no upstream substrate. Codename "Beads" inherited from Stage 9 frame; not a substrate-lift target.

- In-process `dict[str, list[_SnapshotRecord]]` snapshot store, lock-guarded
  for thread safety. Sufficient for the 10 `M-T-VS-*` MAC-Ts at
  `test-strategy.md` v0.2 §2.2.3. Substrate hardening (Postgres backing,
  durability across process restart) deferred to Stage 10 per ADR-9.2-V3 v0.5
  Hand-offs.
- `VersionedStatePort` is `@runtime_checkable` on the port-package side
  (added at Stage 9.4.1 port-scaffold step as an agent-initiative additive
  decision; documented here per Cleo 9.6 supply-chain-review awareness from
  the 9.4.1 port-package code review). The adapter's `on_init()` performs an
  `isinstance(self, VersionedStatePort)` self-check as the §2.2 lifecycle
  contract self-check.
- `_force_snapshot_at()` adapter-internal admin method exposed for the
  `M-T-VS-CONFLICT-01` test scenario (forcing a specific `snapshot_version`
  to reproduce the conflict path). Not part of the `VersionedStatePort`
  surface; underscore-prefixed; not exported via `__all__`. Cleo 9.6 grep
  rule for "kernel never imports from `adapters/`" continues to enforce
  isolation; the adapter-internal admin is a test-surface concern only.
- `migrator_signature` derivation: `sha256(inspect.getsource(migrator).encode())`
  with `repr(migrator)` fallback for built-ins/lambdas without source.
  Audit-stable across calls with identical Migrator code (M-T-VS-MIGRATE-SIG-01).
- `M-T-VS-GAP-01` trigger: `migrate(key, from_version, to_version, migrator)`
  raises `MigrationGap` when no snapshot exists at `from_version` for the
  given key, OR when `migrator(source.value)` returns a value whose
  `schema_version` does not match `to_version`. Carries `available_versions`
  enumerating the payload_schema_versions actually present.

### Discipline-preserved invariants

- Adapter never authors a concrete migrator (M-T-VS-MIGRATE-02 grep target
  `adapters/beads/src/praxis/adapters/beads/` returns zero matches for the
  migrator-class regex; concrete migrator implementations live at
  `ports/src/praxis/ports/migrator/`).
- Adapter does NOT import from `kernel/memory/_internal/beads/` — those are
  audit-trail consumers and stay put per ADR-9.2-V3 v0.5 Migration impact §.
- Adapter does NOT import any upstream `beads` package — there is no upstream;
  the codename is a Stage 9 frame label only.
