"""Exception hierarchy for Pi-Mono."""
from __future__ import annotations


class CostTrackerError(Exception):
    """Base class for Pi-Mono errors."""


class UnknownModelError(CostTrackerError):
    """The requested (provider, model_id) is not in the pricing catalog."""


class PricingGapError(CostTrackerError):
    """No pricing row covers the request timestamp."""


class ProviderExtractionError(CostTrackerError):
    """A provider failed to parse its native response into an LLMResponse."""


class ReconciliationError(CostTrackerError):
    """An invoice cannot be matched against internal records."""


class StorageError(CostTrackerError):
    """A database operation failed."""
