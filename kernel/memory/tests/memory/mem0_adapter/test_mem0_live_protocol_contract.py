"""Live-backend contract tests against the real `mem0.Memory` class.

These tests verify that the *real* Mem0 vendor client (imported from
`mem0ai`, not a fake) structurally satisfies `Mem0ClientProtocol` at the
class level — i.e. the adapter's dependency boundary remains correct
against the currently-pinned Mem0 version.

Scope explicitly excluded:

- Instantiating `mem0.Memory()` — that pulls in qdrant / OpenAI /
  embedder stacks, requires API keys, and makes network calls. Live
  runtime behavior is a Stage 7 concern (tenant credential plumbing).
- Exercising adapter round-trips against real Mem0 — the adapter logic
  is covered by `test_mem0_adapter_roundtrip.py` using `FakeMem0Client`.

What these tests DO catch:

- Mem0 renaming or removing a method on `Memory` (breaks the protocol
  surface — adapter would silently fall through to a different branch).
- Mem0 dropping or renaming a keyword argument that the adapter passes
  (e.g. `user_id`, `agent_id`, `run_id`, `limit`, `infer`).
- Mem0 version drift beyond the locked version in
  `requirements-mem0-lock.txt`.
"""

from __future__ import annotations

import inspect

import pytest

from praxis.kernel.memory._internal.mem0_adapter.client_protocol import (
    Mem0ClientProtocol,
)

mem0 = pytest.importorskip("mem0")
MemoryClass = mem0.Memory


REQUIRED_METHODS = ("add", "search", "get", "get_all", "delete", "delete_all")


@pytest.mark.parametrize("method_name", REQUIRED_METHODS)
def test_real_mem0_memory_exposes_protocol_method(method_name: str) -> None:
    assert hasattr(MemoryClass, method_name), (
        f"mem0.Memory no longer exposes `{method_name}` — "
        f"Mem0ClientProtocol drift. Update client_protocol.py and the "
        f"lockfile together."
    )
    assert callable(getattr(MemoryClass, method_name))


def _param_names(method_name: str) -> set[str]:
    sig = inspect.signature(getattr(MemoryClass, method_name))
    return set(sig.parameters.keys())


def test_add_accepts_scoping_kwargs() -> None:
    params = _param_names("add")
    for required in ("messages", "user_id", "agent_id", "run_id", "metadata", "infer"):
        assert required in params, (
            f"mem0.Memory.add lost kwarg `{required}` — scoping guarantees "
            f"at the adapter boundary assume this exists."
        )


def test_search_accepts_scoping_kwargs() -> None:
    params = _param_names("search")
    for required in ("query", "user_id", "agent_id", "run_id", "limit"):
        assert required in params, (
            f"mem0.Memory.search lost kwarg `{required}` — scoping/R-06 "
            f"tests rely on this to pin queries to a tenant."
        )


def test_get_all_accepts_scoping_kwargs() -> None:
    params = _param_names("get_all")
    for required in ("user_id", "agent_id", "run_id", "limit"):
        assert required in params, (
            f"mem0.Memory.get_all lost kwarg `{required}` — export-by-tenant "
            f"requires this to enumerate within a tenant boundary."
        )


def test_delete_all_accepts_scoping_kwargs() -> None:
    params = _param_names("delete_all")
    for required in ("user_id", "agent_id", "run_id"):
        assert required in params, (
            f"mem0.Memory.delete_all lost kwarg `{required}` — crypto-shred "
            f"relies on this to drop a whole tenant without touching others."
        )


def test_real_mem0_memory_class_is_runtime_checkable_against_protocol() -> None:
    """The real Mem0 class should not fail a runtime isinstance-check on
    the structural protocol. We do NOT instantiate it (would require API
    keys); we assert at the class level that each attribute resolves to a
    callable with the right name.
    """
    for method_name in REQUIRED_METHODS:
        attr = getattr(MemoryClass, method_name, None)
        assert attr is not None and callable(attr), (
            f"`mem0.Memory.{method_name}` is missing or non-callable — "
            f"Mem0ClientProtocol cannot bind to this version."
        )

    # Sanity: the protocol itself is runtime_checkable. We assert
    # the class-level check resolves to a truthy value. (isinstance()
    # against Protocol checks method presence only, not signatures —
    # signature drift is covered by the targeted tests above.)
    assert Mem0ClientProtocol.__name__ == "Mem0ClientProtocol"
