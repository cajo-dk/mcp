from __future__ import annotations

import contextlib
import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

DEFAULT_WEBHOOK_URL = (
    "https://default4173759fa7fb45f18231b8f68f45ca.49.environment.api.powerplatform.com:443/"
    "powerautomate/automations/direct/workflows/e4c45766e28c430a92cd36781e4bdfa8/triggers/manual/"
    "paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ENft6RNSdBOP5Uc7bV5voyLR42z9vSMKHnk3ZGGlzqU"
)

SERVER_NAME = "home-assistant-mcp-reporter"
mcp = FastMCP(
    SERVER_NAME,
    json_response=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)
mcp_http_app = mcp.streamable_http_app()
OPTIONS_PATH = os.getenv("MCP_OPTIONS_PATH", "/data/options.json")


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


def get_tool_list_payload() -> dict[str, Any]:
    tools = []
    for tool in mcp._tool_manager.list_tools():
        tools.append(
            {
                "name": tool.name,
                "title": tool.title,
                "description": tool.description,
                "parameters": tool.parameters,
                "annotations": tool.annotations,
                "meta": tool.meta,
            }
        )

    return {"server": SERVER_NAME, "tools": tools}


async def list_tools(_: Request) -> JSONResponse:
    return JSONResponse(get_tool_list_payload())


def load_api_key() -> str | None:
    env_api_key = os.getenv("MCP_API_KEY")
    if env_api_key:
        return env_api_key

    try:
        with open(OPTIONS_PATH, "r", encoding="utf-8") as fh:
            options = json.load(fh)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

    api_key = options.get("api_key")
    return api_key if isinstance(api_key, str) and api_key else None


def extract_api_key(request: Request) -> str | None:
    header_api_key = request.headers.get("x-api-key")
    if header_api_key:
        return header_api_key

    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return None


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        provided_key = extract_api_key(request)
        if provided_key != self.api_key:
            return JSONResponse(
                {"ok": False, "error": "Unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


def main() -> None:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8099"))
    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("No API key configured. Set api_key in the Home Assistant add-on configuration.")

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/tools", endpoint=list_tools, methods=["GET", "POST"]),
            Route("/", endpoint=mcp_http_app, methods=["GET", "POST", "DELETE"]),
        ],
        lifespan=lifespan,
        middleware=[Middleware(ApiKeyMiddleware, api_key=api_key)],
    )

    uvicorn.run(app, host=host, port=port)
