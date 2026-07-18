# Lightweight DNS Filtering Server

A production-quality, from-scratch DNS filtering server written in Python 3.12+ for Raspberry Pi Zero 2 W and newer Raspberry Pi devices.

## Features

- Async DNS server with UDP and optional TCP support
- Recursive forwarding to upstream resolvers
- In-memory caching with TTL support
- Rule engine with exact, wildcard, regex, allowlist, denylist, and per-client rules
- Modern dashboard and REST API
- Plugin architecture
- Secure defaults and structured logging

## Project Layout

- dnsserver/: core server, DNS protocol, config, and runtime
- dashboard/: web dashboard and templates
- api/: REST API handlers
- database/: persistence helpers
- plugins/: plugin entry points
- blocklists/: blocklist import and management
- logs/: runtime logs
- config/: configuration files
- tests/: unit tests
- docs/: reference documentation

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `config/config.yaml.example` to `config/config.yaml` and adjust settings.
4. Run the server: `python -m dnsserver.main`

## Design Notes

This project is intentionally written from scratch and does not copy or reuse Pi-hole source code. It is designed for modularity, low memory usage, and straightforward extensibility.
