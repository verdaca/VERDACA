"""Compression Layer Orchestrator — pipeline composition with cascade isolation.

100% line + branch coverage required (Murat §0.1 — highest severity component).

Architecture §4.2: the orchestrator is the ONLY public surface. All pipeline
composition, cascade isolation, and Pi-Mono tag emission happen here.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .caveman import CompressionRequest as CavemanRequest
from .caveman import Dialect, Intensity
from .caveman import compress_output as caveman_compress
from .config import CompressionConfig
from .forge import CompactionConfig, Compactor, Conversation
from .rtk import RTKClient, RTKResult
from .telemetry import (
    TAG_BYTES_AFTER,
    TAG_BYTES_BEFORE,
    TAG_FALLBACK,
    TAG_MODE,
    TAG_PIPELINE,
    TAG_TOKENS_AFTER,
    TAG_TOKENS_BEFORE,
    apply_tags_to_request,
    merge_compression_tags,
)
from .tonl import TONLError, decode, encode

logger = logging.getLogger(__name__)


@dataclass
class SessionStats:
    """Per-session compression statistics."""

    session_id: str
    tonl_bytes_saved: int = 0
    forge_tokens_saved: int = 0
    caveman_tokens_saved: int = 0
    rtk_bytes_saved: int = 0
    fallback_count: int = 0
    tag_budget_exceeded_count: int = 0
    pending_rtk_savings: int = 0  # RTK bytes saved awaiting next LLMRequest attribution


class CompressionLayer:
    """The single public facade for all compression operations (architecture §4.2).

    Usage::

        layer = CompressionLayer(config=CompressionConfig())
        encoded = await layer.encode_request(payload, session_id="s1")
        decoded = await layer.decode_response(raw_text, session_id="s1")
        result  = await layer.rtk.run_command(["git", "log", "--oneline", "-10"])
    """

    def __init__(self, config: CompressionConfig | None = None) -> None:
        self._config = config or CompressionConfig()
        self._compactor = Compactor(
            CompactionConfig(
                token_threshold=self._config.forge.token_threshold,
                turn_threshold=self._config.forge.turn_threshold,
                message_threshold=self._config.forge.message_threshold,
                retention_window=self._config.forge.retention_window,
                eviction_window=self._config.forge.eviction_window,
                on_turn_end=self._config.forge.on_turn_end,
            )
        ) if self._config.forge.enabled else None

        self._rtk = RTKClient(
            binary_override=self._config.rtk.binary_override_path,
            timeout_s=self._config.rtk.timeout_s,
        ) if self._config.rtk.enabled else None

        self._sessions: dict[str, SessionStats] = {}

    @property
    def rtk(self) -> RTKClient | None:
        return self._rtk

    def _get_stats(self, session_id: str) -> SessionStats:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionStats(session_id=session_id)
        return self._sessions[session_id]

    async def encode_request(
        self,
        payload: Any,
        session_id: str = "default",
        *,
        conversation: Conversation | None = None,
        request: object | None = None,
    ) -> tuple[Any, dict[str, str]]:
        """Apply request-path compression: TONL encode + optional Forge compaction.

        Args:
            payload:      The payload to encode (dict, list, etc.)
            session_id:   Session identifier for stats tracking.
            conversation: Optional conversation for Forge compaction.
            request:      Optional LLMRequest to attach tags to.

        Returns:
            (encoded_payload, compression_tags)
            where compression_tags should be merged onto the LLMRequest.
        """
        if not self._config.is_enabled:
            return payload, {TAG_MODE: "off"}

        stats = self._get_stats(session_id)
        tags: dict[str, str] = {TAG_MODE: "on"}
        pipeline_layers: list[str] = []
        fallback: str | None = None

        # Measure before
        bytes_before = len(str(payload).encode("utf-8"))
        tokens_before = max(1, bytes_before // 4)

        encoded_payload = payload

        # --- TONL encode ---
        if self._config.tonl.enabled:
            try:
                tonl_text = encode(payload)
                encoded_payload = tonl_text
                pipeline_layers.append("tonl")
                bytes_after_tonl = len(tonl_text.encode("utf-8"))
                stats.tonl_bytes_saved += max(0, bytes_before - bytes_after_tonl)
            except Exception as exc:
                logger.warning("TONL encode failed (cascade isolated): %s", exc)
                fallback = f"tonl:{type(exc).__name__}"
                # encoded_payload stays as original — cascade continues

        # --- Forge compaction (operates on conversation, not current payload) ---
        forge_tags: dict[str, str] = {}
        if self._config.forge.enabled and self._compactor and conversation:
            try:
                result = await self._compactor.compact(conversation)
                if result.compacted:
                    pipeline_layers.append("forge")
                    forge_tags = result.forge_tags
                    stats.forge_tokens_saved += result.tokens_saved
            except Exception as exc:
                logger.warning("Forge compaction failed (cascade isolated): %s", exc)
                if fallback is None:
                    fallback = f"forge:{type(exc).__name__}"

        tags.update(forge_tags)

        # Carry over pending RTK savings from previous tool output
        if stats.pending_rtk_savings > 0:
            tags["compression.rtk.bytes_saved_prior"] = str(stats.pending_rtk_savings)
            stats.rtk_bytes_saved += stats.pending_rtk_savings
            stats.pending_rtk_savings = 0
            if "rtk" not in pipeline_layers:
                pipeline_layers.append("rtk")

        # Aggregate tags
        bytes_after = len(str(encoded_payload).encode("utf-8"))
        tokens_after = max(1, bytes_after // 4)

        tags[TAG_TOKENS_BEFORE] = str(tokens_before)
        tags[TAG_TOKENS_AFTER] = str(tokens_after)
        tags[TAG_BYTES_BEFORE] = str(bytes_before)
        tags[TAG_BYTES_AFTER] = str(bytes_after)
        tags[TAG_PIPELINE] = ",".join(pipeline_layers) if pipeline_layers else "none"

        if fallback:
            tags[TAG_FALLBACK] = fallback

        return encoded_payload, tags

    async def decode_response(
        self,
        raw: str,
        session_id: str = "default",
        *,
        expected_downstream_reads: int = 0,
    ) -> tuple[str, dict[str, str]]:
        """Apply response-path compression: TONL decode + optional Caveman.

        Args:
            raw:                     Raw LLM response text.
            session_id:              Session identifier.
            expected_downstream_reads: For Caveman gate (how many agents will read this).

        Returns:
            (processed_text, caveman_tags)
        """
        if not self._config.is_enabled:
            return raw, {}

        stats = self._get_stats(session_id)
        caveman_tags: dict[str, str] = {}

        # --- TONL decode ---
        decoded = raw
        if self._config.tonl.enabled and raw.startswith("TONL1\n"):
            try:
                decoded = str(decode(raw))
            except TONLError as exc:
                logger.warning("TONL decode failed (cascade isolated): %s", exc)
                decoded = raw  # continue with raw text

        # --- Caveman (gated, feature-flagged OFF by default) ---
        if self._config.caveman.enabled:
            try:
                request = CavemanRequest(
                    text=decoded,
                    intensity=Intensity(self._config.caveman.default_intensity),
                    dialect=Dialect(self._config.caveman.default_dialect),
                    expected_downstream_reads=expected_downstream_reads,
                    accept_wenyan=self._config.caveman.accept_wenyan,
                )
                result = await caveman_compress(
                    request,
                    max_retries=self._config.caveman.max_retries,
                )
                caveman_tags = result.caveman_tags
                if result.compressed:
                    decoded = result.text_out
                    stats.caveman_tokens_saved += result.net_savings_tokens
            except Exception as exc:
                logger.warning("Caveman compression failed (cascade isolated): %s", exc)
                caveman_tags["compression.caveman.fallback"] = f"exception:{type(exc).__name__}"

        return decoded, caveman_tags

    async def run_tool_command(
        self,
        argv: list[str],
        session_id: str = "default",
        *,
        timeout_s: float | None = None,
    ) -> RTKResult:
        """Run a shell command through RTK (tool path).

        Savings from this call are attributed to the NEXT LLMRequest in this session
        (pay-it-forward accounting, architecture §2.4).
        """
        if not self._config.rtk.enabled or self._rtk is None:
            from .rtk.client import RTKResult
            return RTKResult(
                stdout="",
                stderr="RTK disabled",
                exit_code=1,
                bytes_before=0,
                bytes_after=0,
                tokens_saved_estimate=0,
                rtk_used=False,
            )

        result = await self._rtk.run_command(
            argv, timeout_s=timeout_s or self._config.rtk.timeout_s
        )

        # Accumulate savings for next LLMRequest attribution
        stats = self._get_stats(session_id)
        stats.pending_rtk_savings += result.bytes_saved

        return result

    async def session_stats(self, session_id: str) -> SessionStats:
        """Return accumulated compression statistics for *session_id*."""
        return self._get_stats(session_id)
