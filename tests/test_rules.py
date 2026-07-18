import pytest

from dnsserver.rules import RuleEngine, RuleResult


class TestRuleEngine:
    """Tests for the DNS rule engine."""

    def test_allow_all_by_default(self):
        """Test that queries are allowed by default."""
        engine = RuleEngine()
        result = engine.evaluate("google.com")
        assert result.blocked is False

    def test_exact_match_denylist(self):
        """Test exact match on denylist."""
        engine = RuleEngine(denylist=["ads.example.com"])
        result = engine.evaluate("ads.example.com")
        assert result.blocked is True
        assert result.reason == "denylisted"

    def test_exact_match_allowlist_override(self):
        """Test that allowlist takes precedence over denylist."""
        engine = RuleEngine(allowlist=["ads.example.com"], denylist=["ads.example.com"])
        result = engine.evaluate("ads.example.com")
        assert result.blocked is False
        assert result.reason == "allowlisted"

    def test_wildcard_match(self):
        """Test wildcard pattern matching."""
        engine = RuleEngine(denylist=["*.ads.example.com"])
        assert engine.evaluate("tracker.ads.example.com").blocked is True
        assert engine.evaluate("ads.example.com").blocked is False

    def test_regex_match(self):
        """Test regex pattern matching."""
        engine = RuleEngine(denylist=["(ad|tracker).*\\.example\\.com"], enable_regex=True)
        assert engine.evaluate("ads.example.com").blocked is True
        assert engine.evaluate("tracker.example.com").blocked is True
        assert engine.evaluate("example.com").blocked is False

    def test_regex_disabled(self):
        """Test that regex is ignored when disabled."""
        engine = RuleEngine(denylist=["(ad|tracker).*"], enable_regex=False)
        result = engine.evaluate("ads.example.com")
        assert result.blocked is False  # Regex pattern not treated as regex

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        engine = RuleEngine(denylist=["ADS.EXAMPLE.COM"])
        result = engine.evaluate("ads.example.com")
        assert result.blocked is True

    def test_per_client_rules(self):
        """Test per-client rule precedence."""
        engine = RuleEngine(
            denylist=["ads.com"],
            per_client_rules={"192.168.1.100": ["google.com"]},
        )
        # Client-specific rule takes precedence
        result = engine.evaluate("google.com", "192.168.1.100")
        assert result.blocked is True
        assert result.reason == "per-client"

        # Other clients see default rules
        result = engine.evaluate("google.com", "192.168.1.101")
        assert result.blocked is False

    def test_trailing_dot_handling(self):
        """Test that trailing dots are handled correctly."""
        engine = RuleEngine(denylist=["example.com"])
        assert engine.evaluate("example.com").blocked is True
        assert engine.evaluate("example.com.").blocked is True

    def test_invalid_ip_address(self):
        """Test that invalid IP addresses don't crash per-client matching."""
        engine = RuleEngine(per_client_rules={"invalid-ip": ["ads.com"]})
        result = engine.evaluate("ads.com", "invalid-ip")
        # Should not match per-client rule due to invalid IP
        assert result.blocked is False
