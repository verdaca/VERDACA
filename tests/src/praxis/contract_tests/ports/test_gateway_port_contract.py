"""Stage 11 Phase A expected-RED GatewayPort implementation probe.

This file is intentionally RED until the Stage 11 Phase A gateway package lands
and satisfies the frozen GatewayPort Protocol from praxis.ports.gateway.
"""


def test_gateway_port_contract_red_until_phase_a_impl() -> None:
    from praxis.ports.gateway import GatewayPort
    from praxis.kernel.gateway import VerdacaGatewayService

    gateway = VerdacaGatewayService()

    assert isinstance(gateway, GatewayPort)
