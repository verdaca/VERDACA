"""Stage 12 H#4 MAC-Ts for LiteLLM virtual-key HTTP adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from praxis.adapters.litellm.virtual_keys import LiteLLMProxyError, LiteLLMVirtualKeyAdapter
from praxis.ports.virtual_key import BudgetExhaustedError, VirtualKeySpec

CASSETTES_DIR = Path(__file__).parents[4] / "fixtures" / "vcr_cassettes"
BASE_URL = "https://litellm.example.invalid"
MASTER_KEY = "test-master-key"


class _HttpResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._payload


class _QueuedAsyncClient:
    def __init__(self, responses: list[_HttpResponse]) -> None:
        self._responses = responses
        self.requests: list[dict[str, Any]] = []

    async def __aenter__(self) -> _QueuedAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, **kwargs: object) -> _HttpResponse:
        self.requests.append({"method": "POST", "url": url, **kwargs})
        return self._responses.pop(0)

    async def get(self, url: str, **kwargs: object) -> _HttpResponse:
        self.requests.append({"method": "GET", "url": url, **kwargs})
        return self._responses.pop(0)


def _response_from_cassette(name: str) -> _HttpResponse:
    cassette = yaml.safe_load((CASSETTES_DIR / name).read_text(encoding="utf-8"))
    response = cassette["interactions"][0]["response"]
    body = response["body"]["string"]
    loaded = json.loads(body)
    assert isinstance(loaded, (dict, list))
    return _HttpResponse(status_code=int(response["status"]["code"]), payload=loaded)


def _adapter_with_client(
    monkeypatch: pytest.MonkeyPatch,
    client: _QueuedAsyncClient,
) -> LiteLLMVirtualKeyAdapter:
    monkeypatch.setattr("praxis.adapters.litellm.virtual_keys.httpx.AsyncClient", lambda: client)
    return LiteLLMVirtualKeyAdapter(base_url=BASE_URL, master_key=MASTER_KEY)


def _spec() -> VirtualKeySpec:
    return VirtualKeySpec(
        key_alias="stage12-key",
        max_budget=25.0,
        max_parallel_requests=4,
        allowed_models=["gpt-4o"],
        duration="24h",
    )


@pytest.mark.asyncio
async def test_M_T_VKEY_CREATE_HAPPY_01_returns_virtual_key_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_response_from_cassette("litellm_key_generate.yaml")])
    adapter = _adapter_with_client(monkeypatch, client)

    info = await adapter.create_virtual_key(_spec())

    assert info.key_alias == "stage12-key"
    assert info.token == "sk-stage12-generated"
    assert info.spend == 0.0
    assert info.max_budget == 25.0
    assert info.is_over_budget is False
    assert client.requests[0]["method"] == "POST"
    assert client.requests[0]["url"] == f"{BASE_URL}/key/generate"
    assert client.requests[0]["headers"] == {"Authorization": f"Bearer {MASTER_KEY}"}
    assert client.requests[0]["json"] == {
        "key_alias": "stage12-key",
        "max_budget": 25.0,
        "max_parallel_requests": 4,
        "models": ["gpt-4o"],
        "duration": "24h",
    }


@pytest.mark.asyncio
async def test_M_T_VKEY_CREATE_MISSING_KEY_01_raises_proxy_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_HttpResponse(status_code=200, payload={"spend": 0.0})])
    adapter = _adapter_with_client(monkeypatch, client)

    with pytest.raises(LiteLLMProxyError) as exc_info:
        await adapter.create_virtual_key(_spec())

    assert exc_info.value.operation == "create_virtual_key"
    assert exc_info.value.status_code is None
    assert "missing required field 'key'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_M_T_VKEY_INFO_HAPPY_01_parses_spend_and_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_response_from_cassette("litellm_key_info.yaml")])
    adapter = _adapter_with_client(monkeypatch, client)

    info = await adapter.get_key_info("stage12-key")

    assert info.key_alias == "stage12-key"
    assert info.token == "sk-stage12-existing"
    assert info.spend == 7.5
    assert info.max_budget == 25.0
    assert info.is_over_budget is False
    assert client.requests[0]["url"] == f"{BASE_URL}/key/list"
    assert client.requests[0]["params"] == {
        "key_alias": "stage12-key",
        "return_full_object": "true",
    }


@pytest.mark.asyncio
async def test_M_T_VKEY_INFO_NOT_FOUND_01_raises_when_alias_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_HttpResponse(status_code=200, payload={"keys": []})])
    adapter = _adapter_with_client(monkeypatch, client)

    with pytest.raises(LiteLLMProxyError) as exc_info:
        await adapter.get_key_info("absent-alias")

    assert exc_info.value.operation == "get_key_info"
    assert exc_info.value.status_code is None
    assert "no virtual key with alias" in str(exc_info.value)


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_VKEY_BUDGET_EXHAUSTED_01_check_budget_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_response_from_cassette("litellm_key_info_exhausted.yaml")])
    adapter = _adapter_with_client(monkeypatch, client)

    with pytest.raises(BudgetExhaustedError):
        await adapter.check_budget("stage12-key")


@pytest.mark.asyncio
async def test_M_T_VKEY_SPEND_LOGS_PARSE_01_returns_request_spend_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_response_from_cassette("litellm_spend_logs.yaml")])
    adapter = _adapter_with_client(monkeypatch, client)

    logs = await adapter.get_spend_logs("stage12-key")

    assert logs == [
        {"request_id": "req-001", "spend": 0.12},
        {"request_id": "req-002", "spend": 0.34},
    ]
    assert client.requests[0]["url"] == f"{BASE_URL}/spend/logs"


@pytest.mark.asyncio
async def test_M_T_VKEY_HTTP_ERROR_PROPAGATION_01_raises_proxy_error_with_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _QueuedAsyncClient([_response_from_cassette("litellm_key_info_500.yaml")])
    adapter = _adapter_with_client(monkeypatch, client)

    with pytest.raises(LiteLLMProxyError) as exc_info:
        await adapter.get_key_info("stage12-key")

    assert exc_info.value.operation == "get_key_info"
    assert exc_info.value.status_code == 500
