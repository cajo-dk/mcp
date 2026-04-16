# Home Assistant MCP Reporter

This repository contains a minimal Python MCP server packaged as a Home Assistant add-on.

## What it does

The server exposes one MCP tool:

- `posstReport`

`posstReport` accepts a JSON object and forwards it to the configured Power Automate webhook.

## Local development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m mcp_reporter_server
```

The server listens on `0.0.0.0:8099` using streamable HTTP transport.

## Home Assistant installation

1. Add this repository as an add-on repository in Home Assistant.
2. Install the `MCP Reporter` add-on.
3. Start the add-on.
4. Connect your MCP client to `http://homeassistant.local:8099/mcp` or the add-on host/IP on port `8099`.

## Notes

- The webhook URL is baked in by default to match the requested behavior.
- You can override it with the `POWER_AUTOMATE_WEBHOOK_URL` environment variable if needed.
