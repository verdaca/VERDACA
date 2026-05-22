# Session Index Schema Migrations

Stage 10 introduces the `praxis-kernel-session-index` package and its SQLite
substrate for `SessionIndexPort` and `SkillTelemetryPort`.

## Migration Index

| Version | Packaged file | Purpose |
|---|---|---|
| `001_initial` | `src/praxis/kernel/session_index/schema/001_initial.sql` | Creates the session metadata tables, FTS5 keyword index, artifact refs, telemetry events, skill invocation table, schema migration marker, and query indexes. |

## Frozen Stage 10 Schema

`001_initial.sql` is the Stage 10 frozen schema for this package. It contains:

- `schema_migrations`: migration-version ledger keyed by version string.
- `sessions`: session metadata, `user_id` correlation key, content, status,
  skill/artifact ID JSON fields, DTO metadata, and idempotency key.
- `session_fts`: FTS5 virtual table for keyword-mode `search()`.
- `artifact_refs`: artifact references keyed by `(session_id, artifact_id)`.
- `telemetry_events`: session telemetry keyed by
  `(session_id, occurred_at, event_type)`.
- `skill_invocations`: skill telemetry observations keyed by deterministic
  `observation_id`, with a uniqueness guard over equivalent invocations.
- Query indexes over `sessions.user_id`, `sessions.status`,
  `sessions.created_at`, `skill_invocations.skill_id`, and
  `skill_invocations.observed_at`.

## Migration Discipline

Migrations must be idempotent and re-runnable. Use `CREATE ... IF NOT EXISTS`
for schema objects and `INSERT OR IGNORE` for `schema_migrations` entries.

Before Stage 10 ships, edits may amend `001_initial.sql` directly because no
released database is expected to rely on a prior Stage 10 schema. After Stage 10
ratification, additive or corrective schema changes must land as a new numbered
migration and must preserve already-populated development databases.

The package initializes by executing the packaged migration script via
`importlib.resources`; callers do not run the SQL directly.

## Development Database Policy

The default development database path is package-owned and resolves under the
host temporary directory:

`<tempdir>/verdaca-session-index/session-index-dev.sqlite3`

The default path must never point at the main-worktree
`knowledge/sessions.db`. Tests and CLI smoke runs may pass an explicit database
path or set the CLI environment override, but production code must not silently
reuse the Stage 9 knowledge database.
