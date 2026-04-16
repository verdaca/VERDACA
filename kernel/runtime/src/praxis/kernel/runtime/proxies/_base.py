"""Shared base types for Memory proxies — backward-compat re-export.

AgentRole was relocated to runtime.models (Checkpoint 3) to prevent
directional coupling between loader/registry and the proxy layer.

This file re-exports AgentRole from its canonical location so that all
existing Checkpoint 1 imports continue to work unchanged:

    from praxis.kernel.runtime.proxies import AgentRole     # still works
    from praxis.kernel.runtime.proxies._base import AgentRole  # still works
"""

from __future__ import annotations

# Re-export — NOT a redefinition.  The is-identity test in test_models.py
# verifies that proxies.AgentRole is runtime.models.AgentRole (same object).
from praxis.kernel.runtime.models import AgentRole  # noqa: F401

__all__ = ["AgentRole"]
