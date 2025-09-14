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
            "User-Agent": "GitHub-Poke-Bridge",
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

    def get_commit_details(
        self, owner: str, repo: str, commit_sha: str
    ) -> Dict[str, Any]:
        """Fetch detailed commit information"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commit_data = response.json()
                return {
                    "message": commit_data.get("commit", {}).get("message", ""),
                    "author": commit_data.get("commit", {})
                    .get("author", {})
                    .get("name", ""),
                    "files_changed": len(commit_data.get("files", [])),
                    "additions": commit_data.get("stats", {}).get("additions", 0),
                    "deletions": commit_data.get("stats", {}).get("deletions", 0),
                    "files": [f["filename"] for f in commit_data.get("files", [])[:5]],
                    "url": commit_data.get("html_url", ""),
                }
        except Exception as e:
            print(f"Failed to enrich commit data: {e}")

        return {}

    def get_pull_request_details(
        self, owner: str, repo: str, pr_number: int
    ) -> Dict[str, Any]:
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
                    "url": pr_data.get("html_url", ""),
                }
        except Exception as e:
            print(f"Failed to enrich PR data: {e}")

        return {}

    def get_issue_details(
        self, owner: str, repo: str, issue_number: int
    ) -> Dict[str, Any]:
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
                    "assignees": [
                        assignee["login"]
                        for assignee in issue_data.get("assignees", [])
                    ],
                    "comments": issue_data.get("comments", 0),
                    "url": issue_data.get("html_url", ""),
                }
        except Exception as e:
            print(f"Failed to enrich issue data: {e}")

        return {}

    def add_issue_comment(
        self, owner: str, repo: str, issue_number: int, comment: str
    ) -> Dict[str, Any]:
        """Add a comment to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"

            response = requests.post(url, headers=headers, json={"body": comment})

            if response.status_code == 201:
                return {
                    "success": True,
                    "message": "Comment added successfully",
                    "comment_url": response.json().get("html_url", ""),
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add comment: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def close_issue(
        self, owner: str, repo: str, issue_number: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
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
                    "issue_url": response.json().get("html_url", ""),
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to close issue: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def add_issue_labels(
        self, owner: str, repo: str, issue_number: int, labels: list
    ) -> Dict[str, Any]:
        """Add labels to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"

            response = requests.post(url, headers=headers, json=labels)

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Labels {labels} added successfully",
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add labels: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def assign_issue(
        self, owner: str, repo: str, issue_number: int, assignee: str
    ) -> Dict[str, Any]:
        """Assign a user to a GitHub issue"""
        try:
            headers = self._get_headers()
            url = (
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/assignees"
            )

            response = requests.post(
                url, headers=headers, json={"assignees": [assignee]}
            )

            if response.status_code == 201:
                return {
                    "success": True,
                    "message": f"Issue assigned to {assignee} successfully",
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to assign issue: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def search_code(
        self,
        owner: str,
        repo: str,
        query: str,
        extension: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search for code within a specific repository"""
        try:
            headers = self._get_headers()

            # First, try GitHub's search API
            search_query = f"{query} repo:{owner}/{repo}"
            if extension:
                search_query += f" extension:{extension}"
            if path:
                search_query += f" path:{path}"

            url = f"{self.base_url}/search/code"
            params = {
                "q": search_query,
                "per_page": min(limit, 100),  # GitHub API max is 100
                "sort": "indexed",
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_count", 0)

                # If search API has results, use them
                if total_count > 0:
                    results = []
                    for item in data.get("items", []):
                        results.append(
                            {
                                "file_path": item.get("path", ""),
                                "file_url": item.get("html_url", ""),
                                "repository": item.get("repository", {}).get(
                                    "full_name", f"{owner}/{repo}"
                                ),
                                "score": item.get("score", 0),
                            }
                        )

                    return {
                        "success": True,
                        "total_count": total_count,
                        "results": results,
                    }

                # If search API returns 0 results, fall back to contents API
                print(f"Search API returned 0 results, falling back to contents API...")
                return self._search_code_via_contents(owner, repo, query, extension, path, limit)
            else:
                # If search API fails, fall back to contents API
                print(f"Search API failed with {response.status_code}, falling back to contents API...")
                return self._search_code_via_contents(owner, repo, query, extension, path, limit)

        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}

    def _search_code_via_contents(
        self,
        owner: str,
        repo: str,
        query: str,
        extension: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Fallback search using Contents API and local file content search"""
        try:
            import re
            import base64

            results = []
            search_pattern = re.compile(re.escape(query), re.IGNORECASE)

            # Get all files from the repository
            all_files = self._get_all_repository_files(owner, repo, path)

            # Filter by extension if specified
            if extension:
                ext_filter = f".{extension}" if not extension.startswith('.') else extension
                all_files = [f for f in all_files if f.endswith(ext_filter)]

            files_searched = 0
            matches_found = 0

            for file_path in all_files[:100]:  # Limit to avoid API rate limits
                if len(results) >= limit:
                    break

                files_searched += 1

                # Get file content
                file_content_result = self.get_file_content(owner, repo, file_path)
                if file_content_result.get('success') and file_content_result.get('content'):
                    content = file_content_result.get('content', '')

                    # Search for query in content
                    if search_pattern.search(content):
                        matches_found += 1
                        results.append({
                            "file_path": file_path,
                            "file_url": f"https://github.com/{owner}/{repo}/blob/main/{file_path}",
                            "repository": f"{owner}/{repo}",
                            "score": 1.0,  # Simple scoring
                            "search_method": "contents_api",
                        })

            return {
                "success": True,
                "total_count": matches_found,
                "results": results,
                "search_info": {
                    "method": "contents_api",
                    "files_searched": files_searched,
                    "matches_found": matches_found,
                    "note": "Repository not indexed by GitHub search, used Contents API fallback"
                }
            }

        except Exception as e:
            return {"success": False, "error": f"Contents API fallback failed: {str(e)}"}

    def _get_all_repository_files(self, owner: str, repo: str, path_filter: Optional[str] = None) -> list:
        """Recursively get all file paths from repository"""
        try:
            files = []
            headers = self._get_headers()

            def get_contents_recursive(path=""):
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    items = response.json()
                    if isinstance(items, list):
                        for item in items:
                            if item.get("type") == "file":
                                file_path = item.get("path", "")
                                if not path_filter or path_filter in file_path:
                                    files.append(file_path)
                            elif item.get("type") == "dir":
                                get_contents_recursive(item.get("path", ""))

            get_contents_recursive()
            return files

        except Exception as e:
            print(f"Error getting repository files: {e}")
            return []

    def get_file_content(
        self, owner: str, repo: str, file_path: str, ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the content of a specific file from the repository"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"

            params = {}
            if ref:
                params["ref"] = ref

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()

                # Handle files vs directories
                if isinstance(data, dict) and data.get("type") == "file":
                    import base64

                    content = ""
                    if data.get("encoding") == "base64":
                        try:
                            content = base64.b64decode(data.get("content", "")).decode(
                                "utf-8"
                            )
                        except:
                            content = "[Binary file - cannot display content]"

                    return {
                        "success": True,
                        "content": content,
                        "file_path": data.get("path", file_path),
                        "size": data.get("size", 0),
                        "sha": data.get("sha", ""),
                        "url": data.get("html_url", ""),
                    }
                else:
                    return {
                        "success": False,
                        "error": "Path is not a file or file not found",
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get file content: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}
