"""Stage 13 AST gate inventory."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
CLOSE_MEMO_GLOB = "docs/stage-*-ratified-close-memo.md"


def _tracked_close_memos() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", CLOSE_MEMO_GLOB],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    }


def _on_disk_close_memos() -> set[str]:
    return {path.relative_to(ROOT).as_posix() for path in ROOT.glob(CLOSE_MEMO_GLOB)}


@pytest.mark.no_waiver
def test_gate_f_close_memo_tracking_symmetry() -> None:
    assert _tracked_close_memos() == _on_disk_close_memos()
