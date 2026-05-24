"""Memory Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2.1 §1 / ADR-9.1.2-1.
Vendor strategy: `ports-architecture.md` v0.2 §3 ADR-9.2-V1
(dual-adapter Mem0 primary + Letta substitute-readiness per
substitute-readiness clause at `port-contracts.md` v0.2.1 §3
substitute-readiness clause).

This module introduces zero new contract substance. Pure Python, no
upstream imports.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

18 binding MAC-Ts at `test-strategy.md` v0.2 §2.2.1:
    M-T-MEM-PROMO-01..04 (PS-1..PS-4; allow-list entries #17–#20)
    M-T-MEM-STORE-01/02 / -QUERY-01..04 / -MIGRATE-01/02 / -REVOKE-01
    M-T-MEM-UNAVAIL-01 / -IDEMPOTENT-01 / -SPANRELABEL-01
"""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Literal, Protocol, Sequence, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    TransientError,
    VerdacaDTOMixin,
)

# ---------------------------------------------------------------------------
# DTOs — pinned per ADR-1 §3 corrigendum (port-contracts.md v0.2.1)
#   §3 base DTOs (4): MemoryEntry, MemoryHit, PromotionTier, PromotionRationale
#   §3.6 result/query DTOs (5 new at v0.2.1): StoredMemory, MemoryQuery,
#     PromotedMemory, RevokedPromotion, MigrationReport
# ---------------------------------------------------------------------------


class MemoryEntry(VerdacaDTOMixin):
    """A memory candidate to be stored.

    Per `port-contracts.md` v0.2.1 ADR-1 §3. `metadata` MUST contain
    primitives only (str | int | float | bool); upstream-specific object
    types are forbidden by `extra="forbid"` (inherited from
    VerdacaDTOMixin).
    """

    content: str
    metadata: dict[str, str | int | float | bool]
    confidence: float
    source_span_id: str


class MemoryHit(VerdacaDTOMixin):
    """A memory query hit returned by `MemoryPort.query`.

    Per `port-contracts.md` v0.2.1 ADR-1 §3 (with v0.2.1 tier-
    normalization clause). `tier` is post-normalized via AP-3
    TierNormalizer; adapters MUST normalize upstream-native tier labels
    before DTO construction. Unmapped upstream tiers raise
    `ContractViolation` at the adapter boundary.
    """

    hit_id: str
    content: str
    confidence: float
    tier: Literal["working", "session", "promoted"]


class PromotionTier(str, Enum):
    """Promotion target tier for `MemoryPort.promote`.

    Per `port-contracts.md` v0.2.1 ADR-1 §3. Only SESSION and PROMOTED
    are valid promotion targets; "working" is the entry tier (see
    `MemoryHit.tier` Literal) and is NOT a promotion target.
    """

    SESSION = "session"
    PROMOTED = "promoted"


class PromotionRationale(VerdacaDTOMixin):
    """Caller-supplied rationale for `MemoryPort.promote`.

    Per `port-contracts.md` v0.2.1 ADR-1 §3. `threshold_met` is the
    observed confidence at promotion time; `threshold_required` is the
    contractual minimum (PS-1 binding clause at §3.4 PS-1).
    """

    threshold_met: float
    threshold_required: float
    promoting_actor: str
    evidence_span_ids: list[str]


class StoredMemory(VerdacaDTOMixin):
    """Return DTO for `MemoryPort.store`; identifier-only thin-wrapper.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.6.
    """

    stored_id: str   # JUDGMENT thin-wrapper; type per cross-DTO Memory ID convention


class MemoryQuery(VerdacaDTOMixin):
    """Parameter DTO for `MemoryPort.query`; semantic-query shape with top-K.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.6.
    """

    query_text: str   # JUDGMENT semantic-query shape
    k: int            # JUDGMENT — Pythonic identifier for §2.2.1 "top-K" math symbol


class PromotedMemory(VerdacaDTOMixin):
    """Return DTO for `MemoryPort.promote`; promotion-id thin-wrapper.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.6.
    """

    promotion_id: str   # source-pin §3.4 PS-2 + PS-4; type per cross-DTO ID convention (JUDGMENT)


class RevokedPromotion(VerdacaDTOMixin):
    """Return DTO for `MemoryPort.revoke_promotion`; carries id + reason echo.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.6.
    """

    promotion_id: str   # method-sig echo from revoke_promotion(promotion_id, ...)
    reason: str         # method-sig echo from revoke_promotion(..., reason)


class MigrationReport(VerdacaDTOMixin):
    """Return DTO for `MemoryPort.migrate`; reports version pair + count + signature.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.6.
    """

    from_version: int           # method-sig echo from migrate(from_version, ...)
    to_version: int             # method-sig echo from migrate(..., to_version)
    entries_migrated: int       # cross-port sibling: MigrationResult.snapshots_created (versioned_state.py:63), renamed for Memory scope  # noqa: E501
    migrator_signature: str     # source-pin: test-strategy.md §2.2.1 M-T-MEM-MIGRATE-01


# ---------------------------------------------------------------------------
# Error specializations — verbatim per ADR-1 §3.4
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class PromotionContractViolation(ContractViolation):
    """Promotion attempted with confidence below contractual threshold,
    OR adapter promoted entries the Protocol did not request.

    Per `port-contracts.md` v0.2.1 ADR-1 §3.4 PS-1: raised by `promote()`
    if `rationale.threshold_met < rationale.threshold_required`. Bound by
    M-T-MEM-PROMO-01 (allow-list entry #17): must carry
    `requested_threshold` and `actual_confidence` per ADR-1 §3.4.
    """

    requested_threshold: float
    actual_confidence: float


@dataclass(kw_only=True)
class PromotionRevocationFailed(TransientError):
    """Adapter could not revoke a promotion (upstream eventual-consistency).

    Per `port-contracts.md` v0.2.1 ADR-1 §3.4 PS-4: raised during the
    conformance-asserted SLO window if revocation cannot be confirmed.
    Bound by M-T-MEM-PROMO-04 (allow-list entry #20): must carry
    `promotion_id` per ADR-1 §3.4.
    """

    promotion_id: str


# ---------------------------------------------------------------------------
# Protocol surface — verbatim per ADR-1 §3 method signatures
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryPort(Protocol):
    """Promotion-aware memory with substitute-ready dual-adapter contract.

    Per `port-contracts.md` v0.2.1 §1 ADR-9.1.2-1 design intent: the
    promotion semantic (PS-1..PS-4 at §3.4) is Verdaca-owned and
    non-delegable; adapters wrap Mem0 (primary) and Letta
    (substitute-readiness) per ADR-9.2-V1 dual-adapter pattern.
    Substitute-readiness clause at §3 substitute-readiness clause:
    Protocol MUST be implementable on top of either substrate without
    modification.

    Async / streaming / idempotency profile (ADR-1 §3 idempotency table):
        store              — sync, idempotent (idempotency_key required)
        query              — sync, idempotent (sequence return)
        promote            — sync, idempotent (idempotency_key required)
        revoke_promotion   — sync, idempotent (idempotency_key required)
        migrate            — sync (long-running OK), NOT idempotent
                             (single-fire per version pair)

    `@runtime_checkable` decoration follows the 9.4.1 `VersionedStatePort`
    + 9.4.2 `SerializationPort` precedent. Adapter `on_init()` performs
    `isinstance(self, MemoryPort)` self-check per executor playbook §9.C
    addendum (substrate API surface verified per F7 precedent —
    structural Protocol matching, NOT nominal inheritance).
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def store(self, entry: MemoryEntry) -> StoredMemory: ...

    def query(self, q: MemoryQuery) -> Sequence[MemoryHit]: ...

    def promote(
        self,
        hit_id: str,
        target_tier: PromotionTier,
        rationale: PromotionRationale,
    ) -> PromotedMemory: ...

    def revoke_promotion(self, promotion_id: str, reason: str) -> RevokedPromotion: ...

    def migrate(self, from_version: int, to_version: int) -> MigrationReport: ...


__all__ = [
    "API_VERSION",
    "MemoryEntry",
    "MemoryHit",
    "MemoryPort",
    "MemoryQuery",
    "MigrationReport",
    "PromotedMemory",
    "PromotionContractViolation",
    "PromotionRationale",
    "PromotionRevocationFailed",
    "PromotionTier",
    "RevokedPromotion",
    "StoredMemory",
]


API_VERSION: str = MemoryPort.API_VERSION
