"""Caveman compression error hierarchy."""
from __future__ import annotations


class CavemanError(Exception):
    """Base for all Caveman errors."""


class CavemanProviderError(CavemanError):
    """LLM provider call failed (rate limit, network, unavailable)."""


class CavemanValidationError(CavemanError):
    """Validation exhausted all retries."""


class CavemanGateDenied(CavemanError):
    """Net-positive gate denied compression."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"gate denied: {reason}")
