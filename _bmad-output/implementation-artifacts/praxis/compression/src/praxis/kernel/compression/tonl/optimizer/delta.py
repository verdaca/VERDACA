"""Delta encoder — Strategy 2: numeric time-series compression.

P0 stub: deferred per 'no speculative code' rule (architecture §1.1.2 T-C6).
"""
from __future__ import annotations


class DeltaOptimizer:
    """Placeholder for delta-encoding numeric time-series.

    Not implemented in P0. Included to satisfy the optimizer registry.
    """

    def estimate_savings(self, _payload: object) -> dict[str, int]:
        return {"json_bytes": 0, "tonl_bytes": 0, "savings_bytes": 0}
