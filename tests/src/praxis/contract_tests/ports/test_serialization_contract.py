"""Serialization port contract tests — 12 MAC-Ts.

Per `test-strategy.md` v0.2 §2.2.2 — 12 binding `M-T-SER-*` MAC-Ts (10
binding implementations + 2 deferred-substrate skeletons for MSGSPEC
per Q1 disposition B; ADR-9.2-V2 v0.2 substrate deferral preserved).

Each test below embeds its MAC-T ID in the function name; docstrings
quote the §2.2.2 assertion language verbatim for auditability.

Discipline (per Stage 9.4.1 / 9.4.2-internal step-7 hand-offs):
- Stay strictly within the 12-ID scope. No 13th test, no parametrized
  expansion, no opportunistic coverage.
- Test the public `SerializationPort` Protocol surface via the TONL
  adapter (`praxis.adapters.tonl.adapter.TONLAdapter`).
- MSGSPEC-01 / -02 are deferred-substrate skeletons (`pytest.skip` —
  Stage 10 fill-in). NOT xfail.
- @pytest.mark.no_waiver applied to M-T-SER-EVO-01 (allow-list entry
  #21 — SchemaEvolutionFailure) + M-T-SER-FUZZ-01 (allow-list entry
  #22 — RoundtripDriftDetected) per §6.1 ratification
  (test-strategy.md:645 directive). Verdaca/stage9 22-entry enforcer
  is spec-only at present (test-strategy.md:487); structural
  enforcement gap captured in step-7 close F-docket. Marker is
  unregistered in tests/pyproject.toml (warning emitted at collection,
  non-fatal); registration paired with enforcer landing at next Amelia
  stage.
"""

from __future__ import annotations

import pytest

from praxis.adapters.tonl.adapter import TONLAdapter
from praxis.kernel.compression.tonl import encode as tonl_encode
from praxis.ports.common import ContractViolation
from praxis.ports.serialization import (
    EncodedBytes,
    RoundtripDriftDetected,
    RoundtripFuzzReport,
    SchemaEvolutionFailure,
    SerializablePayload,
)

# `RoundtripDriftDetected` is imported above for allow-list-entry-#22
# grep-discoverability (FUZZ-01 marker rationale per test-strategy.md
# v0.2 §6.1 line 470). The TONL adapter v0.1.0 takes the happy-path
# branch on valid samples, so the class is not raised in-test; the
# import is the structural reference.
_ = RoundtripDriftDetected


# Test-only payload constructors mirror the
# `test_versioned_state_contract.py` precedent (lines 50–72): helper
# functions instantiate `SerializablePayload` directly with body keyed
# by `text`/`label`/`tag` and a `payload_kind` discriminator per
# port-contracts.md v0.2 §2.3. `correlation_id` is required by
# VerdacaDTOMixin (common.py §0.2).
_TEST_CORRELATION_ID = "test-correlation-ser-contract"


def _payload_v1(
    body: str,
    *,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> SerializablePayload:
    """Test-only constructor at schema_version 1."""
    return SerializablePayload(
        schema_version=1,
        correlation_id=correlation_id,
        body={"text": body},
        payload_kind="test_payload_v1",
    )


def _payload_v2(
    body: str,
    label: str,
    *,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> SerializablePayload:
    """Test-only constructor at schema_version 2 (evolution target)."""
    return SerializablePayload(
        schema_version=2,
        correlation_id=correlation_id,
        body={"text": body, "label": label},
        payload_kind="test_payload_v2",
    )


def _payload_v3(
    body: str,
    label: str,
    tag: str,
    *,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> SerializablePayload:
    """Test-only constructor at schema_version 3 (EVO-04 third step)."""
    return SerializablePayload(
        schema_version=3,
        correlation_id=correlation_id,
        body={"text": body, "label": label, "tag": tag},
        payload_kind="test_payload_v3",
    )


@pytest.fixture
def adapter() -> TONLAdapter:
    return TONLAdapter()


# ---------------------------------------------------------------------------
# M-T-SER-ENCODE-TONL-01
# ---------------------------------------------------------------------------
def test_M_T_SER_ENCODE_TONL_01_encode_deterministic(adapter: TONLAdapter) -> None:
    """`encode(payload)` with valid `SerializablePayload` — Returns
    `EncodedBytes`; `encoded_schema_version == payload.schema_version`;
    deterministic (same input = same bytes)."""
    payload = _payload_v1("content")
    encoded_first = adapter.encode(payload)
    encoded_second = adapter.encode(payload)
    assert isinstance(encoded_first, EncodedBytes)
    assert encoded_first.encoded_schema_version == payload.schema_version
    assert encoded_first.data == encoded_second.data


# ---------------------------------------------------------------------------
# M-T-SER-DECODE-TONL-01
# ---------------------------------------------------------------------------
def test_M_T_SER_DECODE_TONL_01_roundtrip(adapter: TONLAdapter) -> None:
    """`decode(encoded, expected_schema_version)` — Returns
    `SerializablePayload` equivalent to pre-encode; roundtrip
    integrity."""
    payload = _payload_v1("roundtrip")
    encoded = adapter.encode(payload)
    decoded = adapter.decode(encoded, expected_schema_version=1)
    assert isinstance(decoded, SerializablePayload)
    assert decoded == payload


# ---------------------------------------------------------------------------
# M-T-SER-ENCODE-MSGSPEC-01 (deferred-substrate skeleton — Q1 disposition B)
# ---------------------------------------------------------------------------
def test_M_T_SER_ENCODE_MSGSPEC_01_encode_msgspec() -> None:
    """`encode(payload)` against msgspec adapter — Same contract as
    TONL; substitute parity via Protocol.

    Deferred per ADR-9.2-V2 v0.2 (`ports-architecture.md` §3): single
    TONL implementation in tree at 9.4.2; msgspec adapter substrate is
    a Stage 10 concern. Stub preserves §2.2.2 12-MAC-T count and makes
    the Stage-10 substrate-landing a fill-in: replace the pytest.skip
    line with `MsgspecAdapter()` instantiation + assertion body
    mirroring `test_M_T_SER_ENCODE_TONL_01_encode_deterministic`.
    """
    pytest.skip(
        "Stage 10 deferred per ADR-9.2-V2 v0.2 — msgspec adapter substrate not yet authored"
    )


# ---------------------------------------------------------------------------
# M-T-SER-DECODE-MSGSPEC-01 (deferred-substrate skeleton — Q1 disposition B)
# ---------------------------------------------------------------------------
def test_M_T_SER_DECODE_MSGSPEC_01_decode_msgspec() -> None:
    """`decode(encoded, ...)` against msgspec adapter — Same contract
    as TONL; substitute parity.

    Deferred per ADR-9.2-V2 v0.2 (`ports-architecture.md` §3): single
    TONL implementation in tree at 9.4.2; msgspec adapter substrate is
    a Stage 10 concern. Stub preserves §2.2.2 12-MAC-T count and makes
    the Stage-10 substrate-landing a fill-in: replace the pytest.skip
    line with `MsgspecAdapter()` instantiation + assertion body
    mirroring `test_M_T_SER_DECODE_TONL_01_roundtrip`.
    """
    pytest.skip(
        "Stage 10 deferred per ADR-9.2-V2 v0.2 — msgspec adapter substrate not yet authored"
    )


# ---------------------------------------------------------------------------
# M-T-SER-EVO-01 — allow-list entry #21 (SchemaEvolutionFailure)
# ---------------------------------------------------------------------------
@pytest.mark.no_waiver  # entry #21 — SchemaEvolutionFailure (test-strategy.md v0.2 §6.1 line 469)
def test_M_T_SER_EVO_01_can_decode_version_forward() -> None:
    """`can_decode_version(expected_v=N)` against
    `encoded_schema_version=N-1` — Returns `True` if migration path
    exists; returns `False` OR raises `SchemaEvolutionFailure`
    otherwise.

    `SchemaEvolutionFailure` (allow-list entry #21 — silent data-drift
    failure mode; recovery-hard; full-conformance warranty per
    test-strategy.md v0.2 §6.1 line 469) is the named exception class
    for the OR-branch. Imported at module top for grep-discoverability.
    The TONL adapter v0.1.0 implements the False-return branch (no
    executable forward-migration chain per
    `adapters/tonl/.../adapter.py:96–97`).
    """
    adapter_multi = TONLAdapter(supported_schema_versions={1, 2})
    assert adapter_multi.can_decode_version(1) is True
    assert adapter_multi.can_decode_version(2) is True
    # No registered support for v=3 → False return (False branch of
    # the §2.2.2 OR clause; no SchemaEvolutionFailure raised in v0.1.0
    # per substrate constraint above).
    assert adapter_multi.can_decode_version(3) is False
    assert SchemaEvolutionFailure is not None  # grep-discoverability anchor


# ---------------------------------------------------------------------------
# M-T-SER-EVO-02
# ---------------------------------------------------------------------------
def test_M_T_SER_EVO_02_decode_gap_raises(adapter: TONLAdapter) -> None:
    """`decode(encoded_v=N-2, expected_v=N)` with no migration chain —
    Raises `SchemaEvolutionFailure`; `decoded_version=N-2`,
    `expected_version=N`."""
    payload_v1 = _payload_v1("v1-payload")
    encoded_v1 = adapter.encode(payload_v1)
    with pytest.raises(SchemaEvolutionFailure) as exc_info:
        adapter.decode(encoded_v1, expected_schema_version=3)
    err = exc_info.value
    assert err.decoded_version == 1
    assert err.expected_version == 3


# ---------------------------------------------------------------------------
# M-T-SER-EVO-03
# ---------------------------------------------------------------------------
def test_M_T_SER_EVO_03_can_decode_reverse_returns_false() -> None:
    """`can_decode_version(expected_v=N-1)` against
    `encoded_schema_version=N` — Returns `False` (forward-only policy);
    no crash."""
    forward_only = TONLAdapter(supported_schema_versions={2})
    assert forward_only.can_decode_version(1) is False


# ---------------------------------------------------------------------------
# M-T-SER-EVO-04
# ---------------------------------------------------------------------------
def test_M_T_SER_EVO_04_preserve_no_field_loss() -> None:
    """Evolution across 3 versions (N → N+1 → N+2) — Roundtrip
    stability preserved; no field loss.

    Structural reading per advisor 9.4.2-internal step-7 disposition.
    v0.1.0 has no executable forward-migration chain (per
    `adapters/tonl/.../adapter.py:96–97` "forward-migration chains are
    Stage 10"); the structural property "no field loss across version
    increments" is verified via three independent same-version
    roundtrips at successive `schema_version` values registered on the
    adapter. If Stage 10 introduces an executable chain, this test's
    assertion semantics may need revision — the literal-substring pin
    above keeps the structural-reading caveat grep-discoverable.
    """
    adapter_multi = TONLAdapter(supported_schema_versions={1, 2, 3})
    p1 = _payload_v1("alpha")
    p2 = _payload_v2("beta", "label-2")
    p3 = _payload_v3("gamma", "label-3", "tag-3")
    for payload, version in [(p1, 1), (p2, 2), (p3, 3)]:
        encoded = adapter_multi.encode(payload)
        decoded = adapter_multi.decode(encoded, expected_schema_version=version)
        assert decoded == payload


# ---------------------------------------------------------------------------
# M-T-SER-FUZZ-01 — allow-list entry #22 (RoundtripDriftDetected)
# ---------------------------------------------------------------------------
@pytest.mark.no_waiver  # entry #22 — RoundtripDriftDetected (test-strategy.md v0.2 §6.1 line 470)
def test_M_T_SER_FUZZ_01_fuzz_roundtrip(adapter: TONLAdapter) -> None:
    """`fuzz_roundtrip(sample_count=1000, seed=42)` — Returns
    `RoundtripFuzzReport`; zero failing samples OR
    `RoundtripDriftDetected` raised with `failing_seed` +
    `diff_summary`.

    `RoundtripDriftDetected` (allow-list entry #22 — serialization
    roundtrip integrity; silent data-drift class per test-strategy.md
    v0.2 §6.1 line 470) is the named exception class for the OR-branch.
    Imported at module top for grep-discoverability. The TONL adapter
    v0.1.0 takes the happy-path branch (RoundtripFuzzReport returned)
    on valid samples; the drift-raise branch is exercisable only via
    fault injection, out of scope at the contract layer.
    """
    report = adapter.fuzz_roundtrip(sample_count=1000, seed=42)
    assert isinstance(report, RoundtripFuzzReport)
    assert report.sample_count == 1000
    assert report.seed == 42
    assert report.samples_passed == 1000
    assert report.encoding_format == "tonl-v0.1.0"


# ---------------------------------------------------------------------------
# M-T-SER-FUZZ-02
# ---------------------------------------------------------------------------
def test_M_T_SER_FUZZ_02_fuzz_deterministic(adapter: TONLAdapter) -> None:
    """Same `(sample_count, seed)` invoked twice — Identical
    `RoundtripFuzzReport`; deterministic."""
    r1 = adapter.fuzz_roundtrip(sample_count=100, seed=42)
    r2 = adapter.fuzz_roundtrip(sample_count=100, seed=42)
    assert r1 == r2


# ---------------------------------------------------------------------------
# M-T-SER-FUZZ-03
# ---------------------------------------------------------------------------
def test_M_T_SER_FUZZ_03_fuzz_adversarial(adapter: TONLAdapter) -> None:
    """Fuzz with adversarial payloads (nested edge cases, Unicode
    boundaries) — `RoundtripDriftDetected` raised iff drift detected;
    otherwise clean.

    The TONL adapter's `_fuzz_sample` already exercises adversarial
    payloads (nested dicts/lists at depth 3, Unicode strings including
    emoji + escape sequences, mixed primitive types) per
    `adapters/tonl/.../adapter.py:251–292`. This test asserts a clean
    `RoundtripFuzzReport` under a high-coverage seed; the IFF-drift
    raise branch is structurally encoded but not fault-injected here.
    """
    report = adapter.fuzz_roundtrip(sample_count=200, seed=1)
    assert isinstance(report, RoundtripFuzzReport)
    assert report.samples_passed == 200


# ---------------------------------------------------------------------------
# M-T-SER-EXTRA-FORBID-01
# ---------------------------------------------------------------------------
def test_M_T_SER_EXTRA_FORBID_01_decode_rejects_extra_field(
    adapter: TONLAdapter,
) -> None:
    """Decode encoded payload with extra upstream-leaked field —
    `extra="forbid"` rejects; `ContractViolation`.

    Constructs a malformed TONL byte stream containing an unauthorized
    upstream-leaked field (`leaked_field`) alongside the expected
    `body`/`payload_kind`/`schema_version` envelope keys. The adapter's
    structural enforcement at `adapters/tonl/.../adapter.py:183–185`
    raises `ContractViolation` with `violation_class="invariant"`.
    """
    malformed_envelope = {
        "body": {"text": "ok"},
        "payload_kind": "test_payload_v1",
        "schema_version": 1,
        "leaked_field": "should be forbidden",
    }
    malformed_text = tonl_encode(malformed_envelope)
    encoded = EncodedBytes(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        data=malformed_text.encode("utf-8"),
        encoding_format="tonl-v0.1.0",
        encoded_schema_version=1,
    )
    with pytest.raises(ContractViolation) as exc_info:
        adapter.decode(encoded, expected_schema_version=1)
    assert exc_info.value.violation_class == "invariant"
