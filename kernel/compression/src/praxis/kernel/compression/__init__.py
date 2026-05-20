"""Praxis Compression Layer — Stage 2 of the Praxis build pipeline.

Public API (architecture §4.2):
    CompressionLayer(config=CompressionConfig()) — the ONLY public facade

Sub-modules are implementation detail. Import from this module only:
    CompressionLayer, CompressionConfig
"""
from .config import CompressionConfig
from .orchestrator import CompressionLayer, SessionStats

__all__ = [
    "CompressionLayer",
    "CompressionConfig",
    "SessionStats",
]
