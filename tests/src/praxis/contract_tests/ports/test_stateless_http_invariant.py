"""Stage 11 H#1 FastMCP stateless Streamable HTTP invariant probe."""

from mcp.server.fastmcp import FastMCP


def test_fastmcp_stateless_http_path_is_mcp_and_stateless() -> None:
    server = FastMCP("verdaca-stage11-probe", stateless_http=True)
    app = server.streamable_http_app()
    route_paths = {getattr(route, "path", None) for route in app.routes}

    assert server.settings.stateless_http is True
    assert server.settings.streamable_http_path == "/mcp"
    assert "/mcp" in route_paths


def test_fastmcp_stateful_default_is_not_silently_used() -> None:
    server = FastMCP("verdaca-stage11-probe-default")

    assert server.settings.stateless_http is False
