# MCP Terragon Bridge

Minimal [FastMCP](https://github.com/jlowin/fastmcp) server template extended with a `POST /poke` endpoint that can spin up Terragon/OpenTerra agents. Designed for easy local testing and one‑click Render deployment.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

— This repo is based on the upstream MCP template and adds a Terragon integration layer. —

## What You Get

- MCP over streamable HTTP at `/mcp`
- Health check at `/healthz`
- `GET /poke` to verify configuration
- `POST /poke` to instruct Terragon/OpenTerra to execute a task (spawn an agent)

## Quick Start (Local)

1) Create and activate an environment

```bash
git clone <your-repo-url>
cd mcp-server-template
uv venv || python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Set Terragon/OpenTerra config

At minimum, set a provider and API key that your Terragon/OpenTerra accepts. If you’re using the open‑source OpenTerra server (recommended for quick testing), it exposes `POST /api/agent/execute` by default.

```bash
export TERRAGON_BASE_URL="http://localhost:8001"   # or your hosted Terragon/OpenTerra URL
export TERRAGON_PROVIDER="anthropic"               # e.g. anthropic | openrouter | moonshot
export TERRAGON_API_KEY="sk-your-key"              # key for the provider selected above
export TERRAGON_MODEL="claude-3-7-sonnet-2025-02-19"  # optional, can be overridden per request
# optional hardening for /poke
export TERRAGON_POKE_SECRET="super-secret"         # require X-Poke-Secret header
```

3) Run the server

```bash
python src/server.py
```

4) Test MCP via Inspector

```bash
npx @modelcontextprotocol/inspector
```
Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using “Streamable HTTP” transport (NOTE the `/mcp`).

5) Try the Poke endpoint

```bash
curl -s http://localhost:8000/poke | jq .

curl -s -X POST http://localhost:8000/poke \
  -H "Content-Type: application/json" \
  -H "X-Poke-Secret: super-secret" \
  -d '{
        "instruction": "Create a simple REST API endpoint using FastAPI",
        "workspaceDir": "/tmp/agent-work",
        "settings": {
          "provider": "anthropic",
          "apiKey": "sk-your-key",
          "model": "claude-3-7-sonnet-2025-02-19"
        }
      }' | jq .
```

If everything is configured, this will call your Terragon/OpenTerra at `TERRAGON_BASE_URL/api/agent/execute` and return its response.

## Using OpenTerra Locally (Optional)

If you don’t have access to Terragon, you can run the open‑source equivalent (OpenTerra):

```bash
git clone https://github.com/KaiStephens/OpenTerra
cd OpenTerra
pip install -r requirements.txt
python web_ui.py  # starts a FastAPI server with /api/agent/execute
```

Then set `TERRAGON_BASE_URL=http://localhost:8001` (or whatever port OpenTerra uses) and use the `POST /poke` example above.

## Deployment (Render)

### One‑Click Deploy
Click the “Deploy to Render” button above.

### Manual
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Add environment variables (`TERRAGON_BASE_URL`, `TERRAGON_PROVIDER`, `TERRAGON_API_KEY`, etc.)
6. Render will apply `render.yaml`

Your MCP endpoint will be available at `https://your-service.onrender.com/mcp` and Poke at `https://your-service.onrender.com/poke`.

## Configuration

Environment variables used by the integration:

- `SERVER_NAME` – Optional display name for this server
- `TERRAGON_BASE_URL` – Base URL to your Terragon/OpenTerra (e.g. `https://terragon.example.com`)
- `TERRAGON_PROVIDER` – Provider id expected by Terragon/OpenTerra (e.g. `anthropic`, `openrouter`)
- `TERRAGON_API_KEY` – API key that Terragon/OpenTerra will pass to the provider
- `TERRAGON_MODEL` – Default model to use if not overridden in the request
- `TERRAGON_CUSTOM_MODEL` – Optional custom model identifier
- `TERRAGON_WORKSPACE_DIR` – Optional default workspace directory for agents
- `TERRAGON_POKE_SECRET` – If set, `POST /poke` requires header `X-Poke-Secret` to match

You can override these per request by including a `settings` object (supports `baseUrl`, `provider`, `apiKey`, `model`, `customModel`) in the `POST /poke` body.

## API: Poke

- `GET /poke` → returns `{ ok: true, message, config }` with API key redacted
- `POST /poke` → spins up a Terragon/OpenTerra agent via `POST {base}/api/agent/execute`

Request body:

```json
{
  "instruction": "<required task instruction>",
  "workspaceDir": "<optional path>",
  "settings": {
    "provider": "anthropic",
    "apiKey": "sk-...",
    "model": "claude-3-7-sonnet-2025-02-19",
    "customModel": "optional-custom"
  }
}
```

Response: pass‑through of Terragon/OpenTerra execute payload wrapped in `{ ok, result }`, or `{ ok: false, error }` on errors.

## Customize MCP Tools

Add more tools by decorating functions with `@mcp.tool` in `src/server.py`.

```python
@mcp.tool
def calculate(x: float, y: float, operation: str) -> float:
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    raise ValueError("unsupported operation")
```

## Notes

- The integration assumes a Terragon/OpenTerra‑compatible endpoint at `/api/agent/execute`.
- If your Terragon differs, set `TERRAGON_BASE_URL` accordingly and adjust request mapping in `src/server.py` as needed.
```
