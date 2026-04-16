"""Billing logic — arch §5.1–§5.5.

Stripe PaymentIntent creation, trial consumption, webhook handling.

Binding anchors:
  - shell/architecture.md §5.1 Stripe Product Catalog
  - shell/architecture.md §5.2 Billing Flow
  - shell/architecture.md §5.5 Trial Mechanics
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class BillingError(Exception):
    """Raised when a billing operation fails."""

    def __init__(self, code: str, message: str, status_code: int = 402) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@runtime_checkable
class StripeClientProtocol(Protocol):
    """Interface for Stripe operations."""

    async def create_payment_intent(
        self, *, amount: int, currency: str, customer: str
    ) -> dict[str, Any]: ...

    def verify_webhook_signature(
        self, payload: bytes, sig_header: str, secret: str
    ) -> dict[str, Any]: ...


# Price constants per arch §5.1 (Victor 7.0.1)
PRICE_QUICK_CENTS = 2900   # $29
PRICE_DEEP_CENTS = 14900   # $149


def session_price_cents(depth: str) -> int:
    """Return the price in cents for the given session depth."""
    if depth == "quick":
        return PRICE_QUICK_CENTS
    return PRICE_DEEP_CENTS


@dataclass
class WorkspaceBillingState:
    """Minimal billing state for a workspace."""

    trial_used: bool
    stripe_customer_id: str | None


class BillingService:
    """Handles billing decisions per arch §5.2 flow."""

    def __init__(self, stripe: StripeClientProtocol) -> None:
        self._stripe = stripe

    async def authorize_session(
        self,
        *,
        workspace_billing: WorkspaceBillingState,
        depth: str,
    ) -> dict[str, Any]:
        """Check billing for a session start.

        Returns:
            dict with "payment_type" ("trial" | "paid") and optional
            "payment_intent_id".

        Raises:
            BillingError if payment fails.
        """
        if not workspace_billing.trial_used:
            return {"payment_type": "trial", "payment_intent_id": None}

        if not workspace_billing.stripe_customer_id:
            raise BillingError(
                code="NO_PAYMENT_METHOD",
                message="No payment method on file. Please connect billing.",
                status_code=402,
            )

        amount = session_price_cents(depth)
        intent = await self._stripe.create_payment_intent(
            amount=amount,
            currency="usd",
            customer=workspace_billing.stripe_customer_id,
        )

        if intent.get("status") != "succeeded":
            raise BillingError(
                code="PAYMENT_FAILED",
                message="Payment failed. Session not started.",
                status_code=402,
            )

        return {
            "payment_type": "paid",
            "payment_intent_id": intent["id"],
        }

    def verify_webhook(
        self, payload: bytes, sig_header: str, secret: str
    ) -> dict[str, Any]:
        """Verify and parse a Stripe webhook event.

        Raises ValueError if signature is invalid.
        """
        return self._stripe.verify_webhook_signature(payload, sig_header, secret)
