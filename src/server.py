#!/usr/bin/env python3
import os
import json
import uuid
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import httpx


SERVER_NAME = os.environ.get("SERVER_NAME", "MCP Terragon Bridge")
mcp = FastMCP(SERVER_NAME)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def terragon_settings_from_env() -> Dict[str, Optional[str]]:
    return {
        "base_url": _env("TERRAGON_BASE_URL", _env("OPENTERRA_BASE_URL", "http://localhost:8001")),
        "provider": _env("TERRAGON_PROVIDER", "anthropic"),
        "api_key": _env("TERRAGON_API_KEY"),
        "model": _env("TERRAGON_MODEL", "claude-3-7-sonnet-2025-02-19"),
        "custom_model": _env("TERRAGON_CUSTOM_MODEL", ""),
        "workspace_dir": _env("TERRAGON_WORKSPACE_DIR"),
        "poke_secret": _env("TERRAGON_POKE_SECRET"),
    }


async def _call_terragon_execute(
    instruction: str,
    *,
    base_url: str,
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    custom_model: Optional[str] = None,
    workspace_dir: Optional[str] = None,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    Call Terragon/OpenTerra's execute endpoint to spin up an agent for a task.

    Expects a compatible API at `{base_url}/api/agent/execute` like OpenTerra.
    """
    payload: Dict[str, Any] = {
        "taskId": str(uuid.uuid4()),
        "instruction": instruction,
        "settings": {
            "provider": provider,
            "apiKey": api_key,
        },
    }
    if model:
        payload["settings"]["model"] = model
    if custom_model:
        payload["settings"]["customModel"] = custom_model
    if workspace_dir:
        payload["workspaceDir"] = workspace_dir

    url = base_url.rstrip("/") + "/api/agent/execute"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to {SERVER_NAME}!"


@mcp.tool(
    description="Get information about this server including name, version, environment, and Python version",
)
def get_server_info() -> dict:
    return {
        "server_name": SERVER_NAME,
        "version": "1.1.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
        "poke_enabled": True,
    }


@mcp.custom_route("/healthz", methods=["GET"], name="health")
async def health(_: Request) -> Response:
    return JSONResponse({"ok": True, "service": SERVER_NAME})


@mcp.custom_route("/poke", methods=["GET"], name="poke_get")
async def poke_get(_: Request) -> Response:
    """Simple GET to verify the endpoint is available."""
    cfg = terragon_settings_from_env()
    redacted_cfg = {**cfg, "api_key": "***" if cfg.get("api_key") else None, "poke_secret": "***" if cfg.get("poke_secret") else None}
    return JSONResponse({"ok": True, "message": "Poke ready", "config": redacted_cfg})


@mcp.custom_route("/poke", methods=["POST"], name="poke_post")
async def poke_post(request: Request) -> Response:
    """
    Spin up a Terragon/OpenTerra agent to perform a task.

    Request body JSON:
    {
      "instruction": "string (required)",
      "workspaceDir": "string (optional)",
      "settings": {            # optional overrides
        "provider": "anthropic|openrouter|moonshot|...",
        "apiKey": "...",
        "model": "...",
        "customModel": "..."
      }
    }
    Provide shared secret via header `X-Poke-Secret` if TERRAGON_POKE_SECRET is set.
    """
    cfg = terragon_settings_from_env()

    # Optional shared-secret auth
    expected_secret = cfg.get("poke_secret")
    if expected_secret:
        provided = request.headers.get("X-Poke-Secret") or (request.query_params.get("secret") if request.query_params else None)
        if not provided or provided != expected_secret:
            return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "Body must be an object"}, status_code=400)

    instruction = body.get("instruction")
    if not instruction or not isinstance(instruction, str):
        return JSONResponse({"ok": False, "error": "'instruction' is required"}, status_code=400)

    overrides: Dict[str, Any] = body.get("settings") or {}
    workspace_dir = body.get("workspaceDir") or overrides.get("workspaceDir") or cfg.get("workspace_dir")

    base_url = overrides.get("baseUrl") or cfg["base_url"]
    provider = overrides.get("provider") or cfg.get("provider")
    api_key = overrides.get("apiKey") or cfg.get("api_key")
    model = overrides.get("model") or cfg.get("model")
    custom_model = overrides.get("customModel") or cfg.get("custom_model")

    missing = [k for k, v in {"baseUrl": base_url, "provider": provider, "apiKey": api_key}.items() if not v]
    if missing:
        return JSONResponse({"ok": False, "error": f"Missing required config: {', '.join(missing)}"}, status_code=400)

    try:
        result = await _call_terragon_execute(
            instruction,
            base_url=str(base_url),
            provider=str(provider),
            api_key=str(api_key),
            model=str(model) if model else None,
            custom_model=str(custom_model) if custom_model else None,
            workspace_dir=str(workspace_dir) if workspace_dir else None,
        )
        # Normalize a minimal response shape
        return JSONResponse({
            "ok": True,
            "result": result,
        })
    except httpx.HTTPStatusError as e:
        return JSONResponse({
            "ok": False,
            "error": f"Terragon API error: {e.response.status_code}",
            "details": e.response.text,
        }, status_code=502)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting FastMCP server on {host}:{port} with MCP at /mcp and custom routes /poke, /healthz")

    mcp.run(
        transport="http",
        host=host,
        port=port,
    )
