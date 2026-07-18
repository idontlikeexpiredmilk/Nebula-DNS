# Developer Guide

## Running Tests

Use the following commands:

```bash
python -m pytest -q
```

## Adding a Plugin

Create a Python module under `plugins/` implementing a `Plugin`-compatible class and register it in your startup code.

## Extending the Rule Engine

Add new matching logic in `dnsserver/rules.py` and cover it with unit tests in `tests/`.
