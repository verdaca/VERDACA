from __future__ import annotations

import asyncio
from typing import Any

import httpx

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class SlackAdapter:
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
        response_url = (intent.metadata or {}).get("response_url")
        if self._post_results and response_url:
            self._dispatch_post_result(response_url, result)
        return result

    def result_to_block_kit(self, result: AnalysisResult) -> dict[str, Any]:
        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": result.recommendation},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Session `{result.session.session_id}` · {result.session.status}",
                    }
                ],
            },
        ]
        if result.cited_tradeoffs:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "\n".join(result.cited_tradeoffs)},
                }
            )
        return {"blocks": blocks}

    async def post_result(self, response_url: str, result: AnalysisResult) -> None:
        if self._http_client is not None:
            response = await self._http_client.post(
                response_url,
                json=self.result_to_block_kit(result),
            )
            response.raise_for_status()
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(response_url, json=self.result_to_block_kit(result))
            response.raise_for_status()

    def _dispatch_post_result(self, response_url: str, result: AnalysisResult) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.post_result(response_url, result))
            return
        loop.create_task(self.post_result(response_url, result))
