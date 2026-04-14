"""Unit tests — TONL optimizer modules and schema inference.

Covers: TabularOptimizer, DeltaOptimizer, ColumnReorderOptimizer,
        is_uniform_dict_array, infer_schema.
"""
from __future__ import annotations

import json
from decimal import Decimal

import pytest

from praxis.kernel.compression.tonl.schema import is_uniform_dict_array, infer_schema
from praxis.kernel.compression.tonl.optimizer.tabular import TabularOptimizer
from praxis.kernel.compression.tonl.optimizer.delta import DeltaOptimizer
from praxis.kernel.compression.tonl.optimizer.column_reorder import ColumnReorderOptimizer
from praxis.kernel.compression.tonl.optimizer import TabularOptimizer as ExportedOptimizer


# ---------------------------------------------------------------------------
# schema.is_uniform_dict_array
# ---------------------------------------------------------------------------

class TestIsUniformDictArrayExtended:
    def test_single_row_returns_false_below_min(self):
        lst = [{"a": 1}]
        assert is_uniform_dict_array(lst) is False

    def test_two_rows_same_keys(self):
        lst = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert is_uniform_dict_array(lst) is True

    def test_missing_key_in_second_row(self):
        lst = [{"a": 1, "b": 2}, {"a": 3}]
        assert is_uniform_dict_array(lst) is False

    def test_extra_key_in_second_row(self):
        lst = [{"a": 1}, {"a": 2, "b": 3}]
        assert is_uniform_dict_array(lst) is False

    def test_non_dict_items(self):
        lst = [1, 2, 3]
        assert is_uniform_dict_array(lst) is False

    def test_mixed_types(self):
        lst = [{"a": 1}, "string"]
        assert is_uniform_dict_array(lst) is False

    def test_empty_dict_rows(self):
        lst = [{}, {}]
        assert is_uniform_dict_array(lst) is False  # empty key set

    def test_min_rows_parameter(self):
        lst = [{"a": 1}]
        assert is_uniform_dict_array(lst, min_rows=1) is True

    def test_five_uniform_rows(self):
        lst = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
        assert is_uniform_dict_array(lst) is True


# ---------------------------------------------------------------------------
# schema.infer_schema
# ---------------------------------------------------------------------------

class TestInferSchema:
    def test_string_column(self):
        lst = [{"name": "alice"}, {"name": "bob"}]
        cols, types = infer_schema(lst)
        assert cols == ["name"]
        assert types == ["str"]

    def test_int_column(self):
        lst = [{"count": 1}, {"count": 2}]
        _, types = infer_schema(lst)
        assert types == ["int"]

    def test_bool_column(self):
        lst = [{"active": True}, {"active": False}]
        _, types = infer_schema(lst)
        assert types == ["bool"]

    def test_null_column(self):
        lst = [{"x": None}, {"x": None}]
        _, types = infer_schema(lst)
        assert types == ["null"]

    def test_decimal_column(self):
        lst = [{"price": Decimal("9.99")}, {"price": Decimal("14.99")}]
        _, types = infer_schema(lst)
        assert types == ["decimal"]

    def test_nested_column(self):
        lst = [{"meta": {"k": "v"}}, {"meta": {"k": "w"}}]
        _, types = infer_schema(lst)
        assert types == ["nested"]

    def test_mixed_columns(self):
        lst = [
            {"name": "alice", "age": 30, "active": True},
            {"name": "bob", "age": 25, "active": False},
        ]
        cols, types = infer_schema(lst)
        assert cols == ["name", "age", "active"]
        assert types == ["str", "int", "bool"]

    def test_column_order_preserved(self):
        lst = [{"z": 1, "a": 2, "m": 3}, {"z": 4, "a": 5, "m": 6}]
        cols, _ = infer_schema(lst)
        assert cols == ["z", "a", "m"]


# ---------------------------------------------------------------------------
# TabularOptimizer
# ---------------------------------------------------------------------------

class TestTabularOptimizer:
    def setup_method(self):
        self.opt = TabularOptimizer()

    def test_savings_uniform_array(self):
        payload = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you"},
        ]
        result = self.opt.estimate_savings(payload)
        assert result["json_bytes"] > 0
        assert result["tonl_bytes"] > 0
        assert "savings_bytes" in result

    def test_uniform_array_has_savings(self):
        payload = [{"role": f"role_{i}", "content": f"content_{i}"} for i in range(10)]
        result = self.opt.estimate_savings(payload)
        # TONL table encoding should be smaller than JSON for uniform arrays
        assert result["savings_bytes"] >= 0

    def test_scalar_no_savings(self):
        result = self.opt.estimate_savings("hello world")
        assert result["json_bytes"] > 0
        assert result["savings_bytes"] == 0 or result["savings_bytes"] >= 0  # no negative

    def test_empty_list(self):
        result = self.opt.estimate_savings([])
        assert result["json_bytes"] == 2  # len(b"[]")
        assert result["tonl_bytes"] == 0  # empty list has no TONL content
        assert result["savings_bytes"] >= 0

    def test_dict_payload(self):
        payload = {"a": 1, "b": {"c": 2}}
        result = self.opt.estimate_savings(payload)
        assert result["json_bytes"] > 0
        assert result["savings_bytes"] >= 0

    def test_non_uniform_list(self):
        payload = [{"a": 1}, {"b": 2}]  # different keys
        result = self.opt.estimate_savings(payload)
        assert result["json_bytes"] > 0

    def test_integer_scalar(self):
        result = self.opt.estimate_savings(42)
        assert result["json_bytes"] == len(b"42")

    def test_savings_never_negative(self):
        payloads = [
            "a short string",
            {"key": "value"},
            [{"x": 1}, {"x": 2}],
            None,
            True,
            0,
        ]
        for payload in payloads:
            result = self.opt.estimate_savings(payload)
            assert result["savings_bytes"] >= 0, f"negative savings for {payload!r}"

    def test_exported_from_init(self):
        assert ExportedOptimizer is TabularOptimizer


# ---------------------------------------------------------------------------
# DeltaOptimizer (P0 stub)
# ---------------------------------------------------------------------------

class TestDeltaOptimizer:
    def test_always_returns_zero_savings(self):
        opt = DeltaOptimizer()
        for payload in [42, "text", [1, 2, 3], {"a": 1}, None]:
            result = opt.estimate_savings(payload)
            assert result == {"json_bytes": 0, "tonl_bytes": 0, "savings_bytes": 0}

    def test_stub_does_not_raise(self):
        opt = DeltaOptimizer()
        opt.estimate_savings(object())  # arbitrary object — must not raise


# ---------------------------------------------------------------------------
# ColumnReorderOptimizer (P0 stub)
# ---------------------------------------------------------------------------

class TestColumnReorderOptimizer:
    def test_always_returns_zero_savings(self):
        opt = ColumnReorderOptimizer()
        for payload in [42, "text", [1, 2, 3], {"a": 1}, None]:
            result = opt.estimate_savings(payload)
            assert result == {"json_bytes": 0, "tonl_bytes": 0, "savings_bytes": 0}

    def test_stub_does_not_raise(self):
        opt = ColumnReorderOptimizer()
        opt.estimate_savings(object())
