"""Memory Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2 §1 / ADR-9.1.2-1.
Vendor strategy: `ports-architecture.md` v0.2 §3 ADR-9.2-V1
(dual-adapter Mem0 primary + Letta substitute-readiness per
substitute-readiness clause at `port-contracts.md` v0.2 lines 241–243).

This module introduces zero new contract substance. Pure Python, no
upstream imports.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

18 binding MAC-Ts at `test-strategy.md` v0.2 §2.2.1:
    M-T-MEM-PROMO-01..04 (PS-1..PS-4; allow-list entries #17–#20)
    M-T-MEM-STORE-01/02 / -QUERY-01..04 / -MIGRATE-01/02 / -REVOKE-01
    M-T-MEM-UNAVAIL-01 / -IDEMPOTENT-01 / -SPANRELABEL-01
    M-T-MEM-CORRELATION-01 / -CONFIDENCE-01

Substance gap — F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage ratification;
NON-BLOCKING for this step 1 file write per Path β disposition):
ADR-1 §3 enumerates 9 DTOs in method signatures but provides Pydantic
class bodies for only 4 (MemoryEntry, MemoryHit, PromotionTier,
PromotionRationale). Five DTOs (StoredMemory, MemoryQuery, PromotedMemory,
RevokedPromotion, MigrationReport) ship as Path-β skeletons; full field
specs deferred to ADR-1 corrigendum per F-9.4.3-MEM-DTO-01.
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
# DTOs — pinned per ADR-1 §3 (4 classes, lines 151–171)
# ---------------------------------------------------------------------------


class MemoryEntry(VerdacaDTOMixin):
    """A memory candidate to be stored.

    Per `port-contracts.md` v0.2 ADR-1 §3 lines 151–155. `metadata` MUST
    contain primitives only (str | int | float | bool); upstream-specific
    object types are forbidden by `extra="forbid"` (inherited from
    VerdacaDTOMixin).
    """

    content: str
    metadata: dict[str, str | int | float | bool]
    confidence: float
    source_span_id: str


class MemoryHit(VerdacaDTOMixin):
    """A memory query hit returned by `MemoryPort.query`.

    Per `port-contracts.md` v0.2 ADR-1 §3 lines 157–161 + v0.2 tier-
    normalization clause at line 174. `tier` is post-normalized via AP-3
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

    Per `port-contracts.md` v0.2 ADR-1 §3 lines 163–165. Only SESSION and
    PROMOTED are valid promotion targets; "working" is the entry tier
    (see `MemoryHit.tier` Literal) and is NOT a promotion target.
    """

    SESSION = "session"
    PROMOTED = "promoted"


class PromotionRationale(VerdacaDTOMixin):
    """Caller-supplied rationale for `MemoryPort.promote`.

    Per `port-contracts.md` v0.2 ADR-1 §3 lines 167–171. `threshold_met`
    is the observed confidence at promotion time; `threshold_required`
    is the contractual minimum (PS-1 binding clause at line 215).
    """

    threshold_met: float
    threshold_required: float
    promoting_actor: str
    evidence_span_ids: list[str]


# ---------------------------------------------------------------------------
# DTOs — Path-β skeletons per F-9.4.3-MEM-DTO-01 (5 classes)
#
# All five inherit `schema_version: int`, `correlation_id: str`,
# `idempotency_key: str | None`, plus `model_config = ConfigDict(frozen=True,
# extra="forbid")` from VerdacaDTOMixin (`praxis.ports.common` lines
# 107–120). No port-scoped fields declared — full field specs deferred to
# ADR-1 corrigendum per F-9.4.3-MEM-DTO-01.
# ---------------------------------------------------------------------------


class StoredMemory(VerdacaDTOMixin):
    """Return value of `MemoryPort.store`.

    Path-β SKELETON per F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage
    ratification). `port-contracts.md` v0.2 ADR-1 §3 references this DTO
    as the return type at line 144 but does not pin field specs. No
    path-α partial pins found; full field spec deferred to ADR-1
    corrigendum per F-9.4.3-MEM-DTO-01.
    """


class MemoryQuery(VerdacaDTOMixin):
    """Parameter type of `MemoryPort.query`.

    Path-β SKELETON per F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage
    ratification). `port-contracts.md` v0.2 ADR-1 §3 references this DTO
    as the parameter type at line 145 but does not pin field specs. No
    path-α partial pins found; full field spec deferred to ADR-1
    corrigendum per F-9.4.3-MEM-DTO-01. (`test-strategy.md` v0.2 §2.2.1
    uses "top-K" terminology in QUERY-01..04 trigger texts, suggesting a
    `k` field, but the spec is untyped in source.)
    """


class PromotedMemory(VerdacaDTOMixin):
    """Return value of `MemoryPort.promote`.

    Path-β SKELETON per F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage
    ratification). `port-contracts.md` v0.2 ADR-1 §3 references this DTO
    as the return type at line 147; PS-2 (line 217) and PS-4 (line 221)
    cite the field name `promotion_id` (type unspecified in source).
    Full field spec deferred to ADR-1 corrigendum per F-9.4.3-MEM-DTO-01.
    """


class RevokedPromotion(VerdacaDTOMixin):
    """Return value of `MemoryPort.revoke_promotion`.

    Path-β SKELETON per F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage
    ratification). `port-contracts.md` v0.2 ADR-1 §3 references this DTO
    as the return type at line 148 but does not pin field specs. No
    path-α partial pins found; full field spec deferred to ADR-1
    corrigendum per F-9.4.3-MEM-DTO-01.
    """


class MigrationReport(VerdacaDTOMixin):
    """Return value of `MemoryPort.migrate`.

    Path-β SKELETON per F-9.4.3-MEM-DTO-01 (BLOCKS 9.4.3 sub-stage
    ratification). `port-contracts.md` v0.2 ADR-1 §3 references this DTO
    as the return type at line 149; `test-strategy.md` v0.2 §2.2.1
    M-T-MEM-MIGRATE-01 trigger text (line 147) cites the field name
    `migrator_signature` (type unspecified in source). Full field spec
    deferred to ADR-1 corrigendum per F-9.4.3-MEM-DTO-01.
    """


# ---------------------------------------------------------------------------
# Error specializations — verbatim per ADR-1 §3.4
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class PromotionContractViolation(ContractViolation):
    """Promotion attempted with confidence below contractual threshold,
    OR adapter promoted entries the Protocol did not request.

    Per `port-contracts.md` v0.2 ADR-1 §3.4 PS-1 (line 215): raised by
    `promote()` if `rationale.threshold_met < rationale.threshold_required`.
    Bound by M-T-MEM-PROMO-01 (allow-list entry #17): must carry
    `requested_threshold` and `actual_confidence` per ADR-1 lines 179–183.
    """

    requested_threshold: float
    actual_confidence: float


@dataclass(kw_only=True)
class PromotionRevocationFailed(TransientError):
    """Adapter could not revoke a promotion (upstream eventual-consistency).

    Per `port-contracts.md` v0.2 ADR-1 §3.4 PS-4 (line 221): raised
    during the conformance-asserted SLO window if revocation cannot be
    confirmed. Bound by M-T-MEM-PROMO-04 (allow-list entry #20): must
    carry `promotion_id` per ADR-1 lines 185–187.
    """

    promotion_id: str


# ---------------------------------------------------------------------------
# Protocol surface — verbatim per ADR-1 §3 lines 141–149
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryPort(Protocol):
    """Promotion-aware memory with substitute-ready dual-adapter contract.

    Per `port-contracts.md` v0.2 §1 ADR-9.1.2-1 design intent: the
    promotion semantic (PS-1..PS-4 at lines 211–221) is Verdaca-owned
    and non-delegable; adapters wrap Mem0 (primary) and Letta
    (substitute-readiness) per ADR-9.2-V1 dual-adapter pattern.
    Substitute-readiness clause at lines 241–243: Protocol MUST be
    implementable on top of either substrate without modification.

    Async / streaming / idempotency profile (ADR-1 lines 192–198):
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

    Substance gap (F-9.4.3-MEM-DTO-01 BLOCKS 9.4.3 sub-stage
    ratification; NON-BLOCKING for this step 1 file write per Path β
    disposition): 5 DTOs in method signatures (StoredMemory, MemoryQuery,
    PromotedMemory, RevokedPromotion, MigrationReport) ship as Path-β
    skeletons; full field specs deferred to ADR-1 corrigendum.
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
