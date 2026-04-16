"""Unit tests — harness/report.py: build_savings_report, write_report, _render_markdown.

Covers:
- build_savings_report with empty comparisons
- build_savings_report with one comparison
- build_savings_report compound savings pct calculation
- build_savings_report with zero tokens before (edge case)
- _aggregate_layers extracts unique layer names, discards "none"
- write_report writes JSON file
- write_report writes Markdown file when include_markdown=True
- write_report skips Markdown when include_markdown=False
- _render_markdown headline matches compound savings
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praxis.kernel.compression.harness.benchmark import (
    ABComparison,
    WorkloadRunResult,
    RequestResult,
)
from praxis.kernel.compression.harness.report import (
    build_savings_report,
    write_report,
    _aggregate_layers,
    _render_markdown,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request_result(bytes_before=1000, bytes_after=300, tokens_before=250,
                          tokens_after=75, layers=None, fallback=None):
    return RequestResult(
        description="test request",
        bytes_before=bytes_before,
        bytes_after=bytes_after,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        layers_applied=["tonl", "forge"] if layers is None else layers,
        fallback=fallback,
    )


def _make_workload_result(name="workload-1", mode="on", config_hash="abc123",
                          requests=None):
    result = WorkloadRunResult(
        workload_name=name,
        mode=mode,
        config_hash=config_hash,
        request_results=requests or [_make_request_result()],
    )
    return result


def _make_comparison(name="workload-1", on_requests=None, off_requests=None,
                     config_hash="abc123"):
    on_result = _make_workload_result(
        name=name, mode="on", config_hash=config_hash,
        requests=on_requests or [_make_request_result(bytes_before=1000, bytes_after=300,
                                                       tokens_before=250, tokens_after=75)]
    )
    off_result = _make_workload_result(
        name=name, mode="off", config_hash=config_hash,
        requests=off_requests or [_make_request_result(bytes_before=1000, bytes_after=1000,
                                                        tokens_before=250, tokens_after=250,
                                                        layers=["none"])]
    )
    return ABComparison(workload_name=name, on_result=on_result, off_result=off_result)


# ---------------------------------------------------------------------------
# build_savings_report
# ---------------------------------------------------------------------------

class TestBuildSavingsReport:
    def test_empty_comparisons(self):
        report = build_savings_report([])
        assert report["summary"]["workload_count"] == 0
        assert report["summary"]["total_bytes_saved"] == 0
        assert report["summary"]["compound_token_reduction_pct"] == 0.0
        assert report["workloads"] == []

    def test_single_comparison_structure(self):
        cmp = _make_comparison()
        report = build_savings_report([cmp])
        assert len(report["workloads"]) == 1
        wl = report["workloads"][0]
        assert wl["workload"] == "workload-1"
        assert "bytes_saved" in wl
        assert "savings_pct" in wl
        assert "token_reduction_pct" in wl
        assert "layers_used" in wl

    def test_compound_savings_calculation(self):
        # OFF: 250 tokens before, ON: 75 tokens after → 70% reduction
        cmp = _make_comparison()
        report = build_savings_report([cmp])
        s = report["summary"]
        assert s["total_tokens_before"] == 250
        assert s["total_tokens_after"] == 75
        assert s["compound_token_reduction_pct"] == 70.0

    def test_zero_tokens_before_returns_zero_pct(self):
        on_req = _make_request_result(tokens_before=0, tokens_after=0)
        off_req = _make_request_result(bytes_before=0, bytes_after=0,
                                        tokens_before=0, tokens_after=0, layers=["none"])
        cmp = _make_comparison(on_requests=[on_req], off_requests=[off_req])
        report = build_savings_report([cmp])
        assert report["summary"]["compound_token_reduction_pct"] == 0.0

    def test_multiple_comparisons_aggregated(self):
        cmp1 = _make_comparison("w1")
        cmp2 = _make_comparison("w2",
                                  on_requests=[_make_request_result(tokens_before=100,
                                                                     tokens_after=50)],
                                  off_requests=[_make_request_result(tokens_before=100,
                                                                      tokens_after=100,
                                                                      layers=["none"])])
        report = build_savings_report([cmp1, cmp2])
        assert len(report["workloads"]) == 2
        assert report["summary"]["workload_count"] == 2

    def test_headline_includes_reduction_pct(self):
        cmp = _make_comparison()
        report = build_savings_report([cmp])
        assert "%" in report["headline"]
        assert "compression" in report["headline"].lower()

    def test_generated_at_is_iso(self):
        from datetime import datetime
        report = build_savings_report([])
        # Should parse without error
        datetime.fromisoformat(report["generated_at"])

    def test_config_consistent_flag(self):
        cmp = _make_comparison(config_hash="hash1")
        report = build_savings_report([cmp])
        assert report["workloads"][0]["config_consistent"] is True

    def test_fallback_count_aggregated(self):
        on_req = _make_request_result(fallback="expansion")
        cmp = _make_comparison(on_requests=[on_req])
        report = build_savings_report([cmp])
        assert report["workloads"][0]["fallback_count_on"] == 1


# ---------------------------------------------------------------------------
# _aggregate_layers
# ---------------------------------------------------------------------------

class TestAggregateLayersHelper:
    def test_extracts_unique_layers(self):
        result = _make_workload_result(requests=[
            _make_request_result(layers=["tonl", "forge"]),
            _make_request_result(layers=["forge", "caveman"]),
        ])
        layers = _aggregate_layers(result)
        assert "tonl" in layers
        assert "forge" in layers
        assert "caveman" in layers
        assert len(layers) == len(set(layers))  # unique

    def test_none_layer_discarded(self):
        result = _make_workload_result(requests=[
            _make_request_result(layers=["none"]),
        ])
        layers = _aggregate_layers(result)
        assert "none" not in layers

    def test_sorted_output(self):
        result = _make_workload_result(requests=[
            _make_request_result(layers=["zzz", "aaa", "mmm"]),
        ])
        layers = _aggregate_layers(result)
        assert layers == sorted(layers)

    def test_empty_layers(self):
        result = _make_workload_result(requests=[
            _make_request_result(layers=["none"]),
            _make_request_result(layers=[]),
        ])
        layers = _aggregate_layers(result)
        assert layers == []


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------

class TestWriteReport:
    def test_writes_json(self, tmp_path):
        report = build_savings_report([_make_comparison()])
        output_path = tmp_path / "report.json"
        write_report(report, output_path, include_markdown=False)
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "summary" in data

    def test_writes_markdown_by_default(self, tmp_path):
        report = build_savings_report([_make_comparison()])
        output_path = tmp_path / "report.json"
        write_report(report, output_path)
        md_path = tmp_path / "report.md"
        assert md_path.exists()
        content = md_path.read_text()
        assert "Praxis Compression" in content

    def test_skips_markdown_when_disabled(self, tmp_path):
        report = build_savings_report([_make_comparison()])
        output_path = tmp_path / "report.json"
        write_report(report, output_path, include_markdown=False)
        md_path = tmp_path / "report.md"
        assert not md_path.exists()

    def test_creates_parent_dirs(self, tmp_path):
        report = build_savings_report([])
        deep_path = tmp_path / "a" / "b" / "c" / "report.json"
        write_report(report, deep_path, include_markdown=False)
        assert deep_path.exists()


# ---------------------------------------------------------------------------
# _render_markdown
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_contains_headline(self):
        report = build_savings_report([_make_comparison()])
        md = _render_markdown(report)
        assert report["headline"] in md

    def test_contains_workload_table(self):
        report = build_savings_report([_make_comparison("test-wl")])
        md = _render_markdown(report)
        assert "test-wl" in md

    def test_contains_summary_metrics(self):
        report = build_savings_report([_make_comparison()])
        md = _render_markdown(report)
        assert "Total bytes saved" in md
        assert "Tokens before" in md

    def test_empty_comparisons_renders_clean(self):
        report = build_savings_report([])
        md = _render_markdown(report)
        assert "0%" in md or "0.0%" in md
        assert "Praxis" in md
