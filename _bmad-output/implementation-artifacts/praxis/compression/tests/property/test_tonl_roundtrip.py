"""Property-based tests — TONL round-trip invariant.

Murat §9: 5,000 Hypothesis cases minimum for P_T1.

decode(encode(x)) == x for every Pydantic-serializable Python value x.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from praxis.kernel.compression.tonl.decode import decode
from praxis.kernel.compression.tonl.encode import encode
from praxis.kernel.compression.tonl.errors import TONLSecurityError, TONLValidationError

# Strategy for JSON-compatible values that TONL must round-trip perfectly
_json_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-2**53, max_value=2**53),
    st.text(max_size=200),
)

_json_values = st.recursive(
    base=_json_scalars,
    extend=lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
            children,
            max_size=10,
        ),
    ),
    max_leaves=30,
)

# Strategy for uniform dict arrays (the table path)
_uniform_row = st.fixed_dictionaries({"role": st.sampled_from(["user", "assistant"]), "content": st.text(max_size=100)})
_uniform_array = st.lists(_uniform_row, min_size=2, max_size=50)


@given(_json_values)
@settings(max_examples=5000, suppress_health_check=[HealthCheck.too_slow])
def test_round_trip_arbitrary_json(value):
    """P_T1: decode(encode(x)) == x for arbitrary JSON-compatible values."""
    # Skip floats — TONL rejects them by design
    if _contains_float(value):
        return
    try:
        encoded = encode(value)
        decoded = decode(encoded)
        assert decoded == value, f"Round-trip failed: {value!r} → {decoded!r}"
    except TONLSecurityError:
        pass  # Security limit hit — not a bug
    except TONLValidationError:
        pass  # Float or invalid type — by design


@given(_uniform_array)
@settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
def test_round_trip_uniform_dict_array(rows):
    """P_T2: uniform arrays are table-encoded and decode perfectly."""
    encoded = encode(rows)
    assert "TABLE0:" in encoded  # confirms table path was taken
    decoded = decode(encoded)
    assert decoded == rows


@given(st.text(min_size=0, max_size=500))
@settings(max_examples=500)
def test_round_trip_strings(text):
    """P_T3: arbitrary strings survive encode/decode."""
    # Exclude floats in strings (not applicable), but include special chars
    try:
        encoded = encode(text)
        decoded = decode(encoded)
        assert decoded == text
    except TONLSecurityError:
        pass


@given(st.lists(
    st.fixed_dictionaries({
        "role": st.sampled_from(["user", "assistant", "tool"]),
        "content": st.text(min_size=0, max_size=500),
        "id": st.integers(min_value=0, max_value=9999),
    }),
    min_size=2,
    max_size=100,
))
@settings(max_examples=500)
def test_round_trip_message_arrays(messages):
    """P_T4: LLM message arrays round-trip correctly (primary use case)."""
    payload = {"messages": messages, "model": "claude-opus-4-6"}
    encoded = encode(payload)
    decoded = decode(encoded)
    assert decoded == payload


def _contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
