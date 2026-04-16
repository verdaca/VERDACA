"""Provider registry — register/lookup by ProviderName."""
from __future__ import annotations

from ..errors import CostTrackerError
from ..models import ProviderName
from .base import Provider

_registry: dict[ProviderName, type[Provider]] = {}


def register_provider(provider: type[Provider]) -> None:
    name = provider.name
    if name in _registry and _registry[name] is not provider:
        raise CostTrackerError(f"provider already registered: {name}")
    _registry[name] = provider


def get_provider(name: ProviderName) -> type[Provider]:
    try:
        return _registry[name]
    except KeyError as exc:
        raise CostTrackerError(f"no provider registered for {name}") from exc


def registered_providers() -> list[ProviderName]:
    return sorted(_registry.keys())
