from __future__ import annotations

import ipaddress
import logging
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RuleResult:
    """Outcome of evaluating a DNS query against rules."""

    blocked: bool
    reason: str | None = None
    matched_rule: str | None = None


@dataclass(slots=True)
class RuleEngine:
    """Small rule engine supporting exact, wildcard, regex, allowlists, and denylist rules."""

    allowlist: list[str] = field(default_factory=list)
    denylist: list[str] = field(default_factory=list)
    per_client_rules: dict[str, list[str]] = field(default_factory=dict)
    enable_regex: bool = True

    def evaluate(self, name: str, client_ip: str | None = None) -> RuleResult:
        r"""
        Evaluate a domain name against the rule engine.
        
        Evaluation order:
        1. Per-client rules (highest priority)
        2. Allowlist (exemptions)
        3. Denylist (blocks - including both manual and imported blocklist entries)
        
        Args:
            name: The domain name to evaluate
            client_ip: Optional client IP for per-client rules
            
        Returns:
            RuleResult with blocked status and matching rule details
        """
        logger = logging.getLogger("dnsserver")
        normalized = name.lower().rstrip(".")
        
        if client_ip is not None:
            try:
                ipaddress.ip_address(client_ip)
            except ValueError:
                client_ip = None

        # Check per-client rules first (highest priority)
        if client_ip and client_ip in self.per_client_rules:
            for rule in self.per_client_rules[client_ip]:
                if self._match_rule(normalized, rule):
                    logger.debug(f"Domain {normalized} blocked by per-client rule '{rule}' for {client_ip}")
                    return RuleResult(blocked=True, reason="per-client", matched_rule=rule)

        # Check allowlist (exemptions take precedence over denylist)
        for rule in self.allowlist:
            if self._match_rule(normalized, rule):
                logger.debug(f"Domain {normalized} allowed by allowlist rule '{rule}'")
                return RuleResult(blocked=False, reason="allowlisted", matched_rule=rule)

        # Check denylist (manual rules + imported blocklists)
        for rule in self.denylist:
            if self._match_rule(normalized, rule):
                logger.debug(f"Domain {normalized} blocked by denylist rule '{rule}'")
                return RuleResult(blocked=True, reason="denylisted", matched_rule=rule)

        # No rules matched
        return RuleResult(blocked=False)

    def _match_rule(self, name: str, pattern: str) -> bool:
        r"""
        Match a domain against a rule pattern (exact, wildcard, regex, or subdomain).
        
        Supports:
        - Exact match: "example.com" matches only "example.com"
        - Subdomain match: "example.com" matches "example.com" AND "ads.example.com"
        - Wildcard: "*.ads.example.com" matches only subdomains under "ads.example.com"
        - Regex: "(^|\.)ads\..*" matches regex patterns (when enable_regex=True)
        
        Args:
            name: The normalized domain name
            pattern: The rule pattern
            
        Returns:
            True if the domain matches the pattern
        """
        pattern = pattern.strip().lower()
        if not pattern:
            return False
        
        # Regex rules start with (
        if self.enable_regex and pattern.startswith("("):
            try:
                return bool(re.search(pattern, name))
            except re.error:
                return False
        
        # Wildcard rules with *
        if "*" in pattern:
            regex = re.escape(pattern).replace(r"\*", ".*") + "$"
            return bool(re.match(regex, name))
        
        # Exact match OR subdomain match
        # e.g., pattern "google.com" matches "google.com" AND "ads.google.com"
        if name == pattern or name.endswith("." + pattern):
            return True
        
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowlist": self.allowlist,
            "denylist": self.denylist,
            "per_client_rules": self.per_client_rules,
            "enable_regex": self.enable_regex,
        }
