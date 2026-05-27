from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class TeamsAdapter:
    API_VERSION = "1.0.0"

    def __init__(self, *, http_client: httpx.Client | None = None, post_results: bool = False) -> None:
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
            self.post_result(callback_url, result)
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

    def post_result(self, callback_url: str, result: AnalysisResult) -> None:
        client = self._http_client or httpx.Client(timeout=10.0)
        close_client = self._http_client is None
        try:
            response = client.post(callback_url, json=self.result_to_adaptive_card(result))
            response.raise_for_status()
        finally:
            if close_client:
                client.close()
