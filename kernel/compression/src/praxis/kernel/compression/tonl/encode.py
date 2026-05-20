"""TONL encoder — Python objects → TONL text.

Format specification
--------------------
Line 1:  ``TONL1``  (magic)
Line 2:  JSON body with table-reference strings ``@TONLT<n>`` and Decimal markers
         ``@TONLD<decimal>`` embedded as JSON string values.
Lines 3+: Zero or more table sections, each introduced by a header line:
         ``TABLE<n>:<count>:<col1>,<col2>,...``
         Followed by *count* data rows, each with ``|``-separated cell values.
         Cell escaping: ``|`` → ``\\|``, newline → ``\\n``, backslash → ``\\\\``.

Round-trip invariant: ``decode(encode(x)) == x`` for every Pydantic-serializable
Python value x (dict, list, str, int, bool, None, Decimal). Floats are rejected.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from .errors import TONLSecurityError, TONLTypeError, TONLValidationError
from .schema import is_uniform_dict_array
from .security import (
    MAX_NESTING_DEPTH,
    check_depth,
    check_fields_per_row,
    check_rows_per_table,
    check_size,
    check_string_len,
)

MAGIC = "TONL1"
_TABLE_REF_PREFIX = "@TONLT"
_DECIMAL_PREFIX = "@TONLD"
_ESCAPE_PREFIX = "@TONLE"   # escape for strings that start with the above prefixes
_FIELD_SEP = "|"
_ESCAPE_MAP = {"\\": "\\\\", "|": "\\|", "\n": "\\n"}


def _escape_cell(value: str) -> str:
    result = []
    for ch in value:
        result.append(_ESCAPE_MAP.get(ch, ch))
    return "".join(result)


def _encode_value(
    value: Any,
    tables: list[tuple[list[str], list[list[str]]]],
    depth: int,
) -> Any:
    """Recursively transform *value*, extracting uniform arrays into *tables*.

    Returns a JSON-serializable object (dict/list/str/int/bool/None) where
    uniform arrays have been replaced by ``"@TONLT<n>"`` sentinel strings.
    """
    check_depth(depth)

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise TONLValidationError(
            "float not allowed in TONL; use Decimal (str-encoded) or int"
        )
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return f"{_DECIMAL_PREFIX}{value}"
    if isinstance(value, str):
        check_string_len(value)
        # Escape strings that start with any TONL sentinel prefix to prevent collision
        if (
            value.startswith(_TABLE_REF_PREFIX)
            or value.startswith(_DECIMAL_PREFIX)
            or value.startswith(_ESCAPE_PREFIX)
        ):
            return f"{_ESCAPE_PREFIX}{value}"
        return value
    if isinstance(value, dict):
        return {k: _encode_value(v, tables, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if is_uniform_dict_array(value):
            return _extract_table(value, tables, depth)
        return [_encode_value(v, tables, depth + 1) for v in value]
    # Handle Pydantic models
    if hasattr(value, "model_dump"):
        return _encode_value(value.model_dump(), tables, depth)
    raise TONLTypeError(
        f"unsupported type {type(value).__name__!r}; "
        "add a model_dump() method or convert to a supported type first"
    )


def _extract_table(
    lst: list[dict[str, Any]],
    tables: list[tuple[list[str], list[list[str]]]],
    depth: int,
) -> str:
    """Extract a uniform dict array into the table registry; return a sentinel string."""
    cols = list(lst[0].keys())
    check_fields_per_row(len(cols))
    check_rows_per_table(len(lst))

    rows: list[list[str]] = []
    for item in lst:
        row: list[str] = []
        for col in cols:
            cell = _encode_value(item[col], tables, depth + 1)
            # Cells must be scalars (strings, ints, bools, None after encoding)
            cell_str = json.dumps(cell, ensure_ascii=False)
            row.append(_escape_cell(cell_str))
        rows.append(row)

    table_idx = len(tables)
    tables.append((cols, rows))
    return f"{_TABLE_REF_PREFIX}{table_idx}"


def encode(payload: Any, *, tokenizer: str | None = None) -> str:
    """Encode *payload* to TONL text.

    Args:
        payload:   Any JSON-serializable Python value (Decimal supported; float rejected).
        tokenizer: Tokenizer name for future alignment optimizations (unused in P0).

    Returns:
        TONL-encoded string.

    Raises:
        TONLValidationError: if float values are present in cost-tracking context.
        TONLTypeError:       if an unsupported Python type is encountered.
        TONLSecurityError:   if size or depth limits are exceeded.
    """
    tables: list[tuple[list[str], list[list[str]]]] = []
    transformed = _encode_value(payload, tables, depth=0)

    json_body = json.dumps(transformed, ensure_ascii=False, separators=(",", ":"))
    check_size(json_body)

    parts = [MAGIC, json_body]

    for i, (cols, rows) in enumerate(tables):
        header = f"TABLE{i}:{len(rows)}:{','.join(cols)}"
        parts.append(header)
        for row in rows:
            parts.append(_FIELD_SEP.join(row))

    return "\n".join(parts) + "\n"
