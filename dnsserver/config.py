from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded."""


class Config:
    """Simple configuration container with safe defaults."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("DNS_SERVER_CONFIG", "config/config.yaml"))
        self.data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            raise ConfigError(f"Configuration file not found: {self.path}")

        with self.path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}

        if not isinstance(loaded, dict):
            raise ConfigError("Configuration root must be a mapping")

        self.data = loaded

    @property
    def server(self) -> dict[str, Any]:
        return self.data.get("server", {})

    @property
    def upstream(self) -> dict[str, Any]:
        return self.data.get("upstream", {})

    @property
    def cache(self) -> dict[str, Any]:
        return self.data.get("cache", {})

    @property
    def rules(self) -> dict[str, Any]:
        return self.data.get("rules", {})

    @property
    def logging(self) -> dict[str, Any]:
        return self.data.get("logging", {})

    @property
    def dashboard(self) -> dict[str, Any]:
        return self.data.get("dashboard", {})

    @property
    def security(self) -> dict[str, Any]:
        return self.data.get("security", {})
