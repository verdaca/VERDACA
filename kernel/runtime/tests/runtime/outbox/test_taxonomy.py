"""
Tests for CostEvent taxonomy/namespace enforcement.
All pure unit tests — no DB or Docker required.
"""

import pytest

from praxis.kernel.runtime.outbox.taxonomy import EXPECTED_COST_EVENT_TYPES, validate_namespace

# ---------------------------------------------------------------------------
# Individual namespace validation
# ---------------------------------------------------------------------------


def test_memory_retention_action_is_valid():
    assert validate_namespace("memory.retention_action") is True


def test_runtime_agent_spawn_is_valid():
    assert validate_namespace("runtime.agent_spawn") is True


def test_compression_passthrough_is_valid():
    assert validate_namespace("compression.passthrough") is True


def test_unknown_prefix_is_invalid():
    result = validate_namespace("foo.bar")
    # Implementations may return False or raise; either satisfies the contract.
    if result is not False:
        pytest.fail(f"validate_namespace('foo.bar') should return False or raise, got {result!r}")


# ---------------------------------------------------------------------------
# Exhaustive validity check against the canonical constant
# ---------------------------------------------------------------------------


def test_all_expected_event_types_are_valid():
    assert len(EXPECTED_COST_EVENT_TYPES) > 0, "EXPECTED_COST_EVENT_TYPES must be non-empty"
    for event_type in EXPECTED_COST_EVENT_TYPES:
        assert validate_namespace(event_type) is True, (
            f"Expected event type {event_type!r} failed validate_namespace()"
        )
