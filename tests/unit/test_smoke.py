"""P0 scaffold smoke tests: package imports and settings load cleanly."""

from __future__ import annotations

import turtle_insight
from turtle_insight.config.settings import Settings, get_settings


def test_package_has_version() -> None:
    assert turtle_insight.__version__ == "0.1.0"


def test_settings_construct_with_defaults() -> None:
    # Ignore any local .env so the test is environment-robust.
    s = Settings(_env_file=None)
    assert isinstance(s.ti_db_url, str) and s.ti_db_url
    # Model identifiers are not hardcoded: absent unless provided via env.
    assert s.ti_deep_model is None or isinstance(s.ti_deep_model, str)


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
