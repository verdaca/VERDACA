from __future__ import annotations

from typing import Any

import httpx

from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest


class SlackAdapter:
    API_VERSION = "1.0.0"

    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
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
            self.post_result(response_url, result)
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

    def post_result(self, response_url: str, result: AnalysisResult) -> None:
        client = self._http_client or httpx.Client(timeout=10.0)
        close_client = self._http_client is None
        try:
            response = client.post(response_url, json=self.result_to_block_kit(result))
            response.raise_for_status()
        finally:
            if close_client:
                client.close()
