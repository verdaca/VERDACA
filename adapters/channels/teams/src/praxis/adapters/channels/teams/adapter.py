from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class TeamsAdapter:
    API_VERSION = "1.0.0"

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        post_results: bool = False,
    ) -> None:
        self._http_client = http_client
        self._post_results = post_results

    def execute(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        gateway: GatewayPort,
    ) -> AnalysisResult:
        result = gateway.execute(intent, ctx)
        callback_url = (intent.metadata or {}).get("service_url")
        if self._post_results and callback_url:
            self._dispatch_post_result(callback_url, result)
        return result

    def result_to_adaptive_card(self, result: AnalysisResult) -> dict[str, Any]:
        facts: list[dict[str, str]] = [
            {"title": "Session", "value": result.session.session_id},
            {"title": "Status", "value": result.session.status},
        ]
        if result.cost_usd is not None:
            facts.append({"title": "Cost USD", "value": str(result.cost_usd)})

        body: list[Mapping[str, Any]] = [
            {
                "type": "TextBlock",
                "text": result.recommendation,
                "wrap": True,
            },
            {
                "type": "FactSet",
                "facts": facts,
            },
        ]
        if result.cited_tradeoffs:
            body.append(
                {
                    "type": "TextBlock",
                    "text": "\n".join(result.cited_tradeoffs),
                    "wrap": True,
                }
            )

        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": body,
        }

    async def post_result(self, callback_url: str, result: AnalysisResult) -> None:
        if self._http_client is not None:
            response = await self._http_client.post(
                callback_url,
                json=self.result_to_adaptive_card(result),
            )
            response.raise_for_status()
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=self.result_to_adaptive_card(result))
            response.raise_for_status()

    def _dispatch_post_result(self, callback_url: str, result: AnalysisResult) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.post_result(callback_url, result))
            return
        loop.create_task(self.post_result(callback_url, result))
