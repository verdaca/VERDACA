"""LiteLLM virtual-key HTTP adapter."""

from __future__ import annotations

from typing import Any, cast

import httpx

from praxis.ports.virtual_key import (
    BudgetExhaustedError,
    VirtualKeyInfo,
    VirtualKeySpec,
)


class LiteLLMProxyError(Exception):
    """Raised when the LiteLLM proxy returns a non-2xx HTTP status."""

    def __init__(
        self,
        operation: str,
        status_code: int | None,
        detail: str | None = None,
    ) -> None:
        self.operation = operation
        self.status_code = status_code
        message = f"{operation} failed: {status_code}" if status_code is not None else operation
        if detail is not None:
            message = f"{message}: {detail}"
        super().__init__(message)


class LiteLLMVirtualKeyAdapter:
    """HTTP implementation of the virtual-key port against LiteLLM proxy routes."""

    def __init__(self, base_url: str, master_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {master_key}"}

    async def create_virtual_key(self, spec: VirtualKeySpec) -> VirtualKeyInfo:
        payload = {
            "key_alias": spec.key_alias,
            "max_budget": spec.max_budget,
            "max_parallel_requests": spec.max_parallel_requests,
            "models": spec.allowed_models,
            "duration": spec.duration,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/key/generate",
                json=payload,
                headers=self._headers,
                timeout=15.0,
            )
            self._raise_for_error("create_virtual_key", resp.status_code)
            data = cast(dict[str, Any], resp.json())
        token = data.get("key")
        if token is None:
            raise LiteLLMProxyError(
                "create_virtual_key",
                None,
                "LiteLLM response missing required field 'key'",
            )
        return VirtualKeyInfo(
            key_alias=spec.key_alias,
            token=str(token),
            spend=float(data.get("spend", 0.0)),
            max_budget=spec.max_budget,
            is_over_budget=False,
        )

    async def get_key_info(self, key_alias: str) -> VirtualKeyInfo:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/key/info",
                params={"key_alias": key_alias},
                headers=self._headers,
                timeout=10.0,
            )
            self._raise_for_error("get_key_info", resp.status_code)
            data = cast(dict[str, Any], resp.json())
        info = cast(dict[str, Any], data.get("info", {}))
        spend = float(info.get("spend", 0.0))
        max_budget = float(info.get("max_budget", 0.0))
        return VirtualKeyInfo(
            key_alias=key_alias,
            token=str(info.get("token", "")),
            spend=spend,
            max_budget=max_budget,
            is_over_budget=spend >= max_budget > 0,
        )

    async def check_budget(self, key_alias: str) -> None:
        info = await self.get_key_info(key_alias)
        if info.is_over_budget:
            raise BudgetExhaustedError(
                f"Virtual key {key_alias!r} exhausted: "
                f"spend={info.spend}, max_budget={info.max_budget}"
            )

    async def get_spend_logs(self, key_alias: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/spend/logs",
                params={"key_alias": key_alias},
                headers=self._headers,
                timeout=10.0,
            )
            self._raise_for_error("get_spend_logs", resp.status_code)
            data = resp.json()
        if isinstance(data, dict):
            return cast(list[dict[str, Any]], data.get("logs", []))
        return cast(list[dict[str, Any]], data)

    def _raise_for_error(self, operation: str, status_code: int) -> None:
        if status_code >= 400:
            raise LiteLLMProxyError(operation, status_code)


__all__ = ["LiteLLMProxyError", "LiteLLMVirtualKeyAdapter"]
