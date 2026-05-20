"""Runtime integration — arch §10.3.

MAC consumes Runtime via:

  1. :class:`AgentSpawnerProtocol` for spawning producers + reviewers
     via the ratified ``AgentRole`` dispatch (arch §10.3 + §7.2).
  2. ``verify_mcp_sdk_shape()`` — Runtime-owned, inherited verbatim.
  3. :class:`OutboxProtocol` — Path B cycle-boundary telemetry.
  4. :class:`ResourceBudget` — bound to every spawn.

**Information asymmetry binding (arch §7.2):** MAC NEVER directly imports
``ProducerMemoryProxy`` or ``ReviewerMemoryProxy`` from
``praxis.kernel.runtime.spawner``. The only legal dispatch is through
:class:`AgentRole` at :meth:`AgentSpawnerProtocol.spawn`. A grep test
(``MAC-T-NEG-MCP-PIN-01`` plus a static asymmetry grep in step 5)
enforces this structurally at collection time.

**SQ-8 dedup namespace (arch §10.3):** every MAC Path B event uses
``dedup_key = "mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq``.
Enforced via :attr:`MacPathBEmitter.DEDUP_PREFIX` class constant + a grep
test in step 5 that scans for ``dedup_key = "`` literals without the
``mac:`` prefix.

Binding anchors:
  - mac/architecture.md §7.2 Binding to Runtime §4.1 Proxies
  - mac/architecture.md §10.3 Runtime Integration (MCP pin, Path A/B)
  - runtime/architecture.md §4.1.5 ``_construct_memory_proxy`` single-point
  - runtime/architecture.md §4.3 ``ResourceBudget``
  - runtime/architecture.md §5 MCP pin + shape guard
  - mac/test-strategy.md v0.3 §6.3 MAC-T-INT-RUNTIME-SPAWNER-01 + MCP-SHAPE-GUARD-01
  - mac/test-strategy.md v0.3 §11.5 MAC-T-NEG-MCP-PIN-01
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol, runtime_checkable

from praxis.kernel.mac.budget import BudgetExceededError, ResourceBudget


# =============================================================================
# AgentRole — MAC-local mirror of runtime.models.AgentRole
# =============================================================================


class AgentRole(str, Enum):
    """Role dispatch passed to :meth:`AgentSpawnerProtocol.spawn`.

    Shape-compatible with ``praxis.kernel.runtime.models.AgentRole``. The
    MAC-local mirror exists so step 3 does not depend on the full Runtime
    package at import time; step 6 rebinds to the canonical Runtime enum.

    **PRODUCER** → receives ``ProducerMemoryProxy`` (full retrieve+write).
    **REVIEWER** → receives ``ReviewerMemoryProxy`` (write-only; retrieve
    raises ``AttributeError`` at the Python interpreter level per Runtime
    §9.0 "the punchline").
    """

    PRODUCER = "producer"
    REVIEWER = "reviewer"


# =============================================================================
# Protocols for Runtime contracts MAC consumes
# =============================================================================


@runtime_checkable
class AgentSpawnerProtocol(Protocol):
    """Shape of ``praxis.kernel.runtime.spawner.spawner.AgentSpawner`` that
    MAC consumes. Only the :meth:`spawn` entry point is pinned — MAC must
    not reach any other surface.
    """

    async def spawn(
        self,
        *,
        agent_id: str,
        role: AgentRole,
        tenant_id: str,
        budget: ResourceBudget,
    ) -> Any: ...


@runtime_checkable
class OutboxProtocol(Protocol):
    """Shape of the Runtime Path B outbox that MAC enqueues events against.

    The ``dedup_key`` parameter is enforced at MAC's side with the ``mac:``
    prefix; the outbox stores it as an idempotency key.
    """

    async def enqueue(
        self, *, dedup_key: str, payload: dict[str, Any]
    ) -> None: ...


ShapeGuardCallable = Callable[[], None]
"""Type alias for ``verify_mcp_sdk_shape()`` — zero-arg, raises on shape
mismatch. The real Runtime version lives at
``praxis.kernel.runtime.mcp_adapter.version_guard.verify_mcp_sdk_shape`` and
raises :class:`MCPSDKShapeMismatchError` on failure. MAC does not care
which exception class is raised; it only cares that the guard runs at
boot without raising."""


# =============================================================================
# Fakes for integration tests (kept in the production module so the test
# layer doesn't need to re-declare them; step 5 and beyond import these)
# =============================================================================


@dataclass
class FakeAgentSpawner:
    """In-memory :class:`AgentSpawnerProtocol` for step-3 integration tests.

    Captures every ``spawn`` call so assertions can verify the
    :class:`AgentRole` dispatch shape (``MAC-T-INT-RUNTIME-SPAWNER-01``)
    and the single-point ``_construct_memory_proxy`` binding invariant
    (enforced via grep test in step 5; here we just assert the role).
    """

    spawn_log: list[tuple[str, AgentRole, str]] = field(default_factory=list)

    async def spawn(
        self,
        *,
        agent_id: str,
        role: AgentRole,
        tenant_id: str,
        budget: ResourceBudget,
    ) -> str:
        del budget  # acknowledged but not used by the fake
        self.spawn_log.append((agent_id, role, tenant_id))
        return f"spawned:{agent_id}:{role.value}"


@dataclass
class FakeOutbox:
    """In-memory :class:`OutboxProtocol` for step-3 cycle telemetry tests.

    Captures every ``enqueue`` call so dedup-key uniqueness and ``mac:``
    prefix assertions in ``MAC-T-CYCLE-TELEMETRY-02/03`` can run without
    a real Runtime outbox.
    """

    events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    async def enqueue(
        self, *, dedup_key: str, payload: dict[str, Any]
    ) -> None:
        self.events.append((dedup_key, dict(payload)))

    @property
    def dedup_keys(self) -> list[str]:
        return [k for k, _ in self.events]


# =============================================================================
# MacRuntimeAdapter — inherits MCP pin + shape guard from Runtime
# =============================================================================


class MacRuntimeAdapter:
    """MAC's interface to Runtime (arch §10.3).

    Holds the :class:`AgentSpawnerProtocol` instance and a zero-arg
    ``verify_mcp_sdk_shape`` callable. Spawning producers and reviewers
    routes through :meth:`spawn_producer` / :meth:`spawn_reviewer`, which
    call :meth:`AgentSpawnerProtocol.spawn` with the correct
    :class:`AgentRole`. MAC never imports ``ProducerMemoryProxy`` or
    ``ReviewerMemoryProxy`` directly — step 5 enforces this via a grep
    test that scans ``praxis/kernel/mac/`` for forbidden imports.
    """

    def __init__(
        self,
        *,
        spawner: AgentSpawnerProtocol,
        shape_guard: ShapeGuardCallable,
        tenant_id: str = "default",
    ) -> None:
        self._spawner = spawner
        self._shape_guard = shape_guard
        self._tenant_id = tenant_id

    def verify_mcp_sdk_shape(self) -> None:
        """Call the Runtime-owned shape guard. Raises whatever the guard
        raises on mismatch; MAC does not translate.
        """
        self._shape_guard()

    async def spawn_producer(
        self, *, agent_id: str, budget: ResourceBudget
    ) -> Any:
        return await self._spawner.spawn(
            agent_id=agent_id,
            role=AgentRole.PRODUCER,
            tenant_id=self._tenant_id,
            budget=budget,
        )

    async def spawn_reviewer(
        self, *, agent_id: str, budget: ResourceBudget
    ) -> Any:
        return await self._spawner.spawn(
            agent_id=agent_id,
            role=AgentRole.REVIEWER,
            tenant_id=self._tenant_id,
            budget=budget,
        )


# =============================================================================
# MacPathBEmitter — SQ-8 dedup namespace enforcer
# =============================================================================


class MacPathBEmitter:
    """Cycle-boundary event emitter for MAC Path B telemetry (arch §10.3).

    **SQ-8 binding (arch §10.3):** every MAC-emitted Path B event's
    ``dedup_key`` MUST start with :attr:`DEDUP_PREFIX` (``"mac:"``). The
    class constant is grep-locked by a step-5 test that scans the MAC
    package for ``dedup_key = "`` literals without the prefix. Callers
    cannot construct a non-``mac:``-prefixed dedup_key through this
    emitter — the only public entry point is :meth:`emit`, which
    formats the key internally.
    """

    DEDUP_PREFIX: str = "mac:"
    """The ratified SQ-8 prefix. Changing this requires a Stage 5
    architecture revision; arch §10.3 grep-locks it."""

    def __init__(self, outbox: OutboxProtocol) -> None:
        self._outbox = outbox
        self._seq_by_cycle: dict[str, itertools.count[int]] = {}

    async def emit(
        self,
        *,
        cycle_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> str:
        """Enqueue a Path B event with the SQ-8 ``mac:``-prefixed
        ``dedup_key``. Returns the computed ``dedup_key`` so tests can
        assert uniqueness + monotonicity.
        """
        counter = self._seq_by_cycle.setdefault(cycle_id, itertools.count(0))
        seq = next(counter)
        dedup_key = f"{self.DEDUP_PREFIX}{cycle_id}:{event_type}:{seq:05d}"
        await self._outbox.enqueue(dedup_key=dedup_key, payload=payload)
        return dedup_key


__all__ = (
    "AgentRole",
    "AgentSpawnerProtocol",
    "BudgetExceededError",
    "FakeAgentSpawner",
    "FakeOutbox",
    "MacPathBEmitter",
    "MacRuntimeAdapter",
    "OutboxProtocol",
    "ResourceBudget",
    "ShapeGuardCallable",
)
