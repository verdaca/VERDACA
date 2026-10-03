"""Shared loader for the onboarding scripts.

The onboarding entrypoints live at ``scripts/onboarding/*.py`` (hyphenated,
outside the ``praxis`` import path), so tests load them by file path rather
than by import. The loader executes the module's top-level imports; it does
NOT run ``main`` (no ``__main__`` trigger), so importing is side-effect-free.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest

ONBOARDING_DIR = Path(__file__).resolve().parents[4] / "scripts" / "onboarding"


def _load(filename: str, module_name: str) -> ModuleType:
    path = ONBOARDING_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        raise ImportError(f"cannot load onboarding script: {path}")
    module = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so module-level @dataclass annotation resolution
    # (dataclasses looks up sys.modules[cls.__module__]) succeeds.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def load_onboarding_script() -> Callable[[str, str], ModuleType]:
    return _load
