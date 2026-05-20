"""Config tests — verify settings load with defaults."""

from __future__ import annotations

import pytest

from api.config import Settings


class TestSettings:

    def test_default_settings(self):
        """Settings instantiates with defaults."""
        s = Settings()
        assert s.debug is False
        assert s.public_dashboard_min_sessions == 10
        assert s.stripe_price_quick == 2900
        assert s.stripe_price_deep == 14900

    def test_database_url_default(self):
        """Default database URL is set."""
        s = Settings()
        assert "postgresql" in s.database_url

    def test_empty_secrets_by_default(self):
        """Secrets default to empty string (not None)."""
        s = Settings()
        assert s.clerk_secret_key == ""
        assert s.stripe_secret_key == ""
        assert s.sentry_dsn == ""
