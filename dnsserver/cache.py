from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    """A cached DNS response entry."""

    value: bytes
    expires_at: float
    created_at: float


class DNSCache:
    """A lightweight in-memory DNS cache with TTL support."""

    def __init__(self, max_entries: int = 10000, ttl_seconds: int = 60) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> bytes | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry.value

    def set(self, key: str, value: bytes) -> None:
        now = time.monotonic()
        self._entries[key] = CacheEntry(value=value, expires_at=now + self.ttl_seconds, created_at=now)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def stats(self) -> dict[str, Any]:
        return {
            "entries": len(self._entries),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl_seconds,
        }

    def clear(self) -> None:
        self._entries.clear()
