from __future__ import annotations

import logging
from typing import Any

from aiohttp import web


class DashboardApp:
    """Simple web dashboard for the DNS filtering server."""

    def __init__(self, server_state: Any | None = None) -> None:
        self.server_state = server_state
        self.logger = logging.getLogger("dashboard")

    def build_app(self) -> web.Application:
        """Build and return the aiohttp web application."""
        app = web.Application()

        # Add routes
        app.router.add_get("/", self.index)
        app.router.add_get("/api/stats", self.api_stats)

        return app

    async def index(self, request: web.Request) -> web.Response:
        """Serve the main dashboard page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Nebula DNS Dashboard</title>
            <style>
                body { font-family: sans-serif; margin: 20px; }
                .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
                .stat-box { border: 1px solid #ccc; padding: 15px; border-radius: 5px; }
                .stat-value { font-size: 24px; font-weight: bold; color: #333; }
                .stat-label { font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <h1>Nebula DNS Filtering Server</h1>
            <div class="stats" id="stats"></div>
            <script>
                async function updateStats() {
                    try {
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        const stats = data.stats || {};
                        
                        document.getElementById('stats').innerHTML = `
                            <div class="stat-box">
                                <div class="stat-label">Total Requests</div>
                                <div class="stat-value">${stats.requests || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Blocked</div>
                                <div class="stat-value">${stats.blocked || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Allowed</div>
                                <div class="stat-value">${stats.allowed || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Cache Hits</div>
                                <div class="stat-value">${stats.cache_hits || 0}</div>
                            </div>
                        `;
                    } catch (error) {
                        console.error('Error fetching stats:', error);
                    }
                }
                
                updateStats();
                setInterval(updateStats, 2000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def api_stats(self, request: web.Request) -> web.Response:
        """API endpoint for getting server statistics."""
        if self.server_state is None:
            return web.json_response({"status": "ok", "stats": {}})
        return web.json_response({"status": "ok", "stats": self.server_state.snapshot()})
