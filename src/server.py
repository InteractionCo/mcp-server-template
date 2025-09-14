#!/usr/bin/env python3
"""
GitHub-Poke Bridge MCP Server
A FastMCP server that receives GitHub webhooks and forwards them to Poke API.
"""
import os
import json
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from security import validate_github_signature
from github_client import GitHubClient
from poke_client import PokeClient
from webhook_handlers import WebhookHandlers

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("GitHub-Poke Bridge")

# Initialize clients
github_client = GitHubClient()
poke_client = PokeClient()
webhook_handlers = WebhookHandlers()


# =============================================================================
# MCP TOOLS
# =============================================================================


@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    """Simple greeting function for testing MCP connectivity."""
    return f"Hello, {name}! Welcome to GitHub-Poke Bridge MCP server!"


@mcp.tool(
    description="Get information about the MCP server including name, version, environment, and Python version"
)
def get_server_info() -> dict:
    """Returns basic information about the MCP server for debugging/monitoring."""
    return {
        "server_name": "GitHub-Poke Bridge",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
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


@mcp.tool(description="Search for code within the connected repository")
def search_code(
    query: str, extension: str = None, path: str = None, limit: int = 10
) -> dict:
    """Search for code patterns within the connected repository."""
    # Get repo info from environment or webhook context
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")

    if not repo_owner or not repo_name:
        return {
            "success": False,
            "error": "Repository not configured. Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables.",
        }

    return github_client.search_code(
        repo_owner, repo_name, query, extension, path, limit
    )


@mcp.tool(
    description="Get the content of a specific file from the connected repository"
)
def get_file_content(file_path: str, ref: str = None) -> dict:
    """Retrieve the content of a specific file from the connected repository."""
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")

    if not repo_owner or not repo_name:
        return {
            "success": False,
            "error": "Repository not configured. Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables.",
        }

    return github_client.get_file_content(repo_owner, repo_name, file_path, ref)


@mcp.tool(description="Get repository information and structure")
def get_repository_info() -> dict:
    """Get information about the connected repository including basic stats and structure."""
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")

    if not repo_owner or not repo_name:
        return {
            "success": False,
            "error": "Repository not configured. Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables.",
        }

    try:
        headers = github_client._get_headers()
        url = f"{github_client.base_url}/repos/{repo_owner}/{repo_name}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            repo_data = response.json()
            return {
                "success": True,
                "repository": {
                    "name": repo_data.get("name", ""),
                    "full_name": repo_data.get("full_name", ""),
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language", ""),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "default_branch": repo_data.get("default_branch", "main"),
                    "url": repo_data.get("html_url", ""),
                },
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get repository info: {response.status_code} - {response.text}",
            }
    except Exception as e:
        return {"success": False, "error": f"Exception: {str(e)}"}


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
                    {"status": "error", "message": "Invalid signature"}, status_code=401
                )

        # Parse payload
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return JSONResponse(
                {"status": "error", "message": "Invalid JSON payload"}, status_code=400
            )

        # Basic payload validation
        if not isinstance(payload, dict):
            return JSONResponse(
                {"status": "error", "message": "Invalid payload format"},
                status_code=400,
            )

        # Get event type and process webhook
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        success = webhook_handlers.process_webhook(event_type, payload)

        if success:
            return JSONResponse({"status": "success", "message": "Forwarded to Poke"})
        else:
            return JSONResponse(
                {"status": "error", "message": "Failed to forward to Poke"}
            )

    except Exception as e:
        # Log full error for debugging but don't expose details to client
        print(f"❌ Webhook processing failed: {str(e)}")
        return JSONResponse(
            {"status": "error", "message": "Webhook processing failed"}, status_code=500
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting FastMCP server on {host}:{port}")

    mcp.run(transport="http", host=host, port=port, stateless_http=True)
