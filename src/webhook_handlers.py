#!/usr/bin/env python3
"""
GitHub webhook event handlers for processing different event types.
"""
import os
from typing import Dict, Any

from github_client import GitHubClient
from poke_client import PokeClient


class WebhookHandlers:
    """Handlers for different GitHub webhook events"""

    def __init__(self):
        self.github = GitHubClient()
        self.poke = PokeClient()

    def handle_push(self, payload: Dict[str, Any]) -> str:
        """Handle push events"""
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        repo_owner = repo_info.get("owner", {}).get("login", "unknown")
        pusher = payload.get("pusher", {}).get("name", "someone")
        commits = payload.get("commits", [])
        commit_count = len(commits)

        if commits:
            latest_commit = commits[-1]
            commit_sha = latest_commit.get("id", "")
            commit_details = self.github.get_commit_details(
                repo_owner, repo_name, commit_sha
            )

            if commit_details:
                include_diff = (
                    os.environ.get("INCLUDE_DIFF_CONTENT", "false").lower() == "true"
                )

                message = f"""🚀 {commit_count} new commit{'s' if commit_count != 1 else ''} pushed to {repo_name} by {pusher}

Latest commit: {commit_details.get('message', 'No message')}
Author: {commit_details.get('author', pusher)}
Files changed: {commit_details.get('files_changed', 0)} (+{commit_details.get('additions', 0)} -{commit_details.get('deletions', 0)})
Modified files: {', '.join(commit_details.get('files', []))}"""

                if include_diff:
                    diff_content = self.github.get_commit_diff(
                        repo_owner, repo_name, commit_sha
                    )
                    if diff_content:
                        message += f"\n\nChanges:\n```\n{diff_content}\n```"

                message += f"\n\nView commit: {commit_details.get('url', '')}"
                return message
            else:
                return f"🚀 {commit_count} new commit{'s' if commit_count != 1 else ''} pushed to {repo_name} by {pusher}"
        else:
            return f"🚀 Push event to {repo_name} by {pusher}"

    def handle_pull_request(self, payload: Dict[str, Any]) -> str:
        """Handle pull request events"""
        action = payload.get("action", "unknown")
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        repo_owner = repo_info.get("owner", {}).get("login", "unknown")

        pr_data = payload.get("pull_request", {})
        pr_number = pr_data.get("number", 0)
        pr_title = pr_data.get("title", "")
        pr_user = pr_data.get("user", {}).get("login", "someone")

        pr_details = self.github.get_pull_request_details(
            repo_owner, repo_name, pr_number
        )

        if pr_details:
            body = pr_details.get("body", "")
            body_preview = body[:200] + "..." if body else "No description"

            return f"""📝 PR #{pr_number} {action} in {repo_name} by {pr_user}

Title: {pr_details.get('title', pr_title)}
Branch: {pr_details.get('head_branch', 'unknown')} → {pr_details.get('base_branch', 'main')}
Files changed: {pr_details.get('files_changed', 0)} (+{pr_details.get('additions', 0)} -{pr_details.get('deletions', 0)})
State: {pr_details.get('state', 'unknown')}

{body_preview}

View PR: {pr_details.get('url', '')}"""
        else:
            return (
                f"📝 PR #{pr_number} {action} in {repo_name} by {pr_user}: {pr_title}"
            )

    def handle_issues(self, payload: Dict[str, Any]) -> str:
        """Handle issue events"""
        action = payload.get("action", "unknown")
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        repo_owner = repo_info.get("owner", {}).get("login", "unknown")

        issue_data = payload.get("issue", {})
        issue_number = issue_data.get("number", 0)
        issue_title = issue_data.get("title", "")
        issue_user = issue_data.get("user", {}).get("login", "someone")

        issue_details = self.github.get_issue_details(
            repo_owner, repo_name, issue_number
        )

        if issue_details:
            labels_str = ", ".join(issue_details.get("labels", [])) or "None"
            assignees_str = (
                ", ".join(issue_details.get("assignees", [])) or "Unassigned"
            )
            body = issue_details.get("body", "")
            body_preview = body[:200] + "..." if body else "No description"

            return f"""🐛 Issue #{issue_number} {action} in {repo_name} by {issue_user}

Title: {issue_details.get('title', issue_title)}
State: {issue_details.get('state', 'unknown')}
Labels: {labels_str}
Assignees: {assignees_str}
Comments: {issue_details.get('comments', 0)}

{body_preview}

View issue: {issue_details.get('url', '')}"""
        else:
            return f"🐛 Issue #{issue_number} {action} in {repo_name} by {issue_user}: {issue_title}"

    def handle_create(self, payload: Dict[str, Any]) -> str:
        """Handle branch/tag creation events"""
        ref_type = payload.get("ref_type", "unknown")
        ref_name = payload.get("ref", "unknown")
        creator = payload.get("sender", {}).get("login", "someone")
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        repo_owner = repo_info.get("owner", {}).get("login", "unknown")

        if ref_type == "branch":
            default_branch = repo_info.get("default_branch", "main")
            return f"""🌿 New branch '{ref_name}' created in {repo_name} by {creator}

Branch: {ref_name}
Branched from: {default_branch} (likely)
Repository: {repo_name}

View branch: https://github.com/{repo_owner}/{repo_name}/tree/{ref_name}"""

        elif ref_type == "tag":
            return f"""🏷️ New tag '{ref_name}' created in {repo_name} by {creator}

Tag: {ref_name}
Repository: {repo_name}

View tag: https://github.com/{repo_owner}/{repo_name}/releases/tag/{ref_name}"""

        else:
            return f"📫 New {ref_type} '{ref_name}' created in {repo_name} by {creator}"

    def handle_delete(self, payload: Dict[str, Any]) -> str:
        """Handle branch/tag deletion events"""
        ref_type = payload.get("ref_type", "unknown")
        ref_name = payload.get("ref", "unknown")
        deleter = payload.get("sender", {}).get("login", "someone")
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")

        return f"""🗑️ {ref_type.title()} '{ref_name}' deleted from {repo_name} by {deleter}

Deleted {ref_type}: {ref_name}
Repository: {repo_name}"""

    def handle_unknown(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Handle unknown event types"""
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        return f"📫 GitHub {event_type} event in {repo_name}"

    def process_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Process a webhook event and send to Poke"""
        handlers = {
            "push": self.handle_push,
            "pull_request": self.handle_pull_request,
            "issues": self.handle_issues,
            "create": self.handle_create,
            "delete": self.handle_delete,
        }

        handler = handlers.get(event_type, lambda p: self.handle_unknown(event_type, p))
        message = handler(payload)

        success = self.poke.send_message(message)

        if success:
            print(f"✅ Forwarded to Poke: {message}")
        else:
            print(f"❌ Failed to forward: {message}")

        return success
