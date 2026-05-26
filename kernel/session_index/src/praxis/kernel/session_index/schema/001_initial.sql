CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NULL,
    title TEXT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL,
    skill_ids_json TEXT NOT NULL,
    artifact_ids_json TEXT NOT NULL,
    source_uri TEXT NULL,
    schema_version INTEGER NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS session_fts USING fts5(
    session_id UNINDEXED,
    content,
    created_at UNINDEXED,
    updated_at UNINDEXED,
    status UNINDEXED
);

CREATE TABLE IF NOT EXISTS artifact_refs (
    session_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_uri TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    schema_version INTEGER NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NULL,
    PRIMARY KEY (session_id, artifact_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    session_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    skill_id TEXT NULL,
    payload_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NULL,
    PRIMARY KEY (session_id, occurred_at, event_type)
);

CREATE TABLE IF NOT EXISTS skill_invocations (
    observation_id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    outcome_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NULL,
    UNIQUE (skill_id, session_id, observed_at, outcome_json)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_source_uri ON sessions(source_uri);
CREATE INDEX IF NOT EXISTS idx_skill_invocations_skill_id ON skill_invocations(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_invocations_observed_at ON skill_invocations(observed_at);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('001_initial');
