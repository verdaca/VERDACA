"""Provider Protocol — structural type for token extractors.

Providers translate native SDK responses into the universal 4-class token
schema. They **never** compute cost. They **never** touch Decimal.
"""
from __future__ import annotations

from typing import Any, ClassVar, Protocol, runtime_checkable

from ..models import LLMRequest, LLMResponse, ProviderName


@runtime_checkable
class Provider(Protocol):
    name: ClassVar[ProviderName]

    @staticmethod
    def supported_models() -> list[str]:
        """Return the set of model_ids this provider knows."""
        ...

    @staticmethod
    def extract_tokens(request: LLMRequest, raw_response: Any) -> LLMResponse:
        """Translate a native SDK response into an LLMResponse."""
        ...
