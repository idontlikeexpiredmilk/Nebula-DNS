from __future__ import annotations

from aiohttp import web


class APIRouter:
    """Basic REST API endpoints for monitoring and configuration."""

    def __init__(self, server_state: object | None = None) -> None:
        self.server_state = server_state

    def build_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/api/statistics", self.statistics)
        app.router.add_get("/api/health", self.health)
        return app

    async def statistics(self, request: web.Request) -> web.Response:
        if self.server_state is None:
            return web.json_response({"status": "ok", "stats": {}})
        return web.json_response({"status": "ok", "stats": self.server_state.snapshot()})

    async def health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})
