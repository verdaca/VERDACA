"""Stage 11 H#1 expected-RED GatewayPort probe.

This file is intentionally RED until the Stage 11 Phase A gateway package lands.
"""


def test_gateway_port_contract_red_until_phase_a_impl() -> None:
    from praxis.kernel.gateway import GatewayPort  # noqa: F401
