"""R53 field allowlist enforcement on the imported TelemetryEvent.

Architecture §6.5.A + §10.4: the R53 gate is the frozen Pydantic
TelemetryEvent(frozen=True, extra='forbid') imported from
praxis.kernel.memory.telemetry.  Tests target the imported model
directly — the structural enforcement lives in Memory (Stage 3).

Test-strategy §6.5.A + §10.4.1 TestTelemetryEventPydanticGate.
OQ-TS-8 close-out: verify ALLOWED_FIELDS matches model_fields exactly.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from praxis.kernel.memory.telemetry import TelemetryEvent

TEST_TENANT_HASH = "test-hash-abc123"

# The seven ALLOWED_FIELDS from test-strategy §10.4.1
ALLOWED_FIELDS = {
    "metric_name",
    "metric_type",
    "value",
    "labels",
    "timestamp",
    "praxis_version",
    "tenant_hash",
}

FORBIDDEN_FIELDS = {
    "query_content",
    "retrieval_result",
    "embedding",
    "raw_text",
    "pii_value",
    "audit_criteria",
    "tenant_data_payload",
    "user_prompt",
}


@pytest.mark.critical
@pytest.mark.r53_structural
class TestTelemetryEventPydanticGate:
    """§10.4.1 — R53 field enforcement via the imported Pydantic model."""

    @pytest.mark.parametrize("forbidden_field", sorted(FORBIDDEN_FIELDS))
    def test_forbidden_field_rejected(self, forbidden_field: str) -> None:
        """Each R53-forbidden field raises ValidationError (extra='forbid')."""
        with pytest.raises(ValidationError, match=r"(?i)extra inputs are not permitted"):
            TelemetryEvent(
                metric_name="runtime.test",
                metric_type="counter",
                value=1.0,
                labels={"tenant_hash": TEST_TENANT_HASH},
                timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                praxis_version="0.1.0",
                tenant_hash=TEST_TENANT_HASH,
                **{forbidden_field: "leaked content"},
            )

    def test_allowed_fields_construct_successfully(self) -> None:
        """All seven allowed fields construct without error."""
        import datetime

        event = TelemetryEvent(
            metric_name="runtime.agent.spawn.duration_ms",
            metric_type="histogram",
            value=234.5,
            labels={"tenant_hash": TEST_TENANT_HASH, "agent_name": "bmad-agent-architect"},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            praxis_version="0.1.0",
            tenant_hash=TEST_TENANT_HASH,
        )
        assert event.metric_name == "runtime.agent.spawn.duration_ms"

    def test_telemetry_event_is_frozen(self) -> None:
        """Post-construction mutation raises ValidationError (frozen=True)."""
        import datetime

        event = TelemetryEvent(
            metric_name="runtime.tool.call.count",
            metric_type="counter",
            value=1.0,
            labels={"tenant_hash": TEST_TENANT_HASH},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            praxis_version="0.1.0",
            tenant_hash=TEST_TENANT_HASH,
        )
        with pytest.raises(ValidationError):
            event.metric_name = "something.else"  # type: ignore[misc]

    def test_allowed_field_set_exactly_matches_model_fields(self) -> None:
        """OQ-TS-8 close-out: introspect model_fields; must match ALLOWED_FIELDS.

        Memory's TelemetryEvent is the source of truth.  If Memory adds or
        removes a field, this test will fail — alerting Stage 4.3 that the
        §10.4.1 ALLOWED_FIELDS constant needs updating.
        """
        actual_fields = set(TelemetryEvent.model_fields.keys())
        assert actual_fields == ALLOWED_FIELDS, (
            f"TelemetryEvent.model_fields does not match ALLOWED_FIELDS.\n"
            f"  model_fields: {sorted(actual_fields)}\n"
            f"  ALLOWED_FIELDS: {sorted(ALLOWED_FIELDS)}\n"
            f"Update §10.4.1 ALLOWED_FIELDS to match Memory's source of truth."
        )
