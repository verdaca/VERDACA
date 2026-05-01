"""Deployment manifest — tenant identity + boot-time invariants.

Phase 3C ships the MINIMUM subset of architecture §3.3:
  - Tenant identity (tenant_id + tenant_hash)
  - Frozen, strict, extra-forbid

Out of scope for Phase 3C (Stage 7 / ops territory):
  - Signed YAML loader
  - 60-second re-verification loop
  - Worktree path derivation
  - Break-glass ledger integration
"""

from praxis.kernel.memory.deployment.manifest import DeploymentManifest

__all__ = ["DeploymentManifest"]
