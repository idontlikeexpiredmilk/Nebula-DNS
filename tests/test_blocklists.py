from pathlib import Path

from dnsserver.blocklist_manager import BlocklistManager


def test_blocklist_import_and_deduplication(tmp_path: Path) -> None:
    manager = BlocklistManager(storage_dir=tmp_path)
    entries = manager.import_from_lines(["ads.example.com", "ads.example.com", "tracker.example"])
    assert entries == ["ads.example.com", "tracker.example"]
    assert manager.deduplicate(["a", "a", "b"]) == ["a", "b"]
