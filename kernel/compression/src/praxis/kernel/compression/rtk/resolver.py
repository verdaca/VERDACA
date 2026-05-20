"""RTK binary resolver — maps platform/arch to vendored binary path."""
from __future__ import annotations

import platform
from pathlib import Path

from .errors import RTKBinaryMissingError

# Vendored binary directory (relative to this file's parent)
BIN_DIR = Path(__file__).parent / "bin"

_PLATFORM_MAP: dict[tuple[str, str], str] = {
    ("linux", "x86_64"): "linux_x64/rtk",
    ("linux", "aarch64"): "linux_arm64/rtk",
    ("linux", "arm64"): "linux_arm64/rtk",
    ("darwin", "x86_64"): "darwin_x64/rtk",
    ("darwin", "arm64"): "darwin_arm64/rtk",
    ("windows", "amd64"): "windows_x64/rtk.exe",
    ("windows", "x86_64"): "windows_x64/rtk.exe",
}


def resolve_binary_path(override: str | None = None) -> Path:
    """Return the absolute path to the RTK binary for the current platform.

    Args:
        override: If set, use this path directly (for testing or custom installs).

    Raises:
        RTKBinaryMissingError: if no binary is available for this platform.
    """
    if override:
        p = Path(override)
        if not p.exists():
            raise RTKBinaryMissingError(f"override binary not found: {override}")
        return p

    system = platform.system().lower()   # linux | darwin | windows
    machine = platform.machine().lower() # x86_64 | aarch64 | arm64 | amd64

    key = (system, machine)
    relative = _PLATFORM_MAP.get(key)
    if relative is None:
        raise RTKBinaryMissingError(
            f"No vendored RTK binary for platform {system}/{machine}. "
            "RTK compression is disabled for this session."
        )

    binary_path = BIN_DIR / relative
    if not binary_path.exists():
        raise RTKBinaryMissingError(
            f"Vendored RTK binary missing at {binary_path}. "
            "RTK compression is disabled for this session."
        )

    return binary_path
