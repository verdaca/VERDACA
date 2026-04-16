"""tests/runtime/tools/test_fs_mcp_contract.py — RED commit.

Contract tests for fs-mcp (filesystem MCP adapter).
Architecture §6.1.1, §9.5 Class C, §9.6 secret isolation.
"""

from __future__ import annotations


def test_fs_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import FsMcpAdapter  # noqa: F401


def test_fs_mcp_denylist_dotenv() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied(".env")


def test_fs_mcp_denylist_ssh() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied(".ssh/id_rsa")


def test_fs_mcp_denylist_credentials() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("credentials.json")


def test_fs_mcp_denylist_secrets_dir() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("app/config/secrets/api_key.txt")


def test_fs_mcp_allowed_path_not_denied() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert not is_path_denied("src/main.py")
    assert not is_path_denied("tests/test_foo.py")


def test_fs_mcp_descriptor_blast_class_c() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.fs_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.C


def test_fs_mcp_descriptor_default_read_only() -> None:
    from praxis.kernel.runtime.tools.fs_mcp import DESCRIPTOR

    assert DESCRIPTOR.default_mode == "read-only"


# ---------------------------------------------------------------------------
# Additional edge-case coverage for is_path_denied (lines 69-98)
# ---------------------------------------------------------------------------


def test_fs_mcp_denylist_dotenv_variant() -> None:
    """'.env.production' matches the .env.* denylist pattern."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied(".env.production")
    assert is_path_denied(".env.local")
    assert is_path_denied("config/.env.staging")


def test_fs_mcp_denylist_secrets_dir_parts() -> None:
    """A path with 'secrets' as a directory segment is denied."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("app/secrets/config.yml")
    assert is_path_denied("infra/secrets/db_password")


def test_fs_mcp_denylist_ssh_dir_parts() -> None:
    """A path containing '.ssh' as a segment is denied."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("home/user/.ssh/known_hosts")
    assert is_path_denied(".ssh/config")


def test_fs_mcp_denylist_credentials_file() -> None:
    """Credentials files at arbitrary paths are denied."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("config/credentials.yaml")
    assert is_path_denied("deploy/credentials.toml")


def test_fs_mcp_pre_invoke_check_raises_on_denied_path() -> None:
    """pre_invoke_check() raises FileSystemAccessDeniedError for denied paths."""
    import pytest

    from praxis.kernel.runtime.tools._base import FileSystemAccessDeniedError
    from praxis.kernel.runtime.tools.fs_mcp import FsMcpAdapter

    adapter = FsMcpAdapter()
    with pytest.raises(FileSystemAccessDeniedError, match="denylist"):
        adapter.pre_invoke_check(".env", mode="read")


def test_fs_mcp_pre_invoke_check_passes_for_allowed_path() -> None:
    """pre_invoke_check() does not raise for a normal path."""
    from praxis.kernel.runtime.tools.fs_mcp import FsMcpAdapter

    adapter = FsMcpAdapter()
    adapter.pre_invoke_check("src/main.py", mode="read")  # must not raise


def test_fs_mcp_denylist_ssh_file_directly() -> None:
    """Direct '.ssh' path is denied (line 90 branch)."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied(".ssh")


def test_fs_mcp_denylist_credentials_json_at_path() -> None:
    """Specific credentials.json path denied via name-based check (line 81)."""
    from praxis.kernel.runtime.tools.fs_mcp import is_path_denied

    assert is_path_denied("some/path/credentials.json")
    assert is_path_denied("credentials.yaml")
