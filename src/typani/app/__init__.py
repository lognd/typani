"""The `typani` CLI application: AppConfig resolves settings, App runs them."""

from __future__ import annotations

from typani.app.app import App
from typani.app.config import AppConfig
from typani.app.errors import ConfigError

__all__ = ["App", "AppConfig", "ConfigError"]
