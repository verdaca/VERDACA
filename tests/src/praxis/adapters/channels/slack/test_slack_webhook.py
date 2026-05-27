from __future__ import annotations

import json

import pytest

from praxis.adapters.channels.slack.webhook import (
    REPLAY_WINDOW_SECONDS,
    ConfigurationError,
    WebhookResponse,
    load_signing_secret,
    receive_webhook,
    sign_body,
)


def _body(event_type: str = "event_callback") -> bytes:
    payload = (
        {"type": "url_verification", "challenge": "challenge-token"}
        if event_type == "url_verification"
        else {"type": "event_callback", "event": {"type": "app_mention", "text": "Run analysis"}}
    )
    return json.dumps(payload).encode("utf-8")


def _headers(
    body: bytes,
    *,
    timestamp: int,
    secret: str,
    signature: str | None = None,
) -> dict[str, str]:
    return {
        "X-Slack-Request-Timestamp": str(timestamp),
        "X-Slack-Signature": signature or sign_body(body, timestamp=str(timestamp), secret=secret),
    }


def test_M_T_SLACK_WEBHOOK_SIGNING_VALID_01_valid_signature_dispatches() -> None:
    body = _body()
    timestamp = 1_770_000_000
    dispatched: list[dict[str, object]] = []

    response = receive_webhook(
        body,
        _headers(body, timestamp=timestamp, secret="stage12-secret"),
        secret="stage12-secret",
        dispatch=lambda envelope: dispatched.append(dict(envelope))
        or WebhookResponse(status_code=200, payload={"ok": True}),
        now=timestamp,
    )

    assert response.status_code == 200
    assert response.payload == {"ok": True}
    assert dispatched == [
        {"type": "event_callback", "event": {"type": "app_mention", "text": "Run analysis"}}
    ]


@pytest.mark.no_waiver
def test_M_T_SLACK_WEBHOOK_SIGNING_TAMPERED_01_tampered_body_is_rejected() -> None:
    body = _body()
    tampered = json.dumps({"type": "event_callback", "event": {"type": "message"}}).encode("utf-8")
    timestamp = 1_770_000_000
    dispatched: list[dict[str, object]] = []

    response = receive_webhook(
        tampered,
        _headers(body, timestamp=timestamp, secret="stage12-secret"),
        secret="stage12-secret",
        dispatch=lambda envelope: dispatched.append(dict(envelope))
        or WebhookResponse(status_code=200, payload={"ok": True}),
        now=timestamp,
    )

    assert response.status_code == 401
    assert response.payload == {"error": "unauthorized"}
    assert dispatched == []


def test_M_T_SLACK_URL_VERIFICATION_01_returns_challenge_without_dispatching() -> None:
    body = _body("url_verification")
    timestamp = 1_770_000_000
    dispatched: list[dict[str, object]] = []

    response = receive_webhook(
        body,
        _headers(body, timestamp=timestamp, secret="stage12-secret"),
        secret="stage12-secret",
        dispatch=lambda envelope: dispatched.append(dict(envelope))
        or WebhookResponse(status_code=200, payload={"ok": True}),
        now=timestamp,
    )

    assert response.status_code == 200
    assert response.payload == {"challenge": "challenge-token"}
    assert dispatched == []


@pytest.mark.parametrize(
    ("age_seconds", "expected_status"),
    [
        (REPLAY_WINDOW_SECONDS - 1, 200),
        (REPLAY_WINDOW_SECONDS + 1, 401),
    ],
)
def test_M_T_SLACK_WEBHOOK_REPLAY_WINDOW_01_rejects_stale_timestamp(
    age_seconds: int,
    expected_status: int,
) -> None:
    body = _body()
    now = 1_770_000_000
    timestamp = now - age_seconds

    response = receive_webhook(
        body,
        _headers(body, timestamp=timestamp, secret="stage12-secret"),
        secret="stage12-secret",
        dispatch=lambda envelope: WebhookResponse(status_code=200, payload={"ok": True}),
        now=now,
    )

    assert response.status_code == expected_status


def test_M_T_SLACK_MISSING_SECRET_STARTUP_01_requires_env_secret() -> None:
    with pytest.raises(ConfigurationError, match="SLACK_SIGNING_SECRET"):
        load_signing_secret({})
