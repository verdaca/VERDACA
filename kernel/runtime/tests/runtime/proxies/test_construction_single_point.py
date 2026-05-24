"""S4.R-01 Layer 2 — Single-point proxy construction audit.

Architecture §4.1.5 / §9.1.1 / §11.2: _construct_memory_proxy is the
ONLY proxy creation point in the runtime.  Verified via:
  (a) Functional tests: correct type per AgentRole.
  (b) Static AST scan: ProducerMemoryProxy()/ReviewerMemoryProxy()
      construction calls appear ONLY in proxies/_construction.py.

Test-strategy §11.2.1 + §11.2.2 + §11.2.3.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import pytest

from praxis.kernel.runtime.proxies import (
    AgentRole,
    ProducerMemoryProxy,
    ReviewerMemoryProxy,
    _construct_memory_proxy,
)
from praxis.kernel.runtime.testing import make_fake_memory


def _find_python_files_containing(root: Path, needle: str) -> list[str]:
    matches: list[str] = []
    for path in root.rglob("*.py"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if needle in line:
                matches.append(f"{path}:{line_number}:{line}")
    return matches

# ---------------------------------------------------------------------------
# §11.2.3 — Construction round-trip: role → correct proxy type
# ---------------------------------------------------------------------------


@pytest.mark.critical
class TestConstructionRoundTrip:
    def test_producer_role_yields_producer_proxy(self) -> None:
        proxy = _construct_memory_proxy(
            memory=make_fake_memory(),
            tenant_id="t",
            agent_name="amelia",
            spawn_id=uuid4(),
            role=AgentRole.PRODUCER,
        )
        assert isinstance(proxy, ProducerMemoryProxy)
        assert not isinstance(proxy, ReviewerMemoryProxy)

    def test_reviewer_role_yields_reviewer_proxy(self) -> None:
        proxy = _construct_memory_proxy(
            memory=make_fake_memory(),
            tenant_id="t",
            agent_name="quinn",
            spawn_id=uuid4(),
            role=AgentRole.REVIEWER,
        )
        assert isinstance(proxy, ReviewerMemoryProxy)
        assert not isinstance(proxy, ProducerMemoryProxy)

    def test_unknown_role_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown role"):
            _construct_memory_proxy(
                memory=make_fake_memory(),
                tenant_id="t",
                agent_name="x",
                spawn_id=uuid4(),
                role="not_a_role",  # type: ignore[arg-type]
            )

    def test_role_is_mandatory(self) -> None:
        """Calling without role= raises TypeError — not a default."""
        with pytest.raises(TypeError):
            _construct_memory_proxy(  # type: ignore[call-arg]
                memory=make_fake_memory(),
                tenant_id="t",
                agent_name="x",
                spawn_id=uuid4(),
            )


# ---------------------------------------------------------------------------
# §11.2.1 — _construct_memory_proxy has exactly one definition
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.static
def test_construct_memory_proxy_defined_exactly_once() -> None:
    """grep over runtime src for 'def _construct_memory_proxy' — must be 1."""
    runtime_root = Path(__file__).resolve().parents[3] / "src" / "praxis" / "kernel" / "runtime"
    definitions = _find_python_files_containing(runtime_root, "def _construct_memory_proxy")
    assert len(definitions) == 1, (
        f"Expected exactly 1 definition of _construct_memory_proxy, found "
        f"{len(definitions)}: {definitions}"
    )


# ---------------------------------------------------------------------------
# §11.2.2 — Proxy construction only inside _construction.py
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.static
def test_proxy_classes_only_constructed_inside_construction_module() -> None:
    """ProducerMemoryProxy( and ReviewerMemoryProxy( appear ONLY in _construction.py.

    Any construction outside that file is a Layer 2 back-door bypassing
    the Spawner's role-based selection (arch §9.1.1 single-point claim).
    """
    runtime_root = Path(__file__).resolve().parents[3] / "src" / "praxis" / "kernel" / "runtime"
    for proxy_class in ["ProducerMemoryProxy", "ReviewerMemoryProxy"]:
        forbidden = [
            line
            for line in _find_python_files_containing(runtime_root, f"{proxy_class}(")
            if line.strip()
            and "_construction.py" not in line
            # Allow class definitions themselves
            and not re.search(rf"class {proxy_class}", line)
            # Allow docstring references (lines starting with # or inside docstrings)
            and not line.strip().split(":", 2)[-1].lstrip().startswith("#")
            # Allow docstring references (contains '...' as placeholder)
            and "..." not in line.split(":", 2)[-1]
        ]
        assert forbidden == [], (
            f"{proxy_class} constructed outside _construction.py: {forbidden}. "
            f"Layer 2 back-door detected — §9.1.1 single-point claim violated."
        )
