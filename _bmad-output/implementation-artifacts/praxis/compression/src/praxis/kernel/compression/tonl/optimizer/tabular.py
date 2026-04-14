"""Tabular optimizer — Strategy 1: uniform arrays to table blocks.

This is the primary savings mechanism. The encode.py already applies this
transformation by default. This class provides a metrics API for the A/B harness.
"""
from __future__ import annotations

import json
from typing import Any

from ..schema import is_uniform_dict_array


class TabularOptimizer:
    """Measures and reports savings from tabular compression."""

    def estimate_savings(self, payload: Any) -> dict[str, int]:
        """Return estimated byte savings from applying tabular encoding to *payload*.

        Args:
            payload: Any JSON-serializable Python value.

        Returns:
            ``{"json_bytes": N, "tonl_bytes": M, "savings_bytes": S}``
        """
        json_bytes = len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        tonl_bytes = self._estimate_tonl_size(payload)
        savings = max(0, json_bytes - tonl_bytes)
        return {
            "json_bytes": json_bytes,
            "tonl_bytes": tonl_bytes,
            "savings_bytes": savings,
        }

    def _estimate_tonl_size(self, value: Any) -> int:
        if isinstance(value, list) and is_uniform_dict_array(value):
            cols = list(value[0].keys())
            header = f"TABLE0:{len(value)}:{','.join(cols)}\n"
            rows_size = sum(
                len("|".join(json.dumps(row[c], separators=(",", ":")) for c in cols)) + 1
                for row in value
            )
            return len(header.encode("utf-8")) + rows_size
        elif isinstance(value, dict):
            return sum(
                len(k) + 1 + self._estimate_tonl_size(v)
                for k, v in value.items()
            )
        elif isinstance(value, list):
            return sum(self._estimate_tonl_size(item) for item in value)
        else:
            return len(json.dumps(value, separators=(",", ":")))
