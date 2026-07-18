from __future__ import annotations

from pathlib import Path
from typing import Iterable


class BlocklistManager:
    """Manage blocklist entries with import, deduplication, and persistence."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self.storage_dir = Path(storage_dir or "blocklists")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def import_from_lines(self, lines: Iterable[str]) -> list[str]:
        entries: list[str] = []
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            entries.append(line)
        return self.deduplicate(entries)

    def import_from_file(self, path: str | Path) -> list[str]:
        return self.import_from_lines(Path(path).read_text(encoding="utf-8").splitlines())

    def deduplicate(self, entries: Iterable[str]) -> list[str]:
        return list(dict.fromkeys(entries))

    def save(self, name: str, entries: Iterable[str]) -> Path:
        target = self.storage_dir / name
        cleaned = self.deduplicate(entries)
        target.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
        return target

    def load(self, name: str) -> list[str]:
        target = self.storage_dir / name
        if not target.exists():
            return []
        return [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
