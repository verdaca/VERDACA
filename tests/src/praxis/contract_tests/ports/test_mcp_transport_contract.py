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
    # Stage 14 Phase-0.5: main() now composes a live gateway (async OIDC
    # discovery) inside a single asyncio.run, then calls
    # policy_health_check(policy=...) with the built policy BEFORE serving.
    # This plain contract test (NOT @no_waiver — pin unaffected) is updated to
    # assert the new compose → health(policy) → serve order; the MAC-T intent
    # ("main validates deploy posture before serving") is preserved.
    calls: list[str] = []
    sentinel_gateway = object()
    sentinel_policy = object()

    async def fake_compose_auth_quartet():
        calls.append("compose")
        return ("verifier", "oidc")

    def fake_build_runtime_gateway(*, jwt_verifier, oidc_policy):
        calls.append("build")
        assert (jwt_verifier, oidc_policy) == ("verifier", "oidc")
        return sentinel_gateway, sentinel_policy

    def fake_policy_health_check(policy=None) -> None:
        calls.append("health")
        assert policy is sentinel_policy

    async def fake_serve_http(*, gateway=None) -> None:
        calls.append("serve")
        assert gateway is sentinel_gateway

    monkeypatch.setattr(http, "compose_auth_quartet", fake_compose_auth_quartet)
    monkeypatch.setattr(http, "build_runtime_gateway", fake_build_runtime_gateway)
    monkeypatch.setattr(http, "policy_health_check", fake_policy_health_check)
    monkeypatch.setattr(http, "serve_http", fake_serve_http)

    http.main()

    assert calls == ["compose", "build", "health", "serve"]


def test_M_T_MCP_TRANSPORT_STDIO_TOOL_LIST_01_stdio_server_has_tools() -> None:
    server = create_stdio_server()
    tool_names = {tool.name for tool in server._tool_manager.list_tools()}  # noqa: SLF001

    assert "verdaca_start_analysis" in tool_names
    assert "verdaca_estimate_cost" in tool_names


def test_M_T_MCP_TRANSPORT_STDIO_TOOL_LIST_01_transport_protocol_version() -> None:
    assert MCPTransportPort.API_VERSION == "1.0.0"
