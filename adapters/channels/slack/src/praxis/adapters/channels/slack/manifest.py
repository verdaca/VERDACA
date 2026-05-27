from __future__ import annotations

BOT_EVENTS: tuple[str, ...] = ("app_mention",)
SCOPES: tuple[str, ...] = ("app_mentions:read", "chat:write")


def manifest_template() -> dict[str, object]:
    return {
        "event_subscriptions": {"bot_events": list(BOT_EVENTS)},
        "oauth_config": {"scopes": {"bot": list(SCOPES)}},
    }
