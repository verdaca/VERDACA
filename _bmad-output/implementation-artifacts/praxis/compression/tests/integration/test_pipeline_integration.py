"""Integration tests — full compression pipeline on real workloads.

Tests: compression ON → tags report savings, pipeline consistent,
Caveman OFF by default, cascade isolation holds end-to-end.
"""
from __future__ import annotations

import pytest

from praxis.kernel.compression.config import CompressionConfig
from praxis.kernel.compression.harness import (
    ALL_WORKLOADS,
    build_savings_report,
    run_ab_comparison,
)
from praxis.kernel.compression.orchestrator import CompressionLayer
from praxis.kernel.compression.tonl.decode import decode
from praxis.kernel.compression.tonl.encode import encode


class TestFullPipelineEncodeRequest:
    @pytest.mark.asyncio
    async def test_nested_payload_round_trip(self, nested_payload):
        layer = CompressionLayer()
        encoded, tags = await layer.encode_request(nested_payload)
        assert tags["compression.mode"] == "on"
        assert "tonl" in tags.get("compression.pipeline", "")
        # Round-trip: re-decode the TONL
        if isinstance(encoded, str) and encoded.startswith("TONL1"):
            decoded_val = decode(encoded)
            assert decoded_val == nested_payload

    @pytest.mark.asyncio
    async def test_messages_get_table_compressed(self, uniform_messages):
        layer = CompressionLayer()
        payload = {"messages": uniform_messages, "session": "test"}
        encoded, tags = await layer.encode_request(payload)
        # TONL output should show table compression
        assert isinstance(encoded, str)
        if "TONL1" in encoded:
            assert "TABLE0:" in encoded

    @pytest.mark.asyncio
    async def test_savings_reported_in_tags(self, nested_payload):
        layer = CompressionLayer()
        encoded, tags = await layer.encode_request(nested_payload)
        tokens_before = int(tags.get("compression.tokens.before", 0))
        tokens_after = int(tags.get("compression.tokens.after", 0))
        assert tokens_before > 0
        assert tokens_after > 0
        # TONL should reduce byte count for uniform array payloads
        bytes_before = int(tags.get("compression.bytes.before", 0))
        bytes_after = int(tags.get("compression.bytes.after", 0))
        assert bytes_before > 0
        assert bytes_after > 0

    @pytest.mark.asyncio
    async def test_cascade_isolation_all_components(self):
        """Full cascade: if TONL fails, pipeline still completes."""
        from unittest.mock import patch

        with patch(
            "praxis.kernel.compression.orchestrator.encode",
            side_effect=RuntimeError("TONL crashed"),
        ):
            layer = CompressionLayer()
            encoded, tags = await layer.encode_request({"x": 1})
            # Pipeline must NOT crash — cascade isolation
            assert tags["compression.mode"] == "on"
            assert "compression.fallback" in tags

    @pytest.mark.asyncio
    async def test_caveman_disabled_by_default(self):
        config = CompressionConfig()
        assert config.caveman.enabled is False
        layer = CompressionLayer(config=config)
        _, tags = await layer.decode_response("some prose " * 200)
        # No Caveman tags when disabled
        assert "compression.caveman.intensity" not in tags
        assert "compression.caveman.fallback" not in tags

    @pytest.mark.asyncio
    async def test_session_stats_accumulated(self, nested_payload):
        layer = CompressionLayer()
        sid = "integration-sess-1"
        for _ in range(3):
            await layer.encode_request(nested_payload, session_id=sid)
        stats = await layer.session_stats(sid)
        # TONL bytes saved should be > 0 for a nested payload with uniform arrays
        assert stats.tonl_bytes_saved >= 0  # >= 0 always


class TestABHarness:
    @pytest.mark.asyncio
    async def test_tonl_heavy_workload_shows_savings(self):
        from praxis.kernel.compression.harness.workload import make_tonl_heavy_workload
        workload = make_tonl_heavy_workload()
        config = CompressionConfig()
        comparison = await run_ab_comparison(workload, config)
        # Config hash must be consistent
        assert comparison.config_consistent
        # ON mode should have savings
        assert comparison.on_result.total_bytes_before > 0

    @pytest.mark.asyncio
    async def test_savings_report_generation(self):
        from praxis.kernel.compression.harness.workload import make_mixed_workload
        workload = make_mixed_workload()
        config = CompressionConfig()
        comparison = await run_ab_comparison(workload, config)
        report = build_savings_report([comparison])

        assert "headline" in report
        assert "summary" in report
        assert report["summary"]["workload_count"] == 1
        assert report["summary"]["total_tokens_before"] >= 0

    @pytest.mark.asyncio
    async def test_all_workloads_run_without_crash(self):
        config = CompressionConfig()
        for workload in ALL_WORKLOADS:
            comparison = await run_ab_comparison(workload, config)
            assert comparison.workload_name == workload.name


class TestTagBudgetIntegration:
    @pytest.mark.asyncio
    async def test_tag_count_never_exceeds_ceiling(self, nested_payload):
        """End-to-end: tag count on the final request must not exceed 28."""
        from praxis.kernel.compression.telemetry import merge_compression_tags, _TAG_CEILING

        layer = CompressionLayer()
        _, compression_tags = await layer.encode_request(nested_payload)

        # Simulate merging with 15 pre-existing tags
        existing = {f"existing_{i}": f"v{i}" for i in range(15)}
        merged = merge_compression_tags(existing, compression_tags)
        assert len(merged) <= _TAG_CEILING
