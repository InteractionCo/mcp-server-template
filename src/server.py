#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Load environment variables
load_dotenv()

mcp = FastMCP("GitHub-Poke Bridge")

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to GitHub-Poke Bridge MCP server!"

@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    return {
        "server_name": "GitHub-Poke Bridge",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }

@mcp.tool(description="Send a test message to Poke API to verify connectivity")
def test_poke_message(message: str) -> dict:
    """Send a test message to Poke API"""
    api_key = os.environ.get("POKE_API_KEY")
    api_url = os.environ.get("POKE_API_URL")

    if not api_key or not api_url:
        return {"error": "Missing POKE_API_KEY or POKE_API_URL in environment"}

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"message": message}
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.content else "No content"
        }
    except Exception as e:
        return {"error": f"Failed to send message: {str(e)}"}

def send_to_poke(message: str) -> bool:
    """Helper function to send messages to Poke"""
    api_key = os.environ.get("POKE_API_KEY")
    api_url = os.environ.get("POKE_API_URL")

    if not api_key or not api_url:
        print("ERROR: Missing Poke API credentials")
        return False

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"message": message}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send to Poke: {e}")
        return False

# Add webhook endpoint
@mcp.custom_route("/webhook/github", methods=["POST"])
async def github_webhook(request: Request) -> JSONResponse:
    """Receive GitHub webhooks and forward to Poke"""
    try:
        payload = await request.json()

        # Get event type from headers
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        # Create message based on event type
        if event_type == "push":
            repo_name = payload.get("repository", {}).get("name", "unknown")
            pusher = payload.get("pusher", {}).get("name", "someone")
            commits = len(payload.get("commits", []))
            message = f"🚀 {commits} new commit{'s' if commits != 1 else ''} pushed to {repo_name} by {pusher}"

        elif event_type == "pull_request":
            action = payload.get("action", "unknown")
            repo_name = payload.get("repository", {}).get("name", "unknown")
            pr_title = payload.get("pull_request", {}).get("title", "")
            pr_user = payload.get("pull_request", {}).get("user", {}).get("login", "someone")
            message = f"📝 PR {action} in {repo_name} by {pr_user}: {pr_title}"

        elif event_type == "issues":
            action = payload.get("action", "unknown")
            repo_name = payload.get("repository", {}).get("name", "unknown")
            issue_title = payload.get("issue", {}).get("title", "")
            issue_user = payload.get("issue", {}).get("user", {}).get("login", "someone")
            message = f"🐛 Issue {action} in {repo_name} by {issue_user}: {issue_title}"

        else:
            repo_name = payload.get("repository", {}).get("name", "repository")
            message = f"📫 GitHub {event_type} event in {repo_name}"

        # Send to Poke
        success = send_to_poke(message)

        if success:
            print(f"✅ Forwarded to Poke: {message}")
            return JSONResponse({"status": "success", "message": "Forwarded to Poke"})
        else:
            print(f"❌ Failed to forward: {message}")
            return JSONResponse({"status": "error", "message": "Failed to forward to Poke"})

    except Exception as e:
        error_msg = f"Webhook processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return JSONResponse({"status": "error", "message": error_msg})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port
    )
