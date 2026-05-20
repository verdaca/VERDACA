"""Praxis Memory — public facade and model surface.

Application code imports from this module and nothing else. The
`Memory` class is the composed facade; every value type the caller
constructs or destructures is re-exported from `praxis.kernel.memory.models`.

NR-S-R1: imports from `praxis.kernel.memory._internal.*` are forbidden
for application code (ruff TID251 + grep tripwire). The Memory module
itself is exempt via per-file-ignores — this file and `facade.py` both
reach into `_internal` to wire up backends, but that is the ONLY legal
use of `_internal`.
"""

from praxis.kernel.memory.deployment.manifest import DeploymentManifest
from praxis.kernel.memory.facade import Memory
from praxis.kernel.memory.models import (
    BackendHealth,
    DecisionDraft,
    DecisionRecord,
    DeleteCriteria,
    DeleteResult,
    DeleteSubstepStatus,
    DissentRecord,
    EvidenceItem,
    ExportCriteria,
    ExportResult,
    FactDraft,
    FactRecord,
    HealthReport,
    HealthStatus,
    MemoryBackendError,
    MemoryQuotaExceeded,
    MemoryRecordNotFound,
    OutcomeStatus,
    QuarantineReason,
    QuarantineResult,
    ReasoningStep,
    RecordType,
    RetrievalHit,
    RetrievalResult,
    SourceDistribution,
    TaskOutcomeDraft,
    TaskOutcomeRecord,
    TaskSignature,
    TenantIdentityError,
)
from praxis.kernel.memory.telemetry import TelemetryEvent

__all__ = [
    "BackendHealth",
    "DecisionDraft",
    "DecisionRecord",
    "DeleteCriteria",
    "DeleteResult",
    "DeleteSubstepStatus",
    "DeploymentManifest",
    "DissentRecord",
    "EvidenceItem",
    "ExportCriteria",
    "ExportResult",
    "FactDraft",
    "FactRecord",
    "HealthReport",
    "HealthStatus",
    "Memory",
    "MemoryBackendError",
    "MemoryQuotaExceeded",
    "MemoryRecordNotFound",
    "OutcomeStatus",
    "QuarantineReason",
    "QuarantineResult",
    "ReasoningStep",
    "RecordType",
    "RetrievalHit",
    "RetrievalResult",
    "SourceDistribution",
    "TaskOutcomeDraft",
    "TaskOutcomeRecord",
    "TaskSignature",
    "TelemetryEvent",
    "TenantIdentityError",
]
