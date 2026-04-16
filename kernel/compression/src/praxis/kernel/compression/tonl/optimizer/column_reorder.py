"""Column reorder optimizer — Strategy 3: query-optimised column layout.

P0 stub: deferred per 'no speculative code' rule (architecture §1.1.2 T-C6).
"""
from __future__ import annotations


class ColumnReorderOptimizer:
    """Placeholder for column-reordering optimisation.

    Not implemented in P0. Included to satisfy the optimizer registry.
    """

    def estimate_savings(self, _payload: object) -> dict[str, int]:
        return {"json_bytes": 0, "tonl_bytes": 0, "savings_bytes": 0}
