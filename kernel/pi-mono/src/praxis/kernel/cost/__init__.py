"""Pi-Mono — Praxis cost tracker (Stage 1, measurement foundation).

Public API re-exports. Code outside `praxis.kernel.cost` imports from here only.
"""
from .errors import (
    CostTrackerError,
    PricingGapError,
    ProviderExtractionError,
    ReconciliationError,
    StorageError,
    UnknownModelError,
)
from .math import QUANTUM, QUANTUM_PLACES, compute_cost
from .models import (
    AggregationScope,
    CacheRetention,
    CostAmount,
    CostEvent,
    CostRecord,
    CostSummary,
    Currency,
    Filter,
    Invoice,
    InvoiceLine,
    LLMRequest,
    LLMResponse,
    ModelPricing,
    ProviderName,
    ReconciliationDrift,
    ReconciliationReport,
    TimeRange,
    TokenClass,
)
from .tracker import CostTracker

__all__ = [
    "CostTracker",
    "compute_cost",
    "QUANTUM",
    "QUANTUM_PLACES",
    "CostTrackerError",
    "UnknownModelError",
    "PricingGapError",
    "ProviderExtractionError",
    "ReconciliationError",
    "StorageError",
    "AggregationScope",
    "CacheRetention",
    "CostAmount",
    "CostEvent",
    "CostRecord",
    "CostSummary",
    "Currency",
    "Filter",
    "Invoice",
    "InvoiceLine",
    "LLMRequest",
    "LLMResponse",
    "ModelPricing",
    "ProviderName",
    "ReconciliationDrift",
    "ReconciliationReport",
    "TimeRange",
    "TokenClass",
]
