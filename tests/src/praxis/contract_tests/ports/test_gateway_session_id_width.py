"""Stage 13 E2 gateway session-ID entropy-floor tests."""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

import pytest

from praxis.kernel.gateway.service import VerdacaGatewayService
from praxis.ports.gateway_dto import StartAnalysisRequest

ROOT = Path(__file__).resolve().parents[5]
SERVICE_PATH = (
    ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway" / "service.py"
)


def _gateway_intent(idempotency_key: str = "idem-1") -> StartAnalysisRequest:
    return StartAnalysisRequest(
        question="Which buyer path should we take?",
        requester_user_id="user-1",
        workspace_id="workspace-1",
        idempotency_key=idempotency_key,
    )


def _session_id_hexdigest_width() -> int:
    module = ast.parse(SERVICE_PATH.read_text(encoding="utf-8"), filename=str(SERVICE_PATH))
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == "_session_id":
            return _hexdigest_width(node)
    raise AssertionError("_session_id() not found in gateway service")


def _hexdigest_width(function: ast.FunctionDef) -> int:
    saw_hexdigest = False
    for node in ast.walk(function):
        if not _is_hexdigest_call(node):
            continue
        saw_hexdigest = True

    for node in ast.walk(function):
        if not isinstance(node, ast.Subscript):
            continue
        if not _is_hexdigest_call(node.value):
            continue
        if not isinstance(node.slice, ast.Slice):
            raise AssertionError("gateway _session_id() must not index a single hex char")
        if node.slice.upper is None:
            return 64
        if not isinstance(node.slice.upper, ast.Constant) or not isinstance(
            node.slice.upper.value,
            int,
        ):
            raise AssertionError(
                "gateway _session_id() hexdigest slice upper bound must be literal"
            )
        return node.slice.upper.value

    if saw_hexdigest:
        return 64
    raise AssertionError("gateway _session_id() must derive from sha256().hexdigest()")


def _is_hexdigest_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "hexdigest"
    )


def test_M_T_GATEWAY_SESSION_ID_WIDTH_01_hexdigest_slice_is_at_least_32_hex() -> None:
    assert _session_id_hexdigest_width() >= 32


@pytest.mark.no_waiver
def test_M_T_SESSION_ID_ENTROPY_FLOOR_01_gateway_session_id_uses_128_bit_floor() -> None:
    assert _session_id_hexdigest_width() >= 32


def test_M_T_GATEWAY_SESSION_ID_DETERMINISTIC_01_same_workspace_and_key_reuse_id() -> None:
    first = VerdacaGatewayService._session_id(_gateway_intent("idem-1"))
    second = VerdacaGatewayService._session_id(_gateway_intent("idem-1"))
    different = VerdacaGatewayService._session_id(_gateway_intent("idem-2"))

    assert first == second
    assert first != different
    assert re.fullmatch(r"gw-[0-9a-f]{32}", first), textwrap.shorten(first, width=80)
