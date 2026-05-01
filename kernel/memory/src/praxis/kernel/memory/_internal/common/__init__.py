"""Shared low-level primitives for the praxis.kernel.memory module.

Everything in this subpackage lives behind the `_internal` banned-import boundary
(see NR-S-R1). Application code MUST NOT import from here directly — go through
the `praxis.kernel.memory` facade.
"""

__all__: list[str] = []
