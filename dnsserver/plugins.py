from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Protocol


class Plugin(Protocol):
    """A minimal plugin interface."""

    name: str

    def initialize(self) -> None:
        ...


class PluginManager:
    """Discover and initialize plugins from the plugins package."""

    def __init__(self, package_name: str = "plugins") -> None:
        self.package_name = package_name

    def discover(self) -> list[Plugin]:
        plugins: list[Plugin] = []
        package = importlib.import_module(self.package_name)
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{self.package_name}.{module_name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj is not Plugin and hasattr(obj, "name") and hasattr(obj, "initialize"):
                    plugins.append(obj())
        return plugins
