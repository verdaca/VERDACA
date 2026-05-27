from __future__ import annotations

import hmac
import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


SIGNATURE_HEADER = "x-slack-signature"
TIMESTAMP_HEADER = "x-slack-request-timestamp"
REPLAY_WINDOW_SECONDS = 300
SIGNATURE_VERSION = "v0"


class ConfigurationError(RuntimeError):
    """Raised when the Slack webhook cannot be constructed."""


class WebhookAuthError(ValueError):
    """Raised when a Slack webhook request fails authentication."""


@dataclass(frozen=True, slots=True)
class WebhookResponse:
    status_code: int
    payload: Mapping[str, Any]


def load_signing_secret(env: Mapping[str, str] | None = None) -> str:
    source = os.environ if env is None else env
    secret = source.get("SLACK_SIGNING_SECRET")
    if not secret:
        raise ConfigurationError("SLACK_SIGNING_SECRET is required")
    return secret


def sign_body(body: bytes, *, timestamp: str, secret: str) -> str:
    base = SIGNATURE_VERSION.encode("utf-8") + b":" + timestamp.encode("utf-8") + b":" + body
    digest = hmac.new(secret.encode("utf-8"), base, sha256).hexdigest()
    return f"{SIGNATURE_VERSION}={digest}"


def verify_signature(
    body: bytes,
    *,
    timestamp: str,
    signature: str,
    secret: str,
    now: float | None = None,
) -> None:
    try:
        request_time = int(timestamp)
    except ValueError as exc:
        raise WebhookAuthError("Invalid Slack webhook timestamp") from exc

    current_time = int(time.time() if now is None else now)
    if abs(current_time - request_time) > REPLAY_WINDOW_SECONDS:
        raise WebhookAuthError("Slack webhook timestamp outside replay window")

    expected = sign_body(body, timestamp=timestamp, secret=secret)
    if not hmac.compare_digest(expected, signature):
        raise WebhookAuthError("Invalid Slack webhook signature")


def receive_webhook(
    body: bytes,
    headers: Mapping[str, str],
    *,
    secret: str,
    dispatch: Callable[[Mapping[str, Any]], WebhookResponse],
    now: float | None = None,
) -> WebhookResponse:
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    try:
        timestamp = normalized_headers[TIMESTAMP_HEADER]
        signature = normalized_headers[SIGNATURE_HEADER]
        verify_signature(body, timestamp=timestamp, signature=signature, secret=secret, now=now)
    except (KeyError, WebhookAuthError):
        return WebhookResponse(status_code=401, payload={"error": "unauthorized"})

    envelope = json.loads(body.decode("utf-8"))
    if envelope.get("type") == "url_verification":
        return WebhookResponse(status_code=200, payload={"challenge": envelope.get("challenge", "")})
    return dispatch(envelope)
