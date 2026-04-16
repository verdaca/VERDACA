"""Root conftest — path bootstrapping for the runtime test suite.

The memory package's praxis/ and praxis/kernel/ dirs use regular __init__.py,
which prevents Python's namespace-package mechanism from finding
praxis.kernel.runtime in a separate tree.  We fix this by:

  1. Adding both src/ trees to sys.path.
  2. After importing praxis and praxis.kernel (which Python resolves via
     memory/src), extending their __path__ to include the runtime/src subtrees.

This is the standard pkgutil.extend_path / __path__ extension pattern.
It fires once, before any test module is imported.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()
_RUNTIME_SRC = _HERE / "src"
_MEMORY_SRC = _HERE.parent / "memory" / "src"
_PIMONO_SRC = _HERE.parent / "pi-mono" / "src"

# Step 1: all src trees on sys.path (memory first so praxis/__init__.py
# is found — then we extend __path__ below).
for _p in [str(_MEMORY_SRC), str(_PIMONO_SRC), str(_RUNTIME_SRC)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Step 2: extend praxis.__path__ and praxis.kernel.__path__ so subpackages
# from both trees are discoverable.
import praxis  # noqa: E402 (must come after sys.path manipulation)
import praxis.kernel  # noqa: E402

_extra_praxis = [str(_RUNTIME_SRC / "praxis"), str(_MEMORY_SRC / "praxis"), str(_PIMONO_SRC / "praxis")]
for _ep in _extra_praxis:
    if _ep not in praxis.__path__:
        praxis.__path__ = list(praxis.__path__) + [_ep]  # type: ignore[assignment]

_extra_kernel = [
    str(_RUNTIME_SRC / "praxis" / "kernel"),
    str(_MEMORY_SRC / "praxis" / "kernel"),
    str(_PIMONO_SRC / "praxis" / "kernel"),
]
for _ek in _extra_kernel:
    if _ek not in praxis.kernel.__path__:
        praxis.kernel.__path__ = list(praxis.kernel.__path__) + [_ek]  # type: ignore[assignment]
