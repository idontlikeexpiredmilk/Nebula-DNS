# Plugin Guide

Plugins should implement a small initialization interface and can register hooks for logging, analytics, or notifications.

## Example

```python
from plugins import Plugin

class ExamplePlugin:
    name = "example"

    def initialize(self) -> None:
        print("Plugin initialized")
```
