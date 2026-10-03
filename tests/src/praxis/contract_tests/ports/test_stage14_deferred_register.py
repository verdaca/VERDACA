"""Stage 14 Phase-B — deferred-set ledger (the machine-enforced honesty spine).

This is the SINGLE TRACKED SOURCE OF TRUTH for everything Stage 14 deferred. Per
the Phase-B roundtable (Murat/Winston/Cleo, ratified):

  - "Name it, don't fake-green it": every deferred capability is a NAMED entry
    here, carried in the suite as a SKIP with a two-axis reason — never a silent
    absence.
  - Three-way encoding: PLAIN-GREEN mechanism/characterization tests prove what
    is genuinely testable now (referenced via ``guard_ref``); the cross-the-
    frozen-line "real" test is a SKIP with a named flip-trigger; strict-xfail is
    RESERVED for "would pass if a named in-scope task ran" (none here — that was
    the hoist fence's correct use).
  - Attestation honesty (refined): the auditor-facing ``caveat`` lives HERE, on
    tracked structure — NOT grepped from the gitignored B-6 prose. The meta-
    tests assert the register matches the ratified set and every caveat/axis is
    well-formed (the drift-canary pattern). A close-memo doc-lint at H#9 checks
    the TRACKED close memo carries these caveats.

Enforcement is via the META-TESTS below (CI-real, on tracked data) — NOT a
blanket ``pytest_collection_modifyitems`` hook, which would fail collection on
the pre-existing postgres ``skip``s that carry no O-# reason.

Plain tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is unaffected;
skip/xfail are orthogonal to the no_waiver inventory walk).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pytest

VALID_AXES: Final[frozenset[str]] = frozenset(
    {"TRANSIENT-CREDS", "DURABLE-FROZEN", "DURABLE-ARCH"}
)
VALID_MARKER_KINDS: Final[frozenset[str]] = frozenset(
    {"skip", "xfail-strict", "plain-green"}
)


@dataclass(frozen=True)
class DeferredItem:
    """One named Stage-14.x deferral.

    ``axis`` — TRANSIENT-CREDS (needs creds/VPN/IdP; flips in staging) ·
    DURABLE-FROZEN (needs a frozen-surface REFREEZE) · DURABLE-ARCH (needs an
    architecture/topology change, no REFREEZE).
    ``caveat`` — the AUDITOR-FACING honesty line (the attestation anchor).
    ``guard_ref`` — the PLAIN-GREEN mechanism/characterization test that IS
    runnable now (or "PB-2" if it is a Phase-B add still pending).
    """

    oid: str
    axis: str
    reason: str
    flip_trigger: str
    caveat: str
    marker_kind: str
    guard_ref: str

    def skip_reason(self) -> str:
        return f"{self.oid}: {self.axis} — {self.reason} — flip:{self.flip_trigger}"


# ── The ratified Stage-14.x deferred set (single source of truth) ──────────

DEFERRED_REGISTER: Final[tuple[DeferredItem, ...]] = (
    DeferredItem(
        oid="O-9",
        axis="DURABLE-FROZEN",
        reason="durable SQLite nonce store is single-thread (check_same_thread); "
        "the worker-thread bridge uses InMemoryNonceStore",
        flip_trigger="nonce.py made thread-safe (connection-per-thread / "
        "check_same_thread=False) under REFREEZE (touches CC6.8-c no_waiver)",
        caveat="Replay rejection runs live on the in-memory store; a thread-safe "
        "PERSISTENT nonce store across the worker-thread bridge is deferred.",
        marker_kind="skip",
        guard_ref="test_phase_b_hermetic_gaps.py::test_O_9_durable_nonce_store_is_thread_affine",
    ),
    DeferredItem(
        oid="O-11",
        # axis-pending: adapter-layer persistent loop = DURABLE-ARCH; a loop that
        # lands in service.py = DURABLE-FROZEN (REFREEZE). Pinned when the fix
        # approach is chosen; SKIP either way so no Phase-B impact.
        axis="DURABLE-ARCH",
        reason="per-request asyncio.run() loops force throughput=1 via the shared "
        "_exec_lock; real concurrency needs a persistent gateway loop "
        "(axis-pending: FROZEN if the fix lands in service.py)",
        flip_trigger="a persistent gateway event loop lands (>1 in-flight admitted)",
        caveat="Throughput is capped at 1 in-flight execution across BOTH channel "
        "routes (shared _exec_lock); concurrent execution is deferred.",
        marker_kind="skip",
        guard_ref="test_channel_webhook_o11_concurrency.py "
        "(throughput=1 invariant — committed, green)",
    ),
    DeferredItem(
        oid="CC6.7-c",
        axis="DURABLE-ARCH",
        reason="vkey budget gate is SPEND-BLIND — it gates on LiteLLM-proxy-reported "
        "spend, but the LLM egresses DIRECT to DIAL, bypassing that proxy's metering",
        flip_trigger="unified egress (DIAL fronted by the LiteLLM proxy so the vkey "
        "both authorizes AND meters real model spend) — adapter/topology, no REFREEZE",
        caveat="The vkey gate MECHANISM is real (rejects a proxy-reported over-budget "
        "key); real-spend gating is NOT exercised (egress bypasses the metering proxy).",
        marker_kind="skip",
        guard_ref="test_runtime_gateway_destub.py::"
        "test_real_vkey_enforce_budget_rejects_over_budget (mechanism, green) "
        "+ test_phase_b_hermetic_gaps.py::"
        "test_CC6_7_c_llm_egress_bypasses_the_vkey_metering_proxy",
    ),
    DeferredItem(
        oid="O-8",
        axis="DURABLE-FROZEN",
        reason="('azure','gpt-4o') row absent from PRICING_TABLE; priced via the "
        "('openai','gpt-4o') row (identical $2.50/$10) by a composition decorator",
        flip_trigger="azure row added + PRICING_TABLE_VERSION re-hashed under REFREEZE "
        "(hashed, contract-asserted constant)",
        caveat="DIAL azure/gpt-4o cost is priced via the openai/gpt-4o row "
        "(verified price-identical); a native azure pricing row is deferred.",
        marker_kind="skip",
        guard_ref="test_runtime_gateway_destub.py::"
        "test_decorator_prices_azure_identically_to_openai_row (equivalence, green)",
    ),
    DeferredItem(
        oid="O-COMMERCIAL-IDP",
        axis="TRANSIENT-CREDS",
        reason="auth-first spine proven only against a LOCAL RS256 OIDC stub; "
        "commercial-IdP (Entra/Okta/Auth0) discovery+claims untested",
        flip_trigger="real IdP issuer URL + tenant creds in staging",
        caveat="Auth-first spine proven against a local RS256 stub; commercial-IdP "
        "(Entra/Okta/Auth0) discovery + claims shapes are unverified.",
        marker_kind="skip",
        guard_ref="test_channel_webhook_wiring_integration.py "
        "(local-OIDC-stub spine, green)",
    ),
    DeferredItem(
        oid="O-MEM0-DIAL-EMBEDDER",
        axis="TRANSIENT-CREDS",
        reason="Mem0 (ratified primary) needs a DIAL-backed embedder config not built "
        "(OpenAI-embedder default unavailable under DIAL-only policy); Letta wired instead",
        flip_trigger="DIAL-backed mem0 embedder config + creds",
        caveat="Memory substrate is Letta; Mem0 (ratified primary) is deferred pending "
        "a DIAL-backed embedder configuration.",
        marker_kind="skip",
        guard_ref="test_runtime_gateway_destub.py "
        "(Letta profile-gate compose + fail-closed, green)",
    ),
    DeferredItem(
        oid="O-LIVE-SMOKE",
        axis="TRANSIENT-CREDS",
        reason="real DIAL LLM / Letta memory / LiteLLM vkey backends unexercised "
        "(profile-gated construction + fail-closed are tested; live calls are not)",
        flip_trigger="VPN + DIAL_API_KEY / LETTA_* / LITELLM_* in staging",
        caveat="Production adapters are construction-wired + fail-closed + gating-"
        "tested, but NOT live-exercised (no creds/VPN in this window).",
        marker_kind="skip",
        guard_ref="test_runtime_gateway_destub.py (profile-gate compose + fail-closed) "
        "+ test_gateway_dial_contract.py (DIAL wiring under mock)",
    ),
)

RATIFIED_DEFERRED_OIDS: Final[frozenset[str]] = frozenset(
    {
        "O-9",
        "O-11",
        "CC6.7-c",
        "O-8",
        "O-COMMERCIAL-IDP",
        "O-MEM0-DIAL-EMBEDDER",
        "O-LIVE-SMOKE",
    }
)

_BY_OID: Final[dict[str, DeferredItem]] = {item.oid: item for item in DEFERRED_REGISTER}


# ── Meta-tests: the CI-real, tracked-structure honesty gate ────────────────


def test_register_matches_ratified_set() -> None:
    """No orphan, no missing — the register is exactly the ratified deferred set
    (drift canary). Adding/removing a deferral must touch BOTH sets."""
    assert {item.oid for item in DEFERRED_REGISTER} == RATIFIED_DEFERRED_OIDS
    assert len(DEFERRED_REGISTER) == len(RATIFIED_DEFERRED_OIDS)  # no dup oids


def test_every_axis_is_valid() -> None:
    for item in DEFERRED_REGISTER:
        assert item.axis in VALID_AXES, f"{item.oid}: bad axis {item.axis!r}"


def test_every_marker_kind_is_valid() -> None:
    for item in DEFERRED_REGISTER:
        assert item.marker_kind in VALID_MARKER_KINDS, f"{item.oid}: {item.marker_kind!r}"
        # No strict-xfail in the deferred set: these are architectural/cred-gated,
        # not imminent-flip (the xpass-masks-governance-breach hazard).
        assert item.marker_kind != "xfail-strict", (
            f"{item.oid}: deferred items are skip, never strict-xfail "
            "(reserved for in-scope imminent-flip)"
        )


def test_every_caveat_is_present() -> None:
    """The attestation-honesty anchor: every deferral carries an auditor-facing
    caveat HERE (tracked), so the close memo / attestation cannot over-claim past
    what the suite proves. Checked against tracked structure, not B-6 prose."""
    for item in DEFERRED_REGISTER:
        assert item.caveat.strip(), f"{item.oid}: empty caveat"
        assert item.flip_trigger.strip(), f"{item.oid}: empty flip-trigger"
        assert item.guard_ref.strip(), f"{item.oid}: empty guard_ref"


def test_durable_arch_and_frozen_are_distinguished() -> None:
    """CC6.7-c is DURABLE-ARCH (topology, no REFREEZE); O-9/O-8 are DURABLE-FROZEN
    (REFREEZE). The axis must not understate the ceremony."""
    assert _BY_OID["CC6.7-c"].axis == "DURABLE-ARCH"
    assert _BY_OID["O-9"].axis == "DURABLE-FROZEN"
    assert _BY_OID["O-8"].axis == "DURABLE-FROZEN"


def test_load_bearing_caveats_are_present_in_the_register() -> None:
    """The three load-bearing honesty caveats an auditor doc MUST carry (Cleo) —
    spend-blind (CC6.7-c), local-IdP-only (O-COMMERCIAL-IDP), throughput=1
    (O-11) — must each be a NAMED register entry with a non-empty caveat.
    Anchored to STRUCTURE (oid membership), NOT brittle prose-substring matching
    (the team-lead's refinement). The H#9 close-memo doc-lint mirrors this."""
    load_bearing = {"CC6.7-c", "O-COMMERCIAL-IDP", "O-11"}
    assert load_bearing <= {item.oid for item in DEFERRED_REGISTER}
    for oid in load_bearing:
        assert _BY_OID[oid].caveat.strip(), f"{oid}: load-bearing caveat empty"


def test_guard_refs_carry_no_pending_pb2_sentinels() -> None:
    """Hardening #1 (team-lead): 'PB-2:' was the authoring-time sentinel meaning
    'the mechanism test will exist after PB-2 runs.' Now that PB-2 is complete,
    every guard_ref must be updated to an actual test node ID. This prevents the
    'ledger says testable-now but the test is a phantom' drift."""
    pending = [item.oid for item in DEFERRED_REGISTER if "PB-2:" in item.guard_ref]
    assert pending == [], f"guard_refs still carry PB-2: sentinel: {pending}"


# ── SKIP-named placeholders: the deferred "real" tests, counted + named ────
# Each is a counted skip carrying its register reason (not a silent absence).
# The body is the cross-the-frozen-line real test, to be implemented when the
# item's flip-trigger fires.


@pytest.mark.skip(reason=_BY_OID["O-9"].skip_reason())
def test_durable_nonce_store_thread_safe_through_worker_bridge() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the durable-store-through-bridge test")


@pytest.mark.skip(reason=_BY_OID["O-11"].skip_reason())
def test_concurrent_execution_above_one_in_flight() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the >1-in-flight concurrency test")


@pytest.mark.skip(reason=_BY_OID["CC6.7-c"].skip_reason())
def test_model_spend_drives_the_vkey_gate() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the unified-egress real-spend test")


@pytest.mark.skip(reason=_BY_OID["O-8"].skip_reason())
def test_native_azure_pricing_row_at_rehashed_version() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the native-azure-row test")


@pytest.mark.skip(reason=_BY_OID["O-COMMERCIAL-IDP"].skip_reason())
def test_discover_against_commercial_idp() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the commercial-IdP discovery test")


@pytest.mark.skip(reason=_BY_OID["O-MEM0-DIAL-EMBEDDER"].skip_reason())
def test_mem0_store_query_with_dial_embedder() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — implement the mem0-DIAL-embedder test")


@pytest.mark.skip(reason=_BY_OID["O-LIVE-SMOKE"].skip_reason())
def test_live_smoke_real_backends() -> None:  # pragma: no cover
    raise AssertionError("flip-trigger reached — see the T3 live-smoke runbook (PB-4)")
