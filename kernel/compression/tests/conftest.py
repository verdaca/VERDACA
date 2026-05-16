"""Shared fixtures for compression tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add compression src to path
_COMPRESSION_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_COMPRESSION_SRC) not in sys.path:
    sys.path.insert(0, str(_COMPRESSION_SRC))

# Add pi-mono src to path so praxis.kernel.cost is importable
_PI_MONO_SRC = (
    Path(__file__).resolve().parents[3] / "pi-mono" / "src"
)
if _PI_MONO_SRC.exists() and str(_PI_MONO_SRC) not in sys.path:
    sys.path.insert(0, str(_PI_MONO_SRC))

# Add ports src to path so praxis.ports.* is importable
_PORTS_SRC = Path(__file__).resolve().parents[3] / "ports" / "src"
if _PORTS_SRC.exists() and str(_PORTS_SRC) not in sys.path:
    sys.path.insert(0, str(_PORTS_SRC))


@pytest.fixture
def simple_dict_payload() -> dict:
    return {"session_id": "test-1", "count": 42, "active": True}


@pytest.fixture
def uniform_messages() -> list[dict]:
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you."},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "Tell me more."},
    ]


@pytest.fixture
def nested_payload(uniform_messages) -> dict:
    return {
        "messages": uniform_messages,
        "session_id": "sess-abc",
        "metadata": {"model": "claude-opus-4-6", "version": 1},
    }


@pytest.fixture
def long_prose_text() -> str:
    return (
        "This is a comprehensive report on the system architecture. "
        "The recommended approach is to enable all supported features. "
        "Do not disable the safety validations. The system is safe and correct. "
        "All components are valid and trusted. The public API is available. "
        "Required dependencies must be included; optional ones can be excluded. "
        "Enable the logging module and disable the debug mode in production. "
        "The configuration is correct and expected behavior is well-documented. "
        "Expected values: 100, 200, 300, 42, 3.14. Versions: 1.2.3, 2.0.0. "
        "Use the make command to build. Run pytest for testing. Include all files. "
    ) * 10  # ~1000 tokens
