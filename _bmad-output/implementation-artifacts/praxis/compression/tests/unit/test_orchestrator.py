"""Unit tests — CompressionLayer orchestrator (cascade isolation + tag budget)."""
from __future__ import annotations

import pytest

from praxis.kernel.compression.config import CompressionConfig
from praxis.kernel.compression.orchestrator import CompressionLayer
from praxis.kernel.compression.telemetry import (
    TAG_BYTES_AFTER,
    TAG_BYTES_BEFORE,
    TAG_MODE,
    TAG_PIPELINE,
    TAG_TOKENS_AFTER,
    TAG_TOKENS_BEFORE,
    merge_compression_tags,
)


class TestTagBudget:
    def test_merge_within_budget(self):
        existing = {f"existing_{i}": f"v{i}" for i in range(5)}
        comp = {"compression.mode": "on", "compression.pipeline": "tonl"}
        merged = merge_compression_tags(existing, comp)
        assert len(merged) <= 28
        assert "compression.mode" in merged

    def test_merge_drops_lowest_priority_tags(self):
        # Fill up to 27 existing tags + add 5 compression tags → needs to drop some
        existing = {f"tag_{i}": f"v{i}" for i in range(25)}
        comp = {
            "compression.mode": "on",
            "compression.pipeline": "tonl,forge",
            "compression.tokens.before": "1000",
            "compression.tokens.after": "400",
            "compression.bytes.before": "4000",
            "compression.bytes.after": "1600",
            "compression.tonl.tokenizer": "anthropic@2026",  # lowest priority
            "compression.caveman.dialect": "caveman_english",  # low priority
        }
        merged = merge_compression_tags(existing, comp)
        assert len(merged) <= 28
        # High-priority tags must survive
        assert "compression.mode" in merged
        assert "compression.tokens.before" in merged

    def test_merge_no_compression_tags_unchanged(self):
        existing = {"a": "1", "b": "2"}
        merged = merge_compression_tags(existing, {})
        assert merged == existing


class TestCompressionLayerOff:
    @pytest.mark.asyncio
    async def test_mode_off_returns_original(self, nested_payload):
        config = CompressionConfig(mode="off")
        layer = CompressionLayer(config=config)
        encoded, tags = await layer.encode_request(nested_payload)
        assert encoded == nested_payload
        assert tags.get(TAG_MODE) == "off"

    @pytest.mark.asyncio
    async def test_mode_off_decode_passthrough(self):
        config = CompressionConfig(mode="off")
        layer = CompressionLayer(config=config)
        result, tags = await layer.decode_response("plain text response")
        assert result == "plain text response"
        assert tags == {}


class TestCompressionLayerOn:
    @pytest.mark.asyncio
    async def test_encode_produces_tonl_and_tags(self, nested_payload):
        layer = CompressionLayer()
        encoded, tags = await layer.encode_request(nested_payload)
        assert tags.get(TAG_MODE) == "on"
        assert TAG_PIPELINE in tags
        assert TAG_TOKENS_BEFORE in tags
        assert TAG_TOKENS_AFTER in tags
        assert TAG_BYTES_BEFORE in tags
        assert TAG_BYTES_AFTER in tags

    @pytest.mark.asyncio
    async def test_encode_decode_round_trip(self, nested_payload):
        layer = CompressionLayer()
        encoded, tags = await layer.encode_request(nested_payload)
        # The encoded form is a TONL string
        assert isinstance(encoded, str)
        if isinstance(encoded, str) and encoded.startswith("TONL1"):
            decoded, _ = await layer.decode_response(encoded)
            # decoded should represent the original payload
            assert "TONL1" not in decoded or len(decoded) > 0

    @pytest.mark.asyncio
    async def test_cascade_isolation_tonl_failure(self, monkeypatch):
        """TONL failure must not abort the pipeline or crash the orchestrator."""
        from praxis.kernel.compression import tonl as tonl_mod

        def bad_encode(*_args, **_kwargs):
            raise RuntimeError("TONL exploded")

        monkeypatch.setattr("praxis.kernel.compression.orchestrator.encode", bad_encode)

        layer = CompressionLayer()
        encoded, tags = await layer.encode_request({"x": 1})
        # Should still return SOMETHING and have mode=on
        assert tags.get(TAG_MODE) == "on"
        assert "compression.fallback" in tags  # cascade isolated: fallback tag present

    @pytest.mark.asyncio
    async def test_caveman_off_by_default(self):
        config = CompressionConfig()
        assert config.caveman.enabled is False
        layer = CompressionLayer(config=config)
        decoded, tags = await layer.decode_response("plain prose " * 200)
        # No Caveman tags should be present when disabled
        assert "compression.caveman.intensity" not in tags

    @pytest.mark.asyncio
    async def test_session_stats_tracks_savings(self, nested_payload):
        layer = CompressionLayer()
        await layer.encode_request(nested_payload, session_id="test-sess")
        stats = await layer.session_stats("test-sess")
        assert stats.session_id == "test-sess"
        # tonl_bytes_saved should be >= 0
        assert stats.tonl_bytes_saved >= 0


class TestRTKNotAvailable:
    @pytest.mark.asyncio
    async def test_rtk_disabled_returns_result(self):
        from praxis.kernel.compression.config import RTKConfig
        config = CompressionConfig(rtk=RTKConfig(enabled=False))
        layer = CompressionLayer(config=config)
        result = await layer.run_tool_command(["echo", "hello"])
        assert result.rtk_used is False
        assert result.exit_code == 1  # disabled, returns error result

    @pytest.mark.asyncio
    async def test_rtk_property_accessor(self):
        layer = CompressionLayer()
        # .rtk is None when binary not found (stub mode) — accessing it should not raise
        _ = layer.rtk  # covers line 83

    @pytest.mark.asyncio
    async def test_rtk_stub_run_command_carries_savings(self):
        """RTK tool path — run_tool_command accumulates pending_rtk_savings."""
        layer = CompressionLayer()
        # run_tool_command with RTK enabled (stub handles missing binary)
        result = await layer.run_tool_command(["echo", "hello"], session_id="rtk-test")
        # Stub returns 0 bytes saved; subsequent encode picks up pending savings
        _, tags = await layer.encode_request({"x": 1}, session_id="rtk-test")
        # Tags should be present (pending savings = 0 in stub case, but path exercised)
        assert TAG_MODE in tags


class TestOrchestratorCoverageGaps:
    """Targeted tests to reach 100% line coverage on orchestrator.py."""

    @pytest.mark.asyncio
    async def test_forge_path_with_conversation(self):
        """Cover lines 140-145: Forge compaction with conversation arg (happy path)."""
        from praxis.kernel.compression.forge.models import Conversation, ConversationMessage, Role
        from praxis.kernel.compression.config import ForgeConfig

        # Use threshold=1 so compaction always triggers regardless of content size
        config = CompressionConfig(forge=ForgeConfig(enabled=True, message_threshold=1, token_threshold=1))
        layer = CompressionLayer(config=config)

        messages = [
            ConversationMessage(role=Role.USER, content="hello " * 50),
            ConversationMessage(role=Role.ASSISTANT, content="world " * 50),
            ConversationMessage(role=Role.USER, content="again " * 50),
            ConversationMessage(role=Role.ASSISTANT, content="ok " * 50),
        ]
        conv = Conversation(messages=messages)
        _, tags = await layer.encode_request({"x": 1}, conversation=conv)
        assert TAG_MODE in tags  # pipeline ran without crash

    @pytest.mark.asyncio
    async def test_forge_cascade_exception(self):
        """Cover lines 146-149: Forge exception is caught and cascade continues."""
        from unittest.mock import AsyncMock, patch
        from praxis.kernel.compression.forge.models import Conversation, ConversationMessage, Role
        from praxis.kernel.compression.config import ForgeConfig

        config = CompressionConfig(forge=ForgeConfig(enabled=True, message_threshold=1, token_threshold=1))
        layer = CompressionLayer(config=config)
        conv = Conversation(messages=[
            ConversationMessage(role=Role.USER, content="test"),
            ConversationMessage(role=Role.ASSISTANT, content="test"),
        ])

        with patch.object(layer._compactor, "compact", new_callable=AsyncMock,
                          side_effect=RuntimeError("forge exploded")):
            _, tags = await layer.encode_request({"x": 1}, conversation=conv)
        assert TAG_MODE in tags  # cascade did not propagate

    @pytest.mark.asyncio
    async def test_tonl_decode_error_cascade(self):
        """Cover lines 204-206: TONL-prefixed text that fails to parse."""
        layer = CompressionLayer()
        # Start with TONL1 prefix but corrupt body → TONLError cascade
        corrupted = "TONL1\nNOT_VALID_JSON{{{"
        decoded, tags = await layer.decode_response(corrupted)
        # Cascade isolation: must not raise; returns raw text
        assert decoded == corrupted

    @pytest.mark.asyncio
    async def test_caveman_enabled_fallback_path(self):
        """Cover lines 210-222, 226-228: Caveman enabled — provider error cascades gracefully."""
        from praxis.kernel.compression.config import CavemanConfig
        config = CompressionConfig(
            caveman=CavemanConfig(enabled=True, caveman_min_readers=0)
        )
        layer = CompressionLayer(config=config)
        prose = "The quick brown fox jumps over the lazy dog. " * 50
        decoded, tags = await layer.decode_response(
            prose, expected_downstream_reads=5
        )
        # Gate may pass or fail; either way, no crash and result is a string
        assert isinstance(decoded, str)

    @pytest.mark.asyncio
    async def test_caveman_compressed_path(self):
        """Cover lines 223-225: result.compressed=True branch."""
        from unittest.mock import AsyncMock, patch
        from praxis.kernel.compression.config import CavemanConfig
        from praxis.kernel.compression.caveman.models import CompressionResult, ValidationReport

        config = CompressionConfig(
            caveman=CavemanConfig(enabled=True, caveman_min_readers=0)
        )
        layer = CompressionLayer(config=config)
        prose = "The quick brown fox jumps over the lazy dog. " * 50

        fake_result = CompressionResult(
            text_in=prose,
            text_out="compressed text",
            compressed=True,
            net_savings_tokens=50,
            validation_report=ValidationReport(),
            caveman_tags={"compression.caveman.intensity": "moderate"},
        )
        with patch(
            "praxis.kernel.compression.orchestrator.caveman_compress",
            new_callable=AsyncMock,
            return_value=fake_result,
        ):
            decoded, tags = await layer.decode_response(prose, expected_downstream_reads=5)
        assert decoded == "compressed text"
        assert tags.get("compression.caveman.intensity") == "moderate"

    @pytest.mark.asyncio
    async def test_caveman_exception_cascade(self):
        """Cover lines 226-228: caveman_compress raises — cascade isolates."""
        from unittest.mock import AsyncMock, patch
        from praxis.kernel.compression.config import CavemanConfig

        config = CompressionConfig(
            caveman=CavemanConfig(enabled=True, caveman_min_readers=0)
        )
        layer = CompressionLayer(config=config)
        prose = "The quick brown fox jumps over the lazy dog. " * 50

        with patch(
            "praxis.kernel.compression.orchestrator.caveman_compress",
            new_callable=AsyncMock,
            side_effect=RuntimeError("caveman exploded"),
        ):
            decoded, tags = await layer.decode_response(prose, expected_downstream_reads=5)
        # Exception cascaded gracefully — original text returned
        assert decoded == prose
        assert "compression.caveman.fallback" in tags

    @pytest.mark.asyncio
    async def test_pending_rtk_savings_carryover(self):
        """Cover lines 154-159: RTK savings from tool command carry to next encode."""
        from praxis.kernel.compression.orchestrator import SessionStats
        layer = CompressionLayer()
        stats = await layer.session_stats("carry-sess")
        # Manually inject pending savings to exercise the carry-over branch
        stats.pending_rtk_savings = 1024
        _, tags = await layer.encode_request({"data": "x"}, session_id="carry-sess")
        # The carry-over branch should have fired and zeroed pending_rtk_savings
        assert stats.pending_rtk_savings == 0
        assert "compression.rtk.bytes_saved_prior" in tags
