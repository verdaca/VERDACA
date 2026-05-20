"""Adversarial corpus rotation protocol tests — mac/test-strategy.md v0.3 §10.4.

Covers MAC-T-ADV-ROTATION-01..03. Arch §10.2 rotation protocol invariants.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.adversarial.rotation import (
    RotationAuditResult,
    RotationProtocol,
)


_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "persona_3"
)


@pytest.mark.critical
@pytest.mark.mac_adversarial
@pytest.mark.static
def test_mac_t_adv_rotation_01_public_and_rotating_distinct_directories() -> None:
    """MAC-T-ADV-ROTATION-01 — public/ and rotating/ are distinct with
    zero file overlap.

    Arch §10.2: rotating corpus is separate from public corpus.
    Promoting rotating prompts to public is out-of-band and
    explicitly NOT supported at step 5.
    """
    protocol = RotationProtocol(fixtures_root=_FIXTURES_ROOT)
    result = protocol.audit()

    assert result.public_count >= 3
    assert result.rotating_count >= 3
    assert result.overlap_files == ()


@pytest.mark.critical
@pytest.mark.mac_adversarial
@pytest.mark.static
def test_mac_t_adv_rotation_02_rotating_has_manifest_file() -> None:
    """MAC-T-ADV-ROTATION-02 — rotating/ has a ROTATION.yaml manifest.

    The manifest records ``replaced_at``, ``next_rotation_due``, and
    ``cadence_weeks`` so external auditors can verify the rotation
    is current.
    """
    protocol = RotationProtocol(fixtures_root=_FIXTURES_ROOT)
    result = protocol.audit()
    assert result.has_manifest

    manifest_path = _FIXTURES_ROOT / "rotating" / "ROTATION.yaml"
    text = manifest_path.read_text(encoding="utf-8")
    assert "replaced_at:" in text
    assert "cadence_weeks:" in text


@pytest.mark.critical
@pytest.mark.mac_adversarial
@pytest.mark.static
def test_mac_t_adv_rotation_03_readme_documents_rotation_cadence() -> None:
    """MAC-T-ADV-ROTATION-03 — README.md at the corpus root documents
    the rotation cadence, file format, and out-of-scope declaration.
    """
    protocol = RotationProtocol(fixtures_root=_FIXTURES_ROOT)
    result = protocol.audit()
    assert result.has_readme
    assert result.is_clean

    readme_path = _FIXTURES_ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    assert "rotation" in text.lower()
    # Rotation cadence must be stated.
    assert "4 weeks" in text
    # Out-of-scope declaration present per v0.3 §10.3.
    assert "jailbreak" in text.lower() or "out-of-scope" in text.lower()
