from __future__ import annotations

import contextlib
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

DEFAULT_WEBHOOK_URL = (
    "https://default4173759fa7fb45f18231b8f68f45ca.49.environment.api.powerplatform.com:443/"
    "powerautomate/automations/direct/workflows/e4c45766e28c430a92cd36781e4bdfa8/triggers/manual/"
    "paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ENft6RNSdBOP5Uc7bV5voyLR42z9vSMKHnk3ZGGlzqU"
)

SERVER_NAME = "home-assistant-mcp-reporter"
mcp = FastMCP(SERVER_NAME, json_response=True, streamable_http_path="/")


@mcp.tool(
    name="postReport",
    description="Post a JSON report object to the configured Power Automate webhook.",
)
async def post_report(report: dict[str, Any]) -> dict[str, Any]:
    webhook_url = os.getenv("POWER_AUTOMATE_WEBHOOK_URL", DEFAULT_WEBHOOK_URL)
    timeout = float(os.getenv("REPORT_TIMEOUT_SECONDS", "15"))

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(webhook_url, json=report)

    response.raise_for_status()

    return {
        "ok": True,
        "status_code": response.status_code,
        "response_text": response.text,
    }


def main() -> None:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8099"))

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    app = Starlette(
        routes=[
            Mount("/mcp", app=mcp.streamable_http_app()),
        ],
        lifespan=lifespan,
    )

    uvicorn.run(app, host=host, port=port)
