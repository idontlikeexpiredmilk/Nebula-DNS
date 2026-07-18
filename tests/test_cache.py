import time

import pytest

from dnsserver.cache import DNSCache


class TestDNSCache:
    """Tests for the DNS cache."""

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = DNSCache(max_entries=100, ttl_seconds=60)
        cache.set("google.com", b"response_data")
        assert cache.get("google.com") == b"response_data"

    def test_cache_miss(self):
        """Test that cache returns None for missing keys."""
        cache = DNSCache(max_entries=100, ttl_seconds=60)
        assert cache.get("missing.com") is None

    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        cache = DNSCache(max_entries=100, ttl_seconds=1)
        cache.set("example.com", b"data")
        assert cache.get("example.com") is not None
        time.sleep(1.1)
        assert cache.get("example.com") is None

    def test_cache_max_entries(self):
        """Test that cache respects max_entries limit."""
        cache = DNSCache(max_entries=3, ttl_seconds=60)
        cache.set("a.com", b"a")
        cache.set("b.com", b"b")
        cache.set("c.com", b"c")
        cache.set("d.com", b"d")  # This should evict the oldest entry

        assert cache.get("a.com") is None  # Oldest entry should be gone
        assert cache.get("d.com") == b"d"

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = DNSCache(max_entries=100, ttl_seconds=60)
        cache.set("test.com", b"data")
        stats = cache.stats()

        assert stats["entries"] == 1
        assert stats["max_entries"] == 100
        assert stats["ttl_seconds"] == 60

    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = DNSCache(max_entries=100, ttl_seconds=60)
        cache.set("test1.com", b"data1")
        cache.set("test2.com", b"data2")
        cache.clear()

        assert cache.get("test1.com") is None
        assert cache.get("test2.com") is None
