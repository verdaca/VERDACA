"""tests/runtime/tools/test_github_mcp_contract.py — RED commit.

Contract tests for github-mcp. Architecture §6.1.3, §9.6 C14 secret scanning.
S4.R-08: secret-scanning redaction.
"""

from __future__ import annotations


def test_github_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.github_mcp import GithubMcpAdapter  # noqa: F401


def test_github_mcp_secret_scanning_strips_sk_anthropic() -> None:
    from praxis.kernel.runtime.tools.github_mcp import redact_secrets

    content = "The API key is sk-proj-abc123xyz and use it carefully"
    redacted = redact_secrets(content)
    assert "sk-proj-abc123xyz" not in redacted


def test_github_mcp_secret_scanning_strips_ghp() -> None:
    from praxis.kernel.runtime.tools.github_mcp import redact_secrets

    content = "token = ghp_secrettoken1234567890abcdefgh"
    redacted = redact_secrets(content)
    assert "ghp_secrettoken" not in redacted


def test_github_mcp_secret_scanning_strips_aws() -> None:
    from praxis.kernel.runtime.tools.github_mcp import redact_secrets

    content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
    redacted = redact_secrets(content)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted


def test_github_mcp_descriptor_blast_class_b() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.github_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.B


def test_github_mcp_no_secrets_in_clean_content() -> None:
    from praxis.kernel.runtime.tools.github_mcp import redact_secrets

    clean = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    assert redact_secrets(clean) == clean
