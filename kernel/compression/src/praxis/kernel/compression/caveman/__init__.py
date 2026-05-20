"""Caveman — LLM-driven prose compressor (OFF by default, feature-flagged).

Public API (architecture §3.4.2):
    compress_output(request, *, ...) -> CompressionResult
    CompressionRequest, CompressionResult, Intensity, Dialect

Exceptions:
    CavemanError, CavemanProviderError, CavemanValidationError, CavemanGateDenied
"""
from .compressor import compress_output
from .errors import CavemanError, CavemanGateDenied, CavemanProviderError, CavemanValidationError
from .models import CompressionRequest, CompressionResult, Dialect, Intensity

__all__ = [
    "compress_output",
    "CompressionRequest",
    "CompressionResult",
    "Intensity",
    "Dialect",
    "CavemanError",
    "CavemanProviderError",
    "CavemanValidationError",
    "CavemanGateDenied",
]
