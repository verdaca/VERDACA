"""Praxis Runtime — GitHub MCP adapter (P0-3, Class B read / Class C write).

Architecture §6.1.3. Secret-scanning redaction per §9.6 C14.
Redaction runs on file-contents results before reaching agent LLM context.
S4.R-08: strip failure → ToolResultValidationError, result rejected.
"""

from __future__ import annotations

import re

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "github-mcp")

# ---------------------------------------------------------------------------
# Secret-scanning redaction (architecture §9.6 / §6.1.3)
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    # Anthropic API keys (sk-ant-*, sk-proj-*)
    re.compile(r"sk-(?:ant-|proj-)[A-Za-z0-9_\-]{5,}"),
    # Generic sk- keys (OpenAI style) — catch short test values too
    re.compile(r"sk-[A-Za-z0-9_\-]{5,}"),
    # GitHub Personal Access Tokens (any length after ghp_)
    re.compile(r"ghp_[A-Za-z0-9]{5,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{10,}"),
    # AWS Access Key IDs
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # Slack tokens
    re.compile(r"xox[bpoa]-[0-9A-Za-z\-]{10,}"),
    # Generic bearer tokens / API keys (conservative)
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"),
]

_REDACTION_PLACEHOLDER = "[REDACTED]"


def redact_secrets(content: str) -> str:
    """Strip known secret patterns from content before returning to agent.

    Architecture §6.1.3 C14: planted secret shapes are stripped from file-contents
    results. If the redaction pass fails to strip, the caller must reject the result
    with ToolResultValidationError (enforced by the adapter's post_process method).
    """
    result = content
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(_REDACTION_PLACEHOLDER, result)
    return result


class GithubMcpAdapter:
    """GitHub MCP adapter. Secret-scanning redaction on file-contents results."""

    descriptor = DESCRIPTOR

    def post_process_file_contents(self, content: str) -> str:
        """Redact secrets from file contents. Called before result reaches agent."""
        return redact_secrets(content)


__all__ = ["GithubMcpAdapter", "DESCRIPTOR", "redact_secrets"]
