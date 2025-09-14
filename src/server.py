#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# =============================================================================
# SETUP & CONFIGURATION
# =============================================================================

# Load environment variables
load_dotenv()

mcp = FastMCP("GitHub-Poke Bridge")

# =============================================================================
# MCP TOOLS (for testing and debugging)
# =============================================================================

# Simple greeting function for testing MCP connectivity
@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    """
    Simple greeting function for testing MCP connectivity.
    Takes a name and returns a welcome message.
    """
    return f"Hello, {name}! Welcome to GitHub-Poke Bridge MCP server!"

# Returns basic server information for debugging
@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    """
    Returns basic information about the MCP server for debugging/monitoring.
    Includes server name, version, environment, and Python version.
    """
    return {
        "server_name": "GitHub-Poke Bridge",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }

# Test function to manually send messages to Poke API
@mcp.tool(description="Send a test message to Poke API to verify connectivity")
def test_poke_message(message: str) -> dict:
    """
    Test function to send a message directly to Poke API.
    Used for debugging and verifying the Poke integration works.
    Returns success/error status and response details.
    """
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

# =============================================================================
# POKE API INTEGRATION
# =============================================================================

# Main function to forward messages to Poke
def send_to_poke(message: str) -> bool:
    """
    Core function to send messages to Poke API.
    Used by webhook handler to forward GitHub events to Poke.
    Returns True if message sent successfully, False otherwise.
    """
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

# =============================================================================
# GITHUB API INTEGRATION
# =============================================================================

# Helper to create authenticated GitHub API headers
def get_github_api_headers():
    """
    Creates HTTP headers for GitHub API requests.
    Includes authentication token and proper user agent.
    """
    token = os.environ.get("GITHUB_TOKEN")
    return {
        "Authorization": f"Bearer {token}" if token else "",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Poke-Bridge"
    }

# Fetches diff content for a commit from GitHub API
def get_commit_diff(owner: str, repo: str, commit_sha: str) -> str:
    """
    Fetches the actual diff content (code changes) for a commit.
    Returns the diff as a string, or empty string if unavailable.
    """
    try:
        headers = get_github_api_headers()
        headers["Accept"] = "application/vnd.github.diff"  # Request diff format
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text[:1500] + "..." if len(response.text) > 1500 else response.text  # Truncate long diffs
    except Exception as e:
        print(f"Failed to fetch commit diff: {e}")

    return ""

# Fetches detailed commit info from GitHub API (files changed, stats, etc.)
def enrich_commit_data(owner: str, repo: str, commit_sha: str) -> dict:
    """Fetch detailed commit information from GitHub API"""
    try:
        headers = get_github_api_headers()
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            commit_data = response.json()
            return {
                "message": commit_data.get("commit", {}).get("message", ""),
                "author": commit_data.get("commit", {}).get("author", {}).get("name", ""),
                "files_changed": len(commit_data.get("files", [])),
                "additions": commit_data.get("stats", {}).get("additions", 0),
                "deletions": commit_data.get("stats", {}).get("deletions", 0),
                "files": [f["filename"] for f in commit_data.get("files", [])[:5]],  # First 5 files
                "url": commit_data.get("html_url", "")
            }
    except Exception as e:
        print(f"Failed to enrich commit data: {e}")

    return {}

# Fetches detailed PR info from GitHub API (changes, reviews, etc.)
def enrich_pull_request_data(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch detailed PR information from GitHub API"""
    try:
        headers = get_github_api_headers()
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            pr_data = response.json()
            return {
                "title": pr_data.get("title", ""),
                "body": pr_data.get("body", "")[:500] + "..." if pr_data.get("body", "") else "",  # Truncate body
                "state": pr_data.get("state", ""),
                "author": pr_data.get("user", {}).get("login", ""),
                "base_branch": pr_data.get("base", {}).get("ref", ""),
                "head_branch": pr_data.get("head", {}).get("ref", ""),
                "files_changed": pr_data.get("changed_files", 0),
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "url": pr_data.get("html_url", "")
            }
    except Exception as e:
        print(f"Failed to enrich PR data: {e}")

    return {}

# Fetches detailed issue info from GitHub API (labels, assignees, comments)
def enrich_issue_data(owner: str, repo: str, issue_number: int) -> dict:
    """Fetch detailed issue information from GitHub API"""
    try:
        headers = get_github_api_headers()
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            issue_data = response.json()
            return {
                "title": issue_data.get("title", ""),
                "body": issue_data.get("body", "")[:300] + "..." if issue_data.get("body", "") else "",  # Truncate body
                "state": issue_data.get("state", ""),
                "author": issue_data.get("user", {}).get("login", ""),
                "labels": [label["name"] for label in issue_data.get("labels", [])],
                "assignees": [assignee["login"] for assignee in issue_data.get("assignees", [])],
                "comments": issue_data.get("comments", 0),
                "url": issue_data.get("html_url", "")
            }
    except Exception as e:
        print(f"Failed to enrich issue data: {e}")

    return {}

# =============================================================================
# WEBHOOK ENDPOINT & EVENT PROCESSING
# =============================================================================

# Main webhook endpoint that receives GitHub events and forwards them to Poke
@mcp.custom_route("/webhook/github", methods=["POST"])
async def github_webhook(request: Request) -> JSONResponse:
    """Receive GitHub webhooks and forward to Poke"""
    try:
        payload = await request.json()

        # Get event type from headers
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        # Create enriched message based on event type
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        repo_owner = repo_info.get("owner", {}).get("login", "unknown")

        if event_type == "push":
            pusher = payload.get("pusher", {}).get("name", "someone")
            commits = payload.get("commits", [])
            commit_count = len(commits)

            # Get detailed info for the latest commit
            if commits:
                latest_commit = commits[-1]
                commit_sha = latest_commit.get("id", "")
                commit_details = enrich_commit_data(repo_owner, repo_name, commit_sha)

                if commit_details:
                    # Check if we should include diff content
                    include_diff = os.environ.get("INCLUDE_DIFF_CONTENT", "false").lower() == "true"

                    message = f"""🚀 {commit_count} new commit{'s' if commit_count != 1 else ''} pushed to {repo_name} by {pusher}

Latest commit: {commit_details.get('message', 'No message')}
Author: {commit_details.get('author', pusher)}
Files changed: {commit_details.get('files_changed', 0)} (+{commit_details.get('additions', 0)} -{commit_details.get('deletions', 0)})
Modified files: {', '.join(commit_details.get('files', []))}"""

                    # Add diff content if enabled
                    if include_diff:
                        diff_content = get_commit_diff(repo_owner, repo_name, commit_sha)
                        if diff_content:
                            message += f"\n\nChanges:\n```\n{diff_content}\n```"

                    message += f"\n\nView commit: {commit_details.get('url', '')}"
                else:
                    message = f"🚀 {commit_count} new commit{'s' if commit_count != 1 else ''} pushed to {repo_name} by {pusher}"
            else:
                message = f"🚀 Push event to {repo_name} by {pusher}"

        elif event_type == "pull_request":
            action = payload.get("action", "unknown")
            pr_data = payload.get("pull_request", {})
            pr_number = pr_data.get("number", 0)
            pr_title = pr_data.get("title", "")
            pr_user = pr_data.get("user", {}).get("login", "someone")

            # Get detailed PR info
            pr_details = enrich_pull_request_data(repo_owner, repo_name, pr_number)

            if pr_details:
                message = f"""📝 PR #{pr_number} {action} in {repo_name} by {pr_user}

Title: {pr_details.get('title', pr_title)}
Branch: {pr_details.get('head_branch', 'unknown')} → {pr_details.get('base_branch', 'main')}
Files changed: {pr_details.get('files_changed', 0)} (+{pr_details.get('additions', 0)} -{pr_details.get('deletions', 0)})
State: {pr_details.get('state', 'unknown')}

{pr_details.get('body', '')[:200] + '...' if pr_details.get('body', '') else 'No description'}

View PR: {pr_details.get('url', '')}"""
            else:
                message = f"📝 PR #{pr_number} {action} in {repo_name} by {pr_user}: {pr_title}"

        elif event_type == "issues":
            action = payload.get("action", "unknown")
            issue_data = payload.get("issue", {})
            issue_number = issue_data.get("number", 0)
            issue_title = issue_data.get("title", "")
            issue_user = issue_data.get("user", {}).get("login", "someone")

            # Get detailed issue info
            issue_details = enrich_issue_data(repo_owner, repo_name, issue_number)

            if issue_details:
                labels_str = ", ".join(issue_details.get('labels', [])) or "None"
                assignees_str = ", ".join(issue_details.get('assignees', [])) or "Unassigned"

                message = f"""🐛 Issue #{issue_number} {action} in {repo_name} by {issue_user}

Title: {issue_details.get('title', issue_title)}
State: {issue_details.get('state', 'unknown')}
Labels: {labels_str}
Assignees: {assignees_str}
Comments: {issue_details.get('comments', 0)}

{issue_details.get('body', '')[:200] + '...' if issue_details.get('body', '') else 'No description'}

View issue: {issue_details.get('url', '')}"""
            else:
                message = f"🐛 Issue #{issue_number} {action} in {repo_name} by {issue_user}: {issue_title}"

        elif event_type == "create":
            # Handle branch/tag creation
            ref_type = payload.get("ref_type", "unknown")
            ref_name = payload.get("ref", "unknown")
            creator = payload.get("sender", {}).get("login", "someone")

            if ref_type == "branch":
                # Try to get the base branch (usually 'main' for new branches)
                default_branch = payload.get("repository", {}).get("default_branch", "main")
                message = f"""🌿 New branch '{ref_name}' created in {repo_name} by {creator}

Branch: {ref_name}
Branched from: {default_branch} (likely)
Repository: {repo_name}

View branch: https://github.com/{repo_owner}/{repo_name}/tree/{ref_name}"""

            elif ref_type == "tag":
                message = f"""🏷️ New tag '{ref_name}' created in {repo_name} by {creator}

Tag: {ref_name}
Repository: {repo_name}

View tag: https://github.com/{repo_owner}/{repo_name}/releases/tag/{ref_name}"""

            else:
                message = f"📫 New {ref_type} '{ref_name}' created in {repo_name} by {creator}"

        elif event_type == "delete":
            # Handle branch/tag deletion
            ref_type = payload.get("ref_type", "unknown")
            ref_name = payload.get("ref", "unknown")
            deleter = payload.get("sender", {}).get("login", "someone")

            message = f"""🗑️ {ref_type.title()} '{ref_name}' deleted from {repo_name} by {deleter}

Deleted {ref_type}: {ref_name}
Repository: {repo_name}"""

        else:
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
