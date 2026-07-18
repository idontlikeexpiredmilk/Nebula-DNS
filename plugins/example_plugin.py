from __future__ import annotations


class ExamplePlugin:
    """Example plugin that can be extended for analytics or notifications."""

    name = "example"

    def initialize(self) -> None:
        print("Example plugin initialized")
