"""Observability test fixtures — ResetCounterFixture autouse.

Per test-strategy v0.3 §14.3.7 S-Q2 bake-in: the
``mac.label_registry.violations`` counter is reset to 0 before each
test in this subtree. Autouse fixture guarantees test-to-test
isolation — no try/except wrapping, no manual reset calls in test bodies.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.observability.counters import MacCounters
from praxis.kernel.mac.observability.emitter import VIOLATIONS_COUNTER


@pytest.fixture(autouse=True)
def reset_counter_fixture():
    """Reset ``mac.label_registry.violations`` to 0 before each test.

    Autouse — applied to every test in tests/mac/observability/.
    """
    MacCounters.reset(VIOLATIONS_COUNTER)
    yield
