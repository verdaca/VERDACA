"""TONL tokenizer adapters."""
from .anthropic import AnthropicTokenizer
from .base import Tokenizer
from .generic import GenericTokenizer
from .openai import OpenAITokenizer

__all__ = ["Tokenizer", "GenericTokenizer", "AnthropicTokenizer", "OpenAITokenizer"]


def get_tokenizer(name: str | None) -> Tokenizer:
    """Resolve a tokenizer by name; falls back to GenericTokenizer."""
    if name is None or name == "generic":
        return GenericTokenizer()
    if name in ("anthropic", "claude"):
        return AnthropicTokenizer()
    if name in ("openai", "gpt"):
        return OpenAITokenizer()
    # Unknown — fall back with a warning
    import logging
    logging.getLogger(__name__).warning("Unknown tokenizer %r; using generic", name)
    return GenericTokenizer()
