"""TONL — tokenizer-aware serialization replacing JSON for LLM payloads.

Public API (architecture §3.1.2):
    encode(payload, *, tokenizer=None) -> str
    decode(text) -> Any
    encode_stream(source, *, tokenizer=None) -> AsyncIterator[str]
    decode_stream(source) -> AsyncIterator[Any]
    TONLDocument

Exceptions:
    TONLError, TONLParseError, TONLValidationError, TONLTypeError, TONLSecurityError
"""
from .decode import decode
from .document import TONLDocument
from .encode import encode
from .errors import (
    TONLError,
    TONLParseError,
    TONLSecurityError,
    TONLTypeError,
    TONLValidationError,
)
from .stream import decode_stream, encode_stream

__all__ = [
    "encode",
    "decode",
    "encode_stream",
    "decode_stream",
    "TONLDocument",
    "TONLError",
    "TONLParseError",
    "TONLValidationError",
    "TONLTypeError",
    "TONLSecurityError",
]
