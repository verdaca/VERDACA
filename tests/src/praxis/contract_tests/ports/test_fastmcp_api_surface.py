"""Stage 11 H#1 FastMCP substrate API probe."""

from importlib.metadata import version
from inspect import signature

from mcp.server.fastmcp import FastMCP

PINNED_MCP_VERSION = "1.27.0"
REQUIRED_FASTMCP_ATTRIBUTES = frozenset(
    {
        "run_stdio_async",
        "run_streamable_http_async",
        "streamable_http_app",
    }
)


def test_fastmcp_api_surface_matches_stage11_substrate_probe() -> None:
    missing = {
        attr for attr in REQUIRED_FASTMCP_ATTRIBUTES if not hasattr(FastMCP, attr)
    }

    assert version("mcp") == PINNED_MCP_VERSION
    assert missing == set()


def test_fastmcp_constructor_exposes_stateless_http_switch() -> None:
    params = signature(FastMCP).parameters

    assert "stateless_http" in params
    assert params["stateless_http"].default is False
