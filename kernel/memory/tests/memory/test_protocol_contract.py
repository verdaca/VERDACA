"""Conformance test harness for MemoryProtocol.

Parameterized over backend fixtures registered in `BACKEND_FIXTURES`. Each
backend's class/factory is checked for:

1. Runtime-checkable protocol membership via `isinstance(..., MemoryProtocol)`.
2. Method presence — all 10 protocol methods exist on the backend.
3. Method signature conformance — parameter names + annotations match the
   protocol method. This catches silent drift (e.g., adding an extra kwarg,
   renaming `tenant_id`, changing the return type).
4. Async discipline — every protocol method on the backend is a coroutine
   function.

Phase 3A ships this harness with `BACKEND_FIXTURES = []`. The conformance
test functions are CONDITIONALLY DEFINED so that an empty registry
collects zero conformance cases (instead of producing "SKIPPED [NOTSET]"
placeholders). Phase 3B appends to the list and the tests come into being.

Why a harness now instead of waiting until backends exist:
- The harness IS the protocol's operational definition. If the protocol
  itself drifts, the self-audit test catches it (always runs).
- Registering backends in Phase 3B is a one-line append — faster than
  building the harness under pressure during implementation.
- Andrey reviews the harness alongside the protocol in Phase 3A; one
  review covers both artefacts.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

import pytest

from praxis.kernel.memory import models as memory_models
from praxis.kernel.memory._internal.atelier.store import AtelierStore
from praxis.kernel.memory._internal.beads.store import BeadsStore
from praxis.kernel.memory._internal.mem0_adapter.adapter import Mem0Adapter
from praxis.kernel.memory._internal.protocol import MemoryProtocol
from tests.memory.facade._helpers import make_memory
from tests.memory.mem0_adapter.fake_client import FakeMem0Client

# NOTE: this test lives under tests/memory/ and is exempted from ruff TID251
# via per-file-ignores — white-box tests may import from _internal.


# =============================================================================
# Backend registry
# =============================================================================

#: Phase 3B populates this list. Each entry is (backend_label, factory)
#: where the factory returns an instance of the backend suitable for
#: conformance checking. Factories should be zero-arg and return fresh
#: instances — no shared state between conformance runs.
BACKEND_FIXTURES: list[tuple[str, Callable[[], Any]]] = [
    ("beads", lambda: BeadsStore(tenant_hash="conformance-tenant")),
    (
        "mem0_adapter",
        lambda: Mem0Adapter(
            client=FakeMem0Client(),
            tenant_hash="conformance-tenant",
        ),
    ),
    ("atelier", lambda: AtelierStore(tenant_hash="conformance-tenant")),
    ("facade", lambda: make_memory(tenant_id="conformance-tenant")),
]


def _backend_ids() -> list[str]:
    return [label for label, _ in BACKEND_FIXTURES]


def _backend_factories() -> list[Callable[[], Any]]:
    return [factory for _, factory in BACKEND_FIXTURES]


# =============================================================================
# Protocol self-audit — always runs, independent of backend registry
# =============================================================================


PROTOCOL_METHOD_NAMES = {
    # write
    "store_task_outcome",
    "store_decision",
    "store_fact",
    # read
    "retrieve_similar_tasks",
    "retrieve_decisions",
    "retrieve_facts",
    # GDPR
    "delete",
    "export",
    "flag_and_quarantine",
    # observability
    "health",
}


def test_protocol_exposes_expected_method_set() -> None:
    """MemoryProtocol has exactly the methods architecture §2.1 names.

    If this fails, either architecture.md has drifted or the protocol has.
    Either way, the conformance harness and every backend need review.
    """
    actual = {
        name
        for name in dir(MemoryProtocol)
        if not name.startswith("_") and callable(getattr(MemoryProtocol, name))
    }
    assert actual == PROTOCOL_METHOD_NAMES, (
        f"MemoryProtocol method set drift:\n"
        f"  missing: {PROTOCOL_METHOD_NAMES - actual}\n"
        f"  extra:   {actual - PROTOCOL_METHOD_NAMES}"
    )


def test_every_protocol_method_is_async() -> None:
    """Architecture §2.1 commits every method to `async def`.

    A sync method on a backend would silently break `await memory.*()`
    in the facade. Catching it at the protocol layer prevents backends
    from ever reaching that state.
    """
    for method_name in PROTOCOL_METHOD_NAMES:
        method = getattr(MemoryProtocol, method_name)
        assert inspect.iscoroutinefunction(method), (
            f"MemoryProtocol.{method_name} must be `async def` per §2.1"
        )


def test_every_protocol_method_takes_tenant_id_first_or_is_health() -> None:
    """Every method except `health` has `tenant_id: str` as its first arg.

    §8.2 defense-in-depth invariant: the facade's tenant validation is
    triggered by the presence of this parameter. `health` is the sole
    exception — it has no tenant scope.
    """
    for method_name in PROTOCOL_METHOD_NAMES:
        method = getattr(MemoryProtocol, method_name)
        sig = inspect.signature(method)
        params = [p for p in sig.parameters.values() if p.name != "self"]

        if method_name == "health":
            assert all(p.name != "tenant_id" for p in params), (
                "MemoryProtocol.health must NOT take tenant_id — health is process-global per §2.1"
            )
            continue

        assert params, f"MemoryProtocol.{method_name} has no parameters"
        first = params[0]
        assert first.name == "tenant_id", (
            f"MemoryProtocol.{method_name} must take tenant_id as first "
            f"non-self parameter; got {first.name!r} (§8.2 invariant)"
        )
        hints = get_type_hints(method)
        assert hints.get("tenant_id") is str, (
            f"MemoryProtocol.{method_name}.tenant_id must be annotated `str`"
        )


# =============================================================================
# Error registry self-audit — always runs
# =============================================================================
#
# The protocol docstrings enumerate a small, closed set of exception types.
# These assertions lock that set in so backends and the facade can rely on
# the hierarchy not silently shifting (e.g., MemoryQuotaExceeded becoming a
# MemoryBackendError subclass and being swallowed by retry logic).


def test_error_registry_has_expected_types() -> None:
    """The four Memory error classes exist under expected names.

    If a class is renamed or deleted, this test catches it immediately
    instead of failing downstream when a backend tries to raise it.
    """
    expected = {
        "TenantIdentityError",
        "MemoryBackendError",
        "MemoryRecordNotFound",
        "MemoryQuotaExceeded",
    }
    for name in expected:
        assert hasattr(memory_models, name), (
            f"praxis.kernel.memory.models is missing expected error class `{name}`"
        )


def test_error_registry_base_classes_are_distinct_categories() -> None:
    """Each error category has a distinct base — caught independently.

    - TenantIdentityError → PermissionError (privacy/auth category)
    - MemoryBackendError  → RuntimeError    (operational category)
    - MemoryRecordNotFound→ LookupError     (lookup-miss category)
    - MemoryQuotaExceeded → Exception       (policy category — intentionally
                                              NOT a subclass of the others;
                                              see Andrey's Q+A)

    If any category collapses into another (e.g. MemoryQuotaExceeded
    becomes a MemoryBackendError), downstream retry logic will silently
    swallow quota errors. Catch that here.
    """
    assert issubclass(memory_models.TenantIdentityError, PermissionError)
    assert issubclass(memory_models.MemoryBackendError, RuntimeError)
    assert issubclass(memory_models.MemoryRecordNotFound, LookupError)

    # MemoryQuotaExceeded is plain Exception, not any of the others.
    assert issubclass(memory_models.MemoryQuotaExceeded, Exception)
    assert not issubclass(memory_models.MemoryQuotaExceeded, memory_models.MemoryBackendError)
    assert not issubclass(memory_models.MemoryQuotaExceeded, PermissionError)
    assert not issubclass(memory_models.MemoryQuotaExceeded, LookupError)


def test_memory_quota_exceeded_carries_required_attributes() -> None:
    """MemoryQuotaExceeded's constructor and attributes match the spec.

    Stage 5 MAC error-handling will depend on these attributes — lock
    them in so a future refactor can't silently drop one.
    """
    err = memory_models.MemoryQuotaExceeded(
        tenant_id="tenant-abc",
        current_count=275_000,
        ceiling_type="hard",
        ceiling_value=250_000,
    )
    assert err.tenant_id == "tenant-abc"
    assert err.current_count == 275_000
    assert err.ceiling_type == "hard"
    assert err.ceiling_value == 250_000
    # Message contains enough context for an operator to triage.
    msg = str(err)
    assert "tenant-abc" in msg
    assert "hard" in msg
    assert "275000" in msg
    assert "250000" in msg


# =============================================================================
# Draft / Record pattern self-audit — always runs
# =============================================================================


DRAFT_RECORD_PAIRS = [
    ("TaskOutcomeDraft", "TaskOutcomeRecord"),
    ("DecisionDraft", "DecisionRecord"),
    ("FactDraft", "FactRecord"),
]


def test_draft_and_record_classes_exist_per_store_method() -> None:
    """Every store_* method has a matching Draft/Record pair in models."""
    for draft_name, record_name in DRAFT_RECORD_PAIRS:
        assert hasattr(memory_models, draft_name), f"missing {draft_name}"
        assert hasattr(memory_models, record_name), f"missing {record_name}"


def test_drafts_do_not_carry_persistence_columns() -> None:
    """Draft types only expose caller-constructable semantic fields.

    Persistence columns (entry_id, tenant_hash, state_snapshot_version,
    created_at) come from _PersistedRecord and MUST NOT appear on a Draft.
    If this test fails, a Draft has leaked a persistence column and
    callers would be able to supply bogus values for fields they
    shouldn't construct.
    """
    persistence_columns = {
        "entry_id",
        "tenant_hash",
        "state_snapshot_version",
        "created_at",
    }
    for draft_name, _ in DRAFT_RECORD_PAIRS:
        draft_cls = getattr(memory_models, draft_name)
        draft_fields = set(draft_cls.model_fields.keys())
        leaked = draft_fields & persistence_columns
        assert not leaked, (
            f"{draft_name} leaked persistence columns: {leaked}. "
            f"Persistence columns belong only on *Record types."
        )


def test_records_carry_all_persistence_columns() -> None:
    """Record types have every persistence column from _PersistedRecord."""
    persistence_columns = {
        "entry_id",
        "tenant_hash",
        "schema_version",
        "state_snapshot_version",
        "created_at",
    }
    for _, record_name in DRAFT_RECORD_PAIRS:
        record_cls = getattr(memory_models, record_name)
        record_fields = set(record_cls.model_fields.keys())
        missing = persistence_columns - record_fields
        assert not missing, f"{record_name} missing persistence columns: {missing}"


def test_records_carry_literal_record_type_discriminator() -> None:
    """Each Record has a self-describing `record_type` Literal default.

    The class-level default lets `hit.record.record_type` be destructured
    without constructing the record — useful for tests and for the facade's
    routing layer.
    """
    expected_discriminators = {
        "TaskOutcomeRecord": "task_outcome",
        "DecisionRecord": "decision",
        "FactRecord": "fact",
    }
    for record_name, discriminator in expected_discriminators.items():
        record_cls = getattr(memory_models, record_name)
        assert "record_type" in record_cls.model_fields, (
            f"{record_name} missing record_type discriminator"
        )
        field = record_cls.model_fields["record_type"]
        assert field.default == discriminator, (
            f"{record_name}.record_type default is {field.default!r}, expected {discriminator!r}"
        )


# =============================================================================
# Backend conformance — parameterized, conditionally defined
# =============================================================================
#
# These test functions are defined ONLY when BACKEND_FIXTURES is non-empty.
# Phase 3A ships with an empty registry so conformance tests collect as 0
# cases, not as "SKIPPED [NOTSET]" placeholders. Phase 3B appends backends
# and the tests come into being with accurate counts.

if BACKEND_FIXTURES:

    @pytest.mark.parametrize("factory", _backend_factories(), ids=_backend_ids())
    def test_backend_is_runtime_protocol_instance(
        factory: Callable[[], Any],
    ) -> None:
        """`isinstance(backend, MemoryProtocol)` — coarse shape check.

        A runtime-checkable Protocol's `isinstance` returns True iff the
        instance has all the method names (not their signatures). Serves
        as a fast smoke test before the heavier per-method signature
        tests below.
        """
        backend = factory()
        assert isinstance(backend, MemoryProtocol), (
            f"{type(backend).__name__} fails isinstance(..., MemoryProtocol); "
            f"missing: "
            f"{sorted(PROTOCOL_METHOD_NAMES - set(dir(backend)))}"
        )

    @pytest.mark.parametrize("factory", _backend_factories(), ids=_backend_ids())
    @pytest.mark.parametrize("method_name", sorted(PROTOCOL_METHOD_NAMES))
    def test_backend_method_signature_matches_protocol(
        factory: Callable[[], Any], method_name: str
    ) -> None:
        """Each backend method has a signature compatible with the protocol.

        "Compatible" means:
          - same parameter names in the same order (minus `self`)
          - same annotations
          - same return type annotation

        Phase 3C facade composition dispatches by method name and trusts
        the signatures to line up. Drift here = latent runtime bugs.
        """
        backend = factory()
        assert hasattr(backend, method_name), (
            f"{type(backend).__name__} missing method {method_name}"
        )

        protocol_method = getattr(MemoryProtocol, method_name)
        backend_method = getattr(backend, method_name)

        protocol_sig = inspect.signature(protocol_method)
        backend_sig = inspect.signature(backend_method)

        protocol_params = [p for p in protocol_sig.parameters.values() if p.name != "self"]
        backend_params = list(backend_sig.parameters.values())

        assert [p.name for p in backend_params] == [p.name for p in protocol_params], (
            f"{type(backend).__name__}.{method_name} parameter names differ "
            f"from protocol: backend={[p.name for p in backend_params]} "
            f"protocol={[p.name for p in protocol_params]}"
        )

        for bp, pp in zip(backend_params, protocol_params, strict=True):
            assert bp.annotation == pp.annotation, (
                f"{type(backend).__name__}.{method_name}.{bp.name} "
                f"annotation differs from protocol: "
                f"backend={bp.annotation!r} protocol={pp.annotation!r}"
            )

        assert backend_sig.return_annotation == protocol_sig.return_annotation, (
            f"{type(backend).__name__}.{method_name} return annotation "
            f"differs: backend={backend_sig.return_annotation!r} "
            f"protocol={protocol_sig.return_annotation!r}"
        )

    @pytest.mark.parametrize("factory", _backend_factories(), ids=_backend_ids())
    @pytest.mark.parametrize("method_name", sorted(PROTOCOL_METHOD_NAMES))
    def test_backend_method_is_async(factory: Callable[[], Any], method_name: str) -> None:
        """Each backend's protocol method is a coroutine function.

        Backends that wrap sync libraries (SQLAlchemy core, Mem0 sync API)
        MUST wrap their sync calls in `asyncio.to_thread` or equivalent.
        """
        backend = factory()
        method = getattr(backend, method_name)
        assert inspect.iscoroutinefunction(method), (
            f"{type(backend).__name__}.{method_name} must be `async def`; "
            f"got {type(method).__name__}"
        )


# =============================================================================
# Harness sanity — catches empty-registry misuse / Phase 3B drift
# =============================================================================


def test_backend_fixture_list_is_a_list_of_pairs() -> None:
    """BACKEND_FIXTURES contract is `list[tuple[label, factory]]`.

    Guards against Phase 3B accidentally registering a bare factory
    (breaks parametrize ids) or a dict (breaks ordering).
    """
    assert isinstance(BACKEND_FIXTURES, list)
    for entry in BACKEND_FIXTURES:
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"BACKEND_FIXTURES entries must be (label, factory) tuples; got {entry!r}"
        )
        label, factory = entry
        assert isinstance(label, str) and label, "label must be a non-empty str"
        assert callable(factory), "factory must be callable"
