"""DeploymentManifest — minimal Phase 3C version.

Architecture §3.3 specifies a signed YAML file loaded at boot, with
60-second re-verification in the runtime. Phase 3C uses only the two
identity fields — the full loader, signature verification, and the
re-verification loop are Stage 7 ops territory.

Under managed single-tenant (Req B1), each deployment process pins
exactly one tenant for its entire lifetime. The facade validates every
incoming `tenant_id` against this manifest; a mismatch raises
`TenantIdentityError` and hard-fails the process per §8.2.

Fields
------
tenant_id
    Canonical tenant identity string (e.g., "acme-corp"). Used by the
    facade for defense-in-depth validation.
tenant_hash
    Derived identifier safe for filesystem paths, collection names, and
    audit hashes. In the real loader this is `sha256(tenant_id || salt)`;
    Phase 3C callers pass it directly.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DeploymentManifest(BaseModel):
    """Pinned tenant identity for the Memory process."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    tenant_id: str
    tenant_hash: str


__all__ = ["DeploymentManifest"]
