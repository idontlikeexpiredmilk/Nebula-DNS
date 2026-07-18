"""Blocklist management package."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class BlocklistManager:
    """Simple, extensible blocklist manager for local and remote sources."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self.storage_dir = Path(storage_dir or "blocklists")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def import_from_file(self, path: str | Path) -> list[str]:
        entries = Path(path).read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in entries if line.strip() and not line.startswith("#")]

    def import_from_url(self, url: str) -> list[str]:
        return [line.strip() for line in url.splitlines() if line.strip() and not line.startswith("#")]

    def deduplicate(self, entries: list[str]) -> list[str]:
        return list(dict.fromkeys(entries))

    def save(self, name: str, entries: list[str]) -> None:
        target = self.storage_dir / name
        target.write_text("\n".join(entries), encoding="utf-8")

    def load(self, name: str) -> list[str]:
        target = self.storage_dir / name
        if not target.exists():
            return []
        return target.read_text(encoding="utf-8").splitlines()
