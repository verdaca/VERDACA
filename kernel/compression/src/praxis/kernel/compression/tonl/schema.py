"""TONL schema inference — detect uniform array shape for table encoding."""
from __future__ import annotations

from typing import Any


def is_uniform_dict_array(lst: list[Any], *, min_rows: int = 2) -> bool:
    """Return True if *lst* is a non-empty list of dicts all sharing the same key set.

    Args:
        lst:      The list to test.
        min_rows: Minimum number of rows to bother encoding as a table.
                  Single-row tables offer no savings.
    """
    if len(lst) < min_rows:
        return False
    if not isinstance(lst[0], dict):
        return False
    keys = frozenset(lst[0].keys())
    if not keys:
        return False
    return all(isinstance(item, dict) and frozenset(item.keys()) == keys for item in lst[1:])


def infer_schema(lst: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Infer column names and value types from a uniform dict array.

    Returns:
        (col_names, col_types) — parallel lists.
        Types are simplified: 'str', 'int', 'bool', 'null', 'decimal', 'nested'.
    """
    cols = list(lst[0].keys())
    types: list[str] = []

    for col in cols:
        col_type = _infer_col_type([row[col] for row in lst])
        types.append(col_type)

    return cols, types


def _infer_col_type(values: list[Any]) -> str:
    non_null = [v for v in values if v is not None]
    if not non_null:
        return "null"
    sample = non_null[0]
    if isinstance(sample, bool):
        return "bool"
    if isinstance(sample, int):
        return "int"
    if isinstance(sample, str):
        return "str"
    # Decimal, dict, list → treat as nested/opaque
    from decimal import Decimal
    if isinstance(sample, Decimal):
        return "decimal"
    return "nested"
