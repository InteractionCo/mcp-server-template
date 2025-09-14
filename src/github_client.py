#!/usr/bin/env python3
"""
GitHub API client for fetching repository data and managing issues/PRs.
"""
import os
import requests
from typing import Dict, Any, Optional


class GitHubClient:
    """Client for interacting with GitHub API"""

    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        """Create authenticated headers for GitHub API requests"""
        return {
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Poke-Bridge"
        }

    def get_commit_diff(self, owner: str, repo: str, commit_sha: str) -> str:
        """Fetch the actual diff content for a commit"""
        try:
            headers = self._get_headers()
            headers["Accept"] = "application/vnd.github.diff"
            url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                text = response.text
                return text[:1500] + "..." if len(text) > 1500 else text
        except Exception as e:
            print(f"Failed to fetch commit diff: {e}")

        return ""

    def get_commit_details(self, owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
        """Fetch detailed commit information"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commit_data = response.json()
                return {
                    "message": commit_data.get("commit", {}).get("message", ""),
                    "author": commit_data.get("commit", {}).get("author", {}).get("name", ""),
                    "files_changed": len(commit_data.get("files", [])),
                    "additions": commit_data.get("stats", {}).get("additions", 0),
                    "deletions": commit_data.get("stats", {}).get("deletions", 0),
                    "files": [f["filename"] for f in commit_data.get("files", [])[:5]],
                    "url": commit_data.get("html_url", "")
                }
        except Exception as e:
            print(f"Failed to enrich commit data: {e}")

        return {}

    def get_pull_request_details(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetch detailed PR information"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                pr_data = response.json()
                body = pr_data.get("body", "")
                return {
                    "title": pr_data.get("title", ""),
                    "body": body[:500] + "..." if len(body) > 500 else body,
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

    def get_issue_details(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetch detailed issue information"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                issue_data = response.json()
                body = issue_data.get("body", "")
                return {
                    "title": issue_data.get("title", ""),
                    "body": body[:300] + "..." if len(body) > 300 else body,
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

    def add_issue_comment(self, owner: str, repo: str, issue_number: int, comment: str) -> Dict[str, Any]:
        """Add a comment to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"

            response = requests.post(url, headers=headers, json={"body": comment})

            if response.status_code == 201:
                return {
                    "success": True,
                    "message": "Comment added successfully",
                    "comment_url": response.json().get("html_url", "")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add comment: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def close_issue(self, owner: str, repo: str, issue_number: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Close a GitHub issue, optionally with a closing comment"""
        try:
            headers = self._get_headers()

            # Add comment if provided
            if comment:
                self.add_issue_comment(owner, repo, issue_number, comment)

            # Close the issue
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            response = requests.patch(url, headers=headers, json={"state": "closed"})

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Issue closed successfully",
                    "issue_url": response.json().get("html_url", "")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to close issue: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def add_issue_labels(self, owner: str, repo: str, issue_number: int, labels: list) -> Dict[str, Any]:
        """Add labels to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"

            response = requests.post(url, headers=headers, json=labels)

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Labels {labels} added successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add labels: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def assign_issue(self, owner: str, repo: str, issue_number: int, assignee: str) -> Dict[str, Any]:
        """Assign a user to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/assignees"

            response = requests.post(url, headers=headers, json={"assignees": [assignee]})

            if response.status_code == 201:
                return {
                    "success": True,
                    "message": f"Issue assigned to {assignee} successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to assign issue: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}