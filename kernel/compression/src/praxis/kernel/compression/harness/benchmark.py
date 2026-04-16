"""A/B benchmark harness — runs workloads with compression ON vs OFF."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import CompressionConfig
from ..orchestrator import CompressionLayer
from .workload import Workload, WorkloadRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequestResult:
    """Result for a single workload request."""

    description: str
    bytes_before: int
    bytes_after: int
    tokens_before: int
    tokens_after: int
    layers_applied: list[str]
    fallback: str | None = None


@dataclass
class WorkloadRunResult:
    """Aggregated result for a full workload run."""

    workload_name: str
    mode: str  # "on" or "off"
    config_hash: str
    request_results: list[RequestResult] = field(default_factory=list)

    @property
    def total_bytes_before(self) -> int:
        return sum(r.bytes_before for r in self.request_results)

    @property
    def total_bytes_after(self) -> int:
        return sum(r.bytes_after for r in self.request_results)

    @property
    def total_tokens_before(self) -> int:
        return sum(r.tokens_before for r in self.request_results)

    @property
    def total_tokens_after(self) -> int:
        return sum(r.tokens_after for r in self.request_results)

    @property
    def savings_bytes(self) -> int:
        return max(0, self.total_bytes_before - self.total_bytes_after)

    @property
    def savings_pct(self) -> float:
        if self.total_bytes_before == 0:
            return 0.0
        return 100.0 * self.savings_bytes / self.total_bytes_before

    @property
    def fallback_count(self) -> int:
        return sum(1 for r in self.request_results if r.fallback)


@dataclass
class ABComparison:
    """Side-by-side comparison of ON vs OFF runs."""

    workload_name: str
    on_result: WorkloadRunResult
    off_result: WorkloadRunResult

    @property
    def config_consistent(self) -> bool:
        return self.on_result.config_hash == self.off_result.config_hash

    @property
    def savings_pct(self) -> float:
        return self.on_result.savings_pct

    @property
    def token_reduction_pct(self) -> float:
        if self.off_result.total_tokens_before == 0:
            return 0.0
        delta = self.off_result.total_tokens_before - self.on_result.total_tokens_after
        return 100.0 * delta / self.off_result.total_tokens_before


def _hash_config(config: CompressionConfig) -> str:
    """Hash the config excluding `mode` — so ON and OFF runs of the same config match."""
    data = config.model_dump()
    data.pop("mode", None)
    config_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


async def run_workload(
    workload: Workload,
    config: CompressionConfig,
    mode: str,
) -> WorkloadRunResult:
    """Run a workload with the given *config* and return aggregated metrics."""
    layer = CompressionLayer(config=config)
    config_hash = _hash_config(config)
    results: list[RequestResult] = []

    for req in workload.requests:
        try:
            encoded, tags = await layer.encode_request(
                req.payload,
                session_id=req.session_id,
            )

            bytes_before = int(tags.get("compression.bytes.before", len(str(req.payload))))
            bytes_after = int(tags.get("compression.bytes.after", len(str(encoded))))
            tokens_before = int(tags.get("compression.tokens.before", bytes_before // 4))
            tokens_after = int(tags.get("compression.tokens.after", bytes_after // 4))
            pipeline = tags.get("compression.pipeline", "none").split(",")
            fallback = tags.get("compression.fallback")

            results.append(RequestResult(
                description=req.description,
                bytes_before=bytes_before,
                bytes_after=bytes_after,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                layers_applied=pipeline,
                fallback=fallback,
            ))
        except Exception as exc:
            logger.error("harness: request %r failed: %s", req.description, exc)
            payload_bytes = len(str(req.payload).encode("utf-8"))
            results.append(RequestResult(
                description=req.description,
                bytes_before=payload_bytes,
                bytes_after=payload_bytes,
                tokens_before=payload_bytes // 4,
                tokens_after=payload_bytes // 4,
                layers_applied=[],
                fallback=f"exception:{type(exc).__name__}",
            ))

    return WorkloadRunResult(
        workload_name=workload.name,
        mode=mode,
        config_hash=config_hash,
        request_results=results,
    )


async def run_ab_comparison(
    workload: Workload,
    config: CompressionConfig,
) -> ABComparison:
    """Run the workload with compression ON and OFF; return side-by-side comparison."""
    off_config = config.model_copy(update={"mode": "off"})

    on_result, off_result = await asyncio.gather(
        run_workload(workload, config, mode="on"),
        run_workload(workload, off_config, mode="off"),
    )

    return ABComparison(
        workload_name=workload.name,
        on_result=on_result,
        off_result=off_result,
    )
