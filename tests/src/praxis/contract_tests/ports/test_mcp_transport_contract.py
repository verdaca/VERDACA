"""Stage 11 E2 MCP transport contracts."""

from __future__ import annotations

from praxis.adapters.mcp_server import http
from praxis.adapters.mcp_server.http import (
    create_mcp_http_app,
    create_mcp_http_server,
    verify_bearer_authorization,
)
from praxis.adapters.mcp_server.stdio import create_stdio_server
from praxis.adapters.mcp_server.transport import MCPTransportPort


def test_M_T_MCP_TRANSPORT_HTTP_STATELESS_01_adapter_exposes_mcp_path() -> None:
    server = create_mcp_http_server()
    app = create_mcp_http_app()
    route_paths = {getattr(route, "path", None) for route in app.routes}

    assert server.settings.stateless_http is True
    assert server.settings.streamable_http_path == "/mcp"
    assert "/mcp" in route_paths


def test_M_T_MCP_TRANSPORT_HTTP_BEARER_01_uses_e1_policy(
    monkeypatch,
) -> None:
    monkeypatch.setenv("VERDACA_GATEWAY_BEARER_TOKEN", "test-token")

    assert verify_bearer_authorization("Bearer test-token") is True
    assert verify_bearer_authorization("Bearer wrong-token") is False


def test_M_T_MCP_TRANSPORT_HTTP_BEARER_01_main_runs_policy_health_check(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_policy_health_check() -> None:
        # Stage 14 B2: return type changed bool → None (callers were
        # side-effect-only); fake mirrors current production signature.
        calls.append("health")

    def fake_asyncio_run(coro) -> None:
        calls.append("run")
        coro.close()

    monkeypatch.setattr(http, "policy_health_check", fake_policy_health_check)
    monkeypatch.setattr(http.asyncio, "run", fake_asyncio_run)

    http.main()

    assert calls == ["health", "run"]


def test_M_T_MCP_TRANSPORT_STDIO_TOOL_LIST_01_stdio_server_has_tools() -> None:
    server = create_stdio_server()
    tool_names = {tool.name for tool in server._tool_manager.list_tools()}  # noqa: SLF001

    assert "verdaca_start_analysis" in tool_names
    assert "verdaca_estimate_cost" in tool_names


def test_M_T_MCP_TRANSPORT_STDIO_TOOL_LIST_01_transport_protocol_version() -> None:
    assert MCPTransportPort.API_VERSION == "1.0.0"
