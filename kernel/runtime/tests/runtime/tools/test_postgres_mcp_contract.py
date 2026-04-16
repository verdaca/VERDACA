"""tests/runtime/tools/test_postgres_mcp_contract.py — RED commit.

Contract tests for postgres-mcp. Architecture §6.1.6. Read-write separation.
"""

from __future__ import annotations


def test_postgres_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.postgres_mcp import PostgresMcpAdapter  # noqa: F401


def test_postgres_mcp_descriptor_blast_class_c() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.postgres_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.C


def test_postgres_mcp_default_read_only() -> None:
    from praxis.kernel.runtime.tools.postgres_mcp import DESCRIPTOR

    assert DESCRIPTOR.default_mode == "read-only"


def test_postgres_mcp_ddl_rejected() -> None:
    """DDL statements must be rejected at the adapter layer."""
    from praxis.kernel.runtime.tools.postgres_mcp import is_ddl_statement

    assert is_ddl_statement("CREATE TABLE foo (id INT)")
    assert is_ddl_statement("DROP TABLE bar")
    assert is_ddl_statement("ALTER TABLE baz ADD COLUMN x TEXT")


def test_postgres_mcp_select_not_ddl() -> None:
    from praxis.kernel.runtime.tools.postgres_mcp import is_ddl_statement

    assert not is_ddl_statement("SELECT * FROM users WHERE id = 1")


def test_postgres_validate_query_raises_on_ddl() -> None:
    """validate_query() raises ToolInputValidationError for DDL statements."""
    import pytest

    from praxis.kernel.runtime.tools._base import ToolInputValidationError
    from praxis.kernel.runtime.tools.postgres_mcp import PostgresMcpAdapter

    adapter = PostgresMcpAdapter()
    with pytest.raises(ToolInputValidationError, match="DDL"):
        adapter.validate_query("DROP TABLE users")


def test_postgres_validate_query_passes_for_select() -> None:
    """validate_query() does not raise for SELECT statements."""
    from praxis.kernel.runtime.tools.postgres_mcp import PostgresMcpAdapter

    adapter = PostgresMcpAdapter()
    adapter.validate_query("SELECT id, name FROM users WHERE active = true")  # must not raise
