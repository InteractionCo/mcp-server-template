#!/usr/bin/env python3
"""
GitHub-Poke Bridge MCP Server
A FastMCP server that receives GitHub webhooks and forwards them to Poke API.
"""
import os
import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .security import validate_github_signature
from .github_client import GitHubClient
from .poke_client import PokeClient
from .webhook_handlers import WebhookHandlers

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("GitHub-Poke Bridge")

# Initialize clients
github_client = GitHubClient()
poke_client = PokeClient()
webhook_handlers = WebhookHandlers()


# =============================================================================
# MCP TOOLS (for testing and debugging)
# =============================================================================

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    """Simple greeting function for testing MCP connectivity."""
    return f"Hello, {name}! Welcome to GitHub-Poke Bridge MCP server!"


@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    """Returns basic information about the MCP server for debugging/monitoring."""
    return {
        "server_name": "GitHub-Poke Bridge",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }


@mcp.tool(description="Add a comment to a GitHub issue")
def add_issue_comment(owner: str, repo: str, issue_number: int, comment: str) -> dict:
    """Add a comment to a GitHub issue."""
    return github_client.add_issue_comment(owner, repo, issue_number, comment)


@mcp.tool(description="Add a comment to a GitHub pull request")
def add_pr_comment(owner: str, repo: str, pr_number: int, comment: str) -> dict:
    """Add a comment to a GitHub pull request."""
    return github_client.add_issue_comment(owner, repo, pr_number, comment)


@mcp.tool(description="Close a GitHub issue")
def close_issue(owner: str, repo: str, issue_number: int, comment: str = None) -> dict:
    """Close a GitHub issue, optionally with a closing comment."""
    return github_client.close_issue(owner, repo, issue_number, comment)


@mcp.tool(description="Add labels to a GitHub issue")
def add_issue_labels(owner: str, repo: str, issue_number: int, labels: list) -> dict:
    """Add labels to a GitHub issue."""
    return github_client.add_issue_labels(owner, repo, issue_number, labels)


@mcp.tool(description="Assign a user to a GitHub issue")
def assign_issue(owner: str, repo: str, issue_number: int, assignee: str) -> dict:
    """Assign a user to a GitHub issue."""
    return github_client.assign_issue(owner, repo, issue_number, assignee)


@mcp.tool(description="Send a test message to Poke API to verify connectivity")
def test_poke_message(message: str) -> dict:
    """Test function to send a message directly to Poke API."""
    return poke_client.test_connection(message)


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@mcp.custom_route("/webhook/github", methods=["POST"])
async def github_webhook(request: Request) -> JSONResponse:
    """Receive GitHub webhooks and forward to Poke"""
    try:
        # Get raw body for signature validation
        body = await request.body()

        # Validate GitHub webhook signature
        webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        if webhook_secret:
            signature = request.headers.get("X-Hub-Signature-256")
            if not validate_github_signature(body, signature, webhook_secret):
                return JSONResponse(
                    {"status": "error", "message": "Invalid signature"},
                    status_code=401
                )

        # Parse payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except Exception:
            return JSONResponse(
                {"status": "error", "message": "Invalid JSON payload"},
                status_code=400
            )

        # Basic payload validation
        if not isinstance(payload, dict):
            return JSONResponse(
                {"status": "error", "message": "Invalid payload format"},
                status_code=400
            )

        # Get event type and process webhook
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        success = webhook_handlers.process_webhook(event_type, payload)

        if success:
            return JSONResponse({"status": "success", "message": "Forwarded to Poke"})
        else:
            return JSONResponse({"status": "error", "message": "Failed to forward to Poke"})

    except Exception as e:
        # Log full error for debugging but don't expose details to client
        print(f"❌ Webhook processing failed: {str(e)}")
        return JSONResponse(
            {"status": "error", "message": "Webhook processing failed"},
            status_code=500
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting FastMCP server on {host}:{port}")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )