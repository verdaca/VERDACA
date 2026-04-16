"""R4 Layer C — tenant identity cross-check at CostEvent emission points.

Architecture §8.1.5 Path B + §8.1.4 Path A: every CostEvent emission
validates tenant_hash against the deployment manifest.  A mismatch raises
TenantDriftError and terminates the Runtime process.

Architecture §9.4 Layer C (per-operation cross-check).
"""

from __future__ import annotations


class TenantDriftError(RuntimeError):
    """Raised when a CostEvent's tenant_hash doesn't match the manifest.

    This is a hard-fail condition — the Runtime process should terminate.
    Architecture §9.4 Layer C.
    """


def check_tenant(event_tenant_hash: str, manifest_tenant_hash: str) -> None:
    """Assert event_tenant_hash matches manifest_tenant_hash.

    Raises TenantDriftError on any mismatch.  Called by both Path A
    (reaper completion) and Path B (tick-drain loop) before any
    events_outbox INSERT is attempted.
    """
    if not event_tenant_hash:
        raise TenantDriftError(
            f"audit buffer event has empty tenant_hash; "
            f"manifest tenant_hash={manifest_tenant_hash!r}"
        )
    if event_tenant_hash != manifest_tenant_hash:
        raise TenantDriftError(
            f"audit buffer event tenant_hash {event_tenant_hash!r} "
            f"does not match manifest tenant_hash {manifest_tenant_hash!r}. "
            f"R4 Layer C drift detected — Runtime must terminate."
        )


__all__ = ["TenantDriftError", "check_tenant"]
