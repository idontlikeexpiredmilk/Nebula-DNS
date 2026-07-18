from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from aiohttp import web

from .config import Config
from .server import DNSServer
from dashboard.app import DashboardApp


def configure_logging(path: str | None = None) -> None:
    Path(path or "logs/dnsserver.log").parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(path or "logs/dnsserver.log", encoding="utf-8")],
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the lightweight DNS filtering server")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--dashboard", action="store_true", help="Launch the dashboard web app")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = Config(str(config_path))
    configure_logging(config.logging.get("file", "logs/dnsserver.log"))

    server = DNSServer(config)
    await server.start()

    if args.dashboard:
        dashboard_app = DashboardApp(server_state=server)
        web_app = dashboard_app.build_app()
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, config.dashboard.get("host", "0.0.0.0"), int(config.dashboard.get("port", 8000)))
        await site.start()

    try:
        await asyncio.Event().wait()
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
