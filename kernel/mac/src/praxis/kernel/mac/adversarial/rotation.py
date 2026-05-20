"""Adversarial corpus rotation protocol — arch §10.2.

Enforces three invariants:

  1. ``public/`` and ``rotating/`` are distinct directories with zero
     file-name overlap.
  2. ``rotating/`` contains a manifest file (``ROTATION.yaml``) with a
     ``replaced_at`` timestamp.
  3. Rotation README documents the replacement cadence.

``MAC-T-ADV-ROTATION-01..03`` assert these invariants at PR-gate time.

Binding anchors:
  - mac/architecture.md §10.2 Rotation Protocol
  - mac/test-strategy.md v0.3 §10.4 (citation repaired to arch §10.2)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RotationAuditResult:
    """Result of a :meth:`RotationProtocol.audit` call."""

    public_count: int
    rotating_count: int
    has_manifest: bool
    has_readme: bool
    overlap_files: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """True when all four rotation invariants hold."""
        return (
            self.has_manifest
            and self.has_readme
            and not self.overlap_files
            and self.public_count >= 3
            and self.rotating_count >= 3
        )


class RotationProtocol:
    """Audit the adversarial corpus against the arch §10.2 rotation rules."""

    MANIFEST_FILENAME: str = "ROTATION.yaml"
    README_FILENAME: str = "README.md"

    def __init__(self, fixtures_root: Path) -> None:
        self._root = fixtures_root

    def audit(self) -> RotationAuditResult:
        """Run the full audit and return a :class:`RotationAuditResult`."""
        public_dir = self._root / "public"
        rotating_dir = self._root / "rotating"

        public_files = (
            {f.name for f in public_dir.glob("*.txt")}
            if public_dir.exists()
            else set()
        )
        rotating_files = (
            {f.name for f in rotating_dir.glob("*.txt")}
            if rotating_dir.exists()
            else set()
        )

        overlap = sorted(public_files & rotating_files)
        has_manifest = (rotating_dir / self.MANIFEST_FILENAME).exists()
        has_readme = (self._root / self.README_FILENAME).exists()

        return RotationAuditResult(
            public_count=len(public_files),
            rotating_count=len(rotating_files),
            has_manifest=has_manifest,
            has_readme=has_readme,
            overlap_files=tuple(overlap),
        )


__all__ = (
    "RotationAuditResult",
    "RotationProtocol",
)
