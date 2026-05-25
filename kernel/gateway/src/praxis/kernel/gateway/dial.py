"""DIAL execution binding for the gateway."""

from __future__ import annotations

from typing import cast

from praxis.adapters.litellm import LiteLLMAdapter  # type: ignore[import-untyped]
from praxis.ports.llm_proxy import LLMProxyPort

DIAL_LITELLM_PROVIDER = "azure"
DIAL_LITELLM_MODEL = "gpt-4o"
DIAL_API_BASE = "https://ai-proxy.lab.epam.com"
DIAL_API_VERSION = "2024-02-01"


def create_dial_llm_proxy(*, api_key: str | None = None) -> LLMProxyPort:
    """Create the LiteLLM-backed EPAM DIAL LLM proxy."""
    api_keys = {DIAL_LITELLM_PROVIDER: api_key} if api_key is not None else None
    return cast(
        LLMProxyPort,
        LiteLLMAdapter(
            api_keys=api_keys,
            api_base_overrides={DIAL_LITELLM_PROVIDER: DIAL_API_BASE},
            api_version_overrides={DIAL_LITELLM_PROVIDER: DIAL_API_VERSION},
        ),
    )


__all__ = [
    "DIAL_API_BASE",
    "DIAL_API_VERSION",
    "DIAL_LITELLM_MODEL",
    "DIAL_LITELLM_PROVIDER",
    "create_dial_llm_proxy",
]
