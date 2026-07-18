from __future__ import annotations
import asyncio
import logging
import socket
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from .blocklist_manager import BlocklistManager
from .cache import DNSCache
from .config import Config
from .plugins import PluginManager
from .protocol import DNSMessage
from .rules import RuleEngine

@dataclass(slots=True)
class Stats:
    requests: int = 0
    blocked: int = 0
    allowed: int = 0
    cache_hits: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "blocked": self.blocked,
            "allowed": self.allowed,
            "cache_hits": self.cache_hits,
        }

@dataclass(slots=True)
class ServerState:
    stats: Stats = field(default_factory=Stats)
    logs: list[dict[str, Any]] = field(default_factory=list)
    clients: Counter[str] = field(default_factory=Counter)
    domains: Counter[str] = field(default_factory=Counter)
    max_logs: int = 1000 

class DNSServer:
    """A simple asynchronous DNS server with caching and rule enforcement."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = logging.getLogger("dnsserver")
        self.cache = DNSCache(
            max_entries=int(self.config.cache.get("max_entries", 10000)),
            ttl_seconds=int(self.config.cache.get("ttl_seconds", 60)),
        )
        
        # Initialize rule engine with config values
        self.rule_engine = RuleEngine(
            allowlist=list(self.config.rules.get("allowlist", [])),
            denylist=list(self.config.rules.get("denylist", [])),
            per_client_rules={k: list(v) for k, v in self.config.rules.get("per_client_rules", {}).items()},
            enable_regex=bool(self.config.rules.get("enable_regex", True)),
        )
        
        self.state = ServerState()
        self.blocklist_manager = BlocklistManager(storage_dir="blocklists")
        self.plugin_manager = PluginManager(package_name="plugins")
        self._upstream = list(self.config.upstream.get("servers", ["1.1.1.1"]))
        self._upstream_index = 0
        self._running = False
        self._plugins = []

        # Log initial rule configuration
        self.logger.info("Rule engine initialized:")
        self.logger.info(f"  - Manual denylist entries: {len(self.rule_engine.denylist)}")
        self.logger.info(f"  - Manual allowlist entries: {len(self.rule_engine.allowlist)}")
        self.logger.info(f"  - Per-client rules: {len(self.rule_engine.per_client_rules)}")
        self.logger.info(f"  - Regex enabled: {self.rule_engine.enable_regex}")

        # Load blocklist file BEFORE query processing (extends denylist)
        blocklist_path = self.config.rules.get("blocklist_path", "blocklists/adlists.txt")
        if blocklist_path:
            self._load_blocklist(blocklist_path)

    def _load_blocklist(self, blocklist_path: str) -> None:
        """Load external blocklist file and add entries to denylist."""
        try:
            path = Path(blocklist_path)
            if path.exists():
                loaded_domains = self.blocklist_manager.import_from_file(blocklist_path)
                if loaded_domains:
                    initial_denylist_count = len(self.rule_engine.denylist)
                    self.rule_engine.denylist.extend(loaded_domains)
                    
                    self.logger.info(
                        f"Successfully loaded {len(loaded_domains)} domains from blocklist: {blocklist_path}"
                    )
                    self.logger.info(
                        f"  - Denylist total: {initial_denylist_count} manual + {len(loaded_domains)} imported = "
                        f"{len(self.rule_engine.denylist)} total"
                    )
                else:
                    self.logger.warning(f"Blocklist file '{blocklist_path}' is empty")
            else:
                self.logger.warning(f"Blocklist file not found at: {blocklist_path}")
        except Exception as e:
            self.logger.error(f"Failed to load blocklist from '{blocklist_path}': {e}")

    async def start(self) -> None:
        self._running = True
        host = str(self.config.server.get("host", "0.0.0.0"))
        udp_port = int(self.config.server.get("udp_port", 5353))
        self.logger.info("Starting DNS server on %s:%s", host, udp_port)
        self._plugins = self.plugin_manager.discover()
        for plugin in self._plugins:
            plugin.initialize()
        self._udp_transport = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: UdpProtocol(self),
            local_addr=(host, udp_port),
            family=socket.AF_INET,
        )
        if self.config.server.get("enable_tcp", False):
            tcp_port = int(self.config.server.get("tcp_port", 5354))
            self._tcp_server = await asyncio.get_running_loop().create_server(
                lambda: TcpProtocol(self),
                host,
                tcp_port,
            )

    async def stop(self) -> None:
        self._running = False
        if hasattr(self, "_udp_transport"):
            self._udp_transport.close()
        if hasattr(self, "_tcp_server"):
            self._tcp_server.close()
            await self._tcp_server.wait_closed()

    async def handle_query(self, payload: bytes, client_ip: str) -> bytes:
        self.state.stats.requests += 1
        self.state.clients[client_ip] += 1
        try:
            message = DNSMessage(payload)
            domain = message.question_name()
            self.state.domains[domain] += 1
        except Exception as exc: 
            self.logger.warning("Malformed query from %s: %s", client_ip, exc)
            return b""

        cache_key = f"{client_ip}:{domain}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.state.stats.cache_hits += 1
            self._add_log({"client_ip": client_ip, "domain": domain, "cache_hit": True})
            return cached

        # Evaluate domain against rules (checks denylist FIRST before any blocklist files)
        decision = self.rule_engine.evaluate(domain, client_ip)
        if decision.blocked:
            self.state.stats.blocked += 1
            self._add_log({
                "client_ip": client_ip,
                "domain": domain,
                "blocked": True,
                "reason": decision.reason,
                "matched_rule": decision.matched_rule
            })
            return message.build_nxdomain_response()

        self.state.stats.allowed += 1
        response = await self._forward_query(domain)
        if response:
            self.cache.set(cache_key, response)
            self._add_log({"client_ip": client_ip, "domain": domain, "blocked": False, "cache_hit": False})
            return response

    def _add_log(self, log_entry: dict[str, Any]) -> None:
        """Add a log entry, maintaining a maximum size to prevent memory leaks."""
        log_entry["timestamp"] = time.time()
        self.state.logs.append(log_entry)
        if len(self.state.logs) > self.state.max_logs:
            self.state.logs = self.state.logs[-self.state.max_logs :]

    async def _forward_query(self, domain: str) -> bytes:
        """Forward a DNS query to an upstream resolver using proper DNS wire format."""
        upstream = self._get_upstream_server()
        timeout = float(self.config.server.get("timeout_seconds", 2.0))
        try:
            query_packet = self._build_dns_query(domain)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(upstream, 53),
                timeout=timeout,
            )
            try:
                writer.write(len(query_packet).to_bytes(2, "big") + query_packet)
                await writer.drain()
                data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
                return data
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc: 
            self.logger.warning("Upstream lookup failed for %s via %s: %s", domain, upstream, exc)
            return b""

    def _build_dns_query(self, domain: str) -> bytes:
        """Build a proper DNS query packet for the given domain."""
        query = bytearray()
        query.extend(b"\x00\x00") 
        query.extend(b"\x01\x00") 
        query.extend(b"\x00\x01") 
        query.extend(b"\x00\x00") 
        query.extend(b"\x00\x00") 
        query.extend(b"\x00\x00") 

        for label in domain.rstrip(".").split("."):
            query.append(len(label))
            query.extend(label.encode("ascii", errors="ignore"))
        query.append(0) 

        query.extend(b"\x00\x01") 
        query.extend(b"\x00\x01") 
        return bytes(query)

    def _get_upstream_server(self) -> str:
        server = self._upstream[self._upstream_index % len(self._upstream)]
        self._upstream_index += 1
        return server

    def snapshot(self) -> dict[str, Any]:
        recent_logs = self.state.logs[-10:]
        return {
            "stats": self.state.stats.to_dict(),
            "cache": self.cache.stats(),
            "clients": dict(self.state.clients.most_common(10)),
            "domains": dict(self.state.domains.most_common(10)),
            "plugins": [plugin.name for plugin in self._plugins],
            "recent_logs": recent_logs,
        }

class UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: DNSServer) -> None:
        self.server = server

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        client_ip = addr[0]
        asyncio.create_task(self.server.handle_query(data, client_ip))

class TcpProtocol(asyncio.Protocol):
    def __init__(self, server: DNSServer) -> None:
        self.server = server
        self._buffer = bytearray()
        self.transport = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        self._buffer.extend(data)
        self._process_buffer()

    def _process_buffer(self) -> None:
        """Process complete DNS messages from the buffer."""
        while len(self._buffer) >= 2:
            message_length = int.from_bytes(self._buffer[:2], "big")
            if len(self._buffer) < 2 + message_length:
                break
            message_data = bytes(self._buffer[2 : 2 + message_length])
            del self._buffer[: 2 + message_length]

            client_ip = self.transport.get_extra_info("peername")[0]
            asyncio.create_task(self._handle_query_and_send(message_data, client_ip))

    async def _handle_query_and_send(self, data: bytes, client_ip: str) -> None:
        """Handle a query and send the response."""
        try:
            response = await self.server.handle_query(data, client_ip)
            if response and self.transport:
                self.transport.write(len(response).to_bytes(2, "big") + response)
        except Exception as exc:
            self.server.logger.error("Error handling TCP query: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        self._buffer.clear()
