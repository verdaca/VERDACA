"""Verdaca runtime composition root (neutral apex).

Wires the FROZEN kernel composition (``build_gateway``) with adapter substrates
into a deployable ``GatewayPort``. Hoisted out of the ``mcp_server`` adapter
(D-1 / finding D-O6-6) so transports — the MCP server and the Teams/Slack
channel webhooks — depend on THIS neutral member rather than on each other. The
prior wrong-direction ``channels → mcp_server → FastMCP`` arrow is gone.
"""

from praxis.composition.runtime_gateway import (
    build_runtime_gateway,
    compose_auth_quartet,
)

__all__ = ["build_runtime_gateway", "compose_auth_quartet"]
