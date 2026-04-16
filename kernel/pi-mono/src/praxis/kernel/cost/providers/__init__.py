"""Provider token extractors. Self-register at import time."""
from .anthropic import AnthropicProvider
from .base import Provider
from .fake import FakeProvider
from .google import GoogleProvider
from .openai import OpenAIProvider
from .registry import get_provider, register_provider, registered_providers

register_provider(AnthropicProvider)
register_provider(OpenAIProvider)
register_provider(GoogleProvider)
register_provider(FakeProvider)

__all__ = [
    "Provider",
    "AnthropicProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "FakeProvider",
    "get_provider",
    "register_provider",
    "registered_providers",
]
