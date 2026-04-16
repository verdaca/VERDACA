"""Shell configuration — arch §12.3.

All secrets come from environment variables. No defaults for secrets.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/praxis"

    # Clerk
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwks_url: str = "https://api.clerk.com/.well-known/jwks.json"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_quick: int = 2900  # cents
    stripe_price_deep: int = 14900  # cents

    # Anthropic (production engine only)
    anthropic_api_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    # App
    debug: bool = False
    public_dashboard_min_sessions: int = 10

    model_config = {"env_prefix": "PRAXIS_"}
