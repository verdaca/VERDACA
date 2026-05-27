from __future__ import annotations

BOT_ID_ENV = "TEAMS_BOT_ID"
SCOPES: tuple[str, ...] = ("team", "personal")
SUPPORTS_FILES = False


def manifest_template(*, bot_id: str) -> dict[str, object]:
    return {
        "bots": [
            {
                "botId": bot_id,
                "scopes": list(SCOPES),
                "supportsFiles": SUPPORTS_FILES,
            }
        ],
        "permissions": ["identity", "messageTeamMembers"],
    }
