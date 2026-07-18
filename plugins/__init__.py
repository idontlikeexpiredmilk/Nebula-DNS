"""Plugin system entry points."""

from typing import Protocol


class Plugin(Protocol):
    """Base protocol for simple plugins."""

    name: str

    def initialize(self) -> None:
        ...
