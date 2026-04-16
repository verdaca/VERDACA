"""A/B harness report generator — produces JSON + Markdown savings reports."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .benchmark import ABComparison


def build_savings_report(comparisons: list[ABComparison]) -> dict[str, Any]:
    """Build a structured savings report from a list of A/B comparisons.

    This is the output that feeds the "Built With Praxis" dashboard.
    Architecture §6.2 — metrics captured per workload.
    """
    workload_reports = []
    total_bytes_saved = 0
    total_tokens_before = 0
    total_tokens_after = 0
    total_fallbacks = 0

    for cmp in comparisons:
        on = cmp.on_result
        off = cmp.off_result

        wl_report = {
            "workload": cmp.workload_name,
            "config_consistent": cmp.config_consistent,
            "config_hash": on.config_hash,
            "bytes_before": off.total_bytes_before,
            "bytes_after": on.total_bytes_after,
            "bytes_saved": on.savings_bytes,
            "savings_pct": round(on.savings_pct, 2),
            "tokens_before": off.total_tokens_before,
            "tokens_after": on.total_tokens_after,
            "token_reduction_pct": round(cmp.token_reduction_pct, 2),
            "fallback_count_on": on.fallback_count,
            "fallback_count_off": off.fallback_count,
            "layers_used": _aggregate_layers(on),
        }
        workload_reports.append(wl_report)

        total_bytes_saved += on.savings_bytes
        total_tokens_before += off.total_tokens_before
        total_tokens_after += on.total_tokens_after
        total_fallbacks += on.fallback_count

    compound_savings_pct = 0.0
    if total_tokens_before > 0:
        compound_savings_pct = round(
            100.0 * (total_tokens_before - total_tokens_after) / total_tokens_before, 2
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": (
            f"Three compression layers combined deliver "
            f"{compound_savings_pct}% total token reduction"
        ),
        "summary": {
            "total_bytes_saved": total_bytes_saved,
            "total_tokens_before": total_tokens_before,
            "total_tokens_after": total_tokens_after,
            "compound_token_reduction_pct": compound_savings_pct,
            "total_fallback_count": total_fallbacks,
            "workload_count": len(comparisons),
        },
        "workloads": workload_reports,
    }


def _aggregate_layers(result: object) -> list[str]:
    """Extract unique compression layers used across all requests in a result."""
    layers: set[str] = set()
    for req in result.request_results:  # type: ignore[union-attr]
        layers.update(req.layers_applied)
    layers.discard("none")
    return sorted(layers)


def write_report(
    report: dict[str, Any],
    output_path: Path,
    *,
    include_markdown: bool = True,
) -> None:
    """Write the savings report to *output_path* as JSON (and optionally Markdown)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if include_markdown:
        md_path = output_path.with_suffix(".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(_render_markdown(report))


def _render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Praxis Compression Layer — A/B Savings Report",
        "",
        f"**Generated:** {report['generated_at']}",
        "",
        f"## {report['headline']}",
        "",
        "### Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total bytes saved | {s['total_bytes_saved']:,} |",
        f"| Tokens before | {s['total_tokens_before']:,} |",
        f"| Tokens after | {s['total_tokens_after']:,} |",
        f"| **Compound token reduction** | **{s['compound_token_reduction_pct']}%** |",
        f"| Fallback count | {s['total_fallback_count']} |",
        f"| Workloads tested | {s['workload_count']} |",
        "",
        "### Per-Workload Results",
        "",
        "| Workload | Bytes saved | Token reduction | Layers | Fallbacks |",
        "|----------|-------------|-----------------|--------|-----------|",
    ]
    for wl in report["workloads"]:
        layers = ", ".join(wl["layers_used"]) or "none"
        lines.append(
            f"| {wl['workload']} | {wl['bytes_saved']:,} | {wl['token_reduction_pct']}% "
            f"| {layers} | {wl['fallback_count_on']} |"
        )
    lines.append("")
    return "\n".join(lines)
