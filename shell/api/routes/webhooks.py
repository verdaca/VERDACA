"""Stripe webhook handler — arch §3.1.

POST /api/webhooks/stripe — Stripe webhook handler (sig-verified)

Binding anchors:
  - shell/architecture.md §3.1 Endpoint Specifications
  - shell/architecture.md §5.2 Billing Flow (webhook callbacks)
"""

from __future__ import annotations

from typing import Any

from api.billing import BillingService


class WebhookHandler:
    """Handles Stripe webhook events."""

    def __init__(self, billing: BillingService, webhook_secret: str) -> None:
        self._billing = billing
        self._webhook_secret = webhook_secret

    def handle(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        """Verify signature and dispatch event.

        Returns processed event data.
        Raises ValueError if signature is invalid.
        """
        event = self._billing.verify_webhook(
            payload, sig_header, self._webhook_secret
        )

        event_type = event.get("type", "")

        if event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(event)
        elif event_type == "payment_intent.payment_failed":
            return self._handle_payment_failed(event)

        return {"status": "ignored", "type": event_type}

    def _handle_payment_succeeded(self, event: dict) -> dict:
        return {
            "status": "processed",
            "type": "payment_intent.succeeded",
            "payment_intent_id": event.get("data", {}).get("object", {}).get("id"),
        }

    def _handle_payment_failed(self, event: dict) -> dict:
        return {
            "status": "processed",
            "type": "payment_intent.payment_failed",
            "payment_intent_id": event.get("data", {}).get("object", {}).get("id"),
        }
