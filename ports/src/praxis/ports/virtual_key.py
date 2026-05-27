"""Virtual key port for managed LiteLLM proxy credentials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class VirtualKeySpec:
    key_alias: str
    max_budget: float
    max_parallel_requests: int
    allowed_models: list[str]
    duration: str


@dataclass(frozen=True)
class VirtualKeyInfo:
    key_alias: str
    token: str
    spend: float
    max_budget: float
    is_over_budget: bool


class BudgetExhaustedError(Exception):
    """Raised when virtual key spend has reached or exceeded budget."""


class VirtualKeyPort(Protocol):
    async def create_virtual_key(self, spec: VirtualKeySpec) -> VirtualKeyInfo: ...
    async def get_key_info(self, key_alias: str) -> VirtualKeyInfo: ...
    async def check_budget(self, key_alias: str) -> None: ...
    async def get_spend_logs(self, key_alias: str) -> list[dict[str, Any]]: ...


__all__ = [
    "BudgetExhaustedError",
    "VirtualKeyInfo",
    "VirtualKeyPort",
    "VirtualKeySpec",
]
