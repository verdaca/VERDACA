"""MAC adversarial corpus — arch §12.6 + benchmark-questions.md §4 Persona 3.

Public surface:
  - :class:`Persona3CorpusLoader` — loads the public + rotating gaming
    prompt fixtures from ``tests/mac/adversarial/fixtures/persona_3/``
  - :class:`RotationProtocol` — enforces the arch §10.2 rotation rules
    (no file overlap, manifest timestamps, N-week replacement)
"""

from __future__ import annotations

from praxis.kernel.mac.adversarial.persona_3 import Persona3CorpusLoader
from praxis.kernel.mac.adversarial.rotation import RotationProtocol

__all__ = (
    "Persona3CorpusLoader",
    "RotationProtocol",
)
