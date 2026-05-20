"""Fake fixtures for MAC tests — test-strategy v0.3 §14.3.

Each fake is a frozen interface contract that Amelia transcribes verbatim
per v0.3 §14.3.x. Additional fakes land as subsequent steps bring their
gate / asymmetry / benchmark / bootstrap integration layers online.
"""

from __future__ import annotations

from praxis.kernel.mac.testing.fakes.fake_benchmark_outputs import (
    BASELINES,
    FakeBenchmarkOutputs,
    PreScoredOutput,
    QUESTION_IDS,
    build_default_benchmark_outputs,
)
from praxis.kernel.mac.testing.fakes.fake_compressor import (
    CompressionResult,
    FakeCompressor,
)
from praxis.kernel.mac.testing.fakes.fake_llm_judge import (
    FakeLLMJudge,
    build_default_lookup_table,
)
from praxis.kernel.mac.testing.fakes.fake_memory_facade import FakeMemoryFacade
from praxis.kernel.mac.testing.fakes.fake_memory_proxies import (
    FakeProducerProxy,
    FakeReviewerProxy,
)
from praxis.kernel.mac.testing.fakes.fake_metadata_store import (
    InMemoryMacBootstrapMetadataStore,
    MacBootstrapMetadataRow,
)
from praxis.kernel.mac.testing.fakes.frozen_clock import FrozenClock

__all__ = (
    "BASELINES",
    "CompressionResult",
    "FakeBenchmarkOutputs",
    "FakeCompressor",
    "FakeLLMJudge",
    "FakeMemoryFacade",
    "FakeProducerProxy",
    "FakeReviewerProxy",
    "FrozenClock",
    "InMemoryMacBootstrapMetadataStore",
    "MacBootstrapMetadataRow",
    "PreScoredOutput",
    "QUESTION_IDS",
    "build_default_benchmark_outputs",
    "build_default_lookup_table",
)
