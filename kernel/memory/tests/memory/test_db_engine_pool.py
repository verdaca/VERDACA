"""Smoke test for NR-SC-R2 connection pool sizing.

Validates that `create_memory_engine()` applies the exact pool parameters
ratified in nfr-report.md NR-SC-R2. No live database is required — the test
spies on `sqlalchemy.create_engine` to capture the kwargs Memory's factory
passes through, and verifies them against the NR-SC-R2 constants.

Why a mock instead of a real engine: SQLite forces SingletonThreadPool
which rejects `max_overflow`, and Postgres requires a dialect driver. The
NR-SC-R2 contract is "these four kwargs reach SQLAlchemy", and that is what
we assert — directly, without needing a dialect at all.

If this test fails, the Memory module's pool configuration has drifted from
NR-SC-R2 and every downstream component is affected. Failures must be
triaged before any A3.3.4 work can land.
"""

from __future__ import annotations

from unittest.mock import patch

from praxis.kernel.memory._internal.common import db as db_module
from praxis.kernel.memory._internal.common.db import (
    MAX_OVERFLOW,
    POOL_PRE_PING,
    POOL_RECYCLE_SECONDS,
    POOL_SIZE,
    create_memory_engine,
)

# NOTE: this test lives under tests/memory/ and is exempted from ruff TID251
# via per-file-ignores in pyproject.toml — white-box tests are allowed to
# reach into _internal.


def test_nrscr2_strawman_constants() -> None:
    """The NR-SC-R2 strawman constants match the ratified values verbatim."""
    assert POOL_SIZE == 10
    assert MAX_OVERFLOW == 15
    assert POOL_PRE_PING is True
    assert POOL_RECYCLE_SECONDS == 3600


def test_factory_passes_nrscr2_kwargs_to_sqlalchemy() -> None:
    """create_memory_engine() forwards exactly the NR-SC-R2 pool kwargs."""
    url = "postgresql://fake:fake@localhost:5432/fake"
    with patch.object(db_module, "create_engine") as mock_create_engine:
        mock_create_engine.return_value = object()
        create_memory_engine(url)

    mock_create_engine.assert_called_once()
    args, kwargs = mock_create_engine.call_args

    # Positional arg must be the URL — no silent rewrites.
    assert args == (url,), f"expected positional=({url!r},), got {args!r}"

    # NR-SC-R2 kwargs must be present with exact values.
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 15
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 3600

    # No extra kwargs — NR-SC-R2 scope is exactly four parameters.
    # Andrey's constraint: "No additional pool config beyond NR-SC-R2."
    expected_keys = {"pool_size", "max_overflow", "pool_pre_ping", "pool_recycle"}
    assert set(kwargs.keys()) == expected_keys, (
        f"factory must pass only NR-SC-R2 kwargs; "
        f"extras={set(kwargs.keys()) - expected_keys}, "
        f"missing={expected_keys - set(kwargs.keys())}"
    )


def test_create_memory_engine_is_the_only_factory() -> None:
    """Sanity check: the module exposes exactly one Memory-layer factory.

    Enforces the "one pool per process" invariant from NR-SC-R2 by making it
    structurally obvious that there is no alternative construction path.
    """
    public_callables = [
        name
        for name in dir(db_module)
        if not name.startswith("_") and callable(getattr(db_module, name))
    ]
    factories = [n for n in public_callables if n.startswith("create_memory")]
    assert factories == ["create_memory_engine"], (
        f"expected exactly one Memory engine factory, found: {factories}"
    )
