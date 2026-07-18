# Architecture Overview

The project uses a layered design:

1. Configuration and startup: load config, initialize logging, and create services.
2. DNS runtime: receive queries, evaluate rules, use caching, and forward to upstream resolvers.
3. Monitoring layer: expose a REST API and a simple web dashboard.
4. Extensions: plugin hooks and blocklist management for future expansion.

## Components

- DNS server: asynchronous UDP/TCP handling with rule evaluation and caching.
- Rule engine: exact, wildcard, regex, allowlist, denylist, and per-client rules.
- Cache: low-overhead in-memory TTL storage.
- Dashboard/API: lightweight monitoring endpoints.
- Blocklist manager: import and deduplicate rules from local files and URLs.
