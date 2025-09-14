#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Add src to path to import GitHub client
sys.path.append("src")
from github_client import GitHubClient

# Load environment variables
load_dotenv()


def test_code_search():
    """Test the GitHub code search functionality directly"""

    # Check environment variables
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")
    github_token = os.environ.get("GITHUB_TOKEN")

    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"GitHub Token: {'✓' if github_token else '✗'}")

    if not repo_owner or not repo_name or not github_token:
        print("❌ ERROR: Missing required environment variables:")
        print("  - GITHUB_REPO_OWNER")
        print("  - GITHUB_REPO_NAME")
        print("  - GITHUB_TOKEN")
        return

    # Test GitHub client initialization
    client = GitHubClient()
    print(f"GitHub client initialized")

    # Test code search
    print("\nTesting code search...")
    result = client.search_code(
        owner=repo_owner,
        repo=repo_name,
        query="function",  # Simple search query
        limit=5,
    )

    print(f"Search result: {result}")

    if result.get("success"):
        print(
            f"✅ Code search successful! Found {result.get('total_count', 0)} results"
        )
        for i, item in enumerate(result.get("results", []), 1):
            print(f"  {i}. {item.get('file_path')} (score: {item.get('score')})")
    else:
        print(f"❌ Code search failed: {result.get('error')}")

    # Test a more specific search
    print("\nTesting specific search for 'def '...")
    result2 = client.search_code(
        owner=repo_owner, repo=repo_name, query="def ", extension="py", limit=3
    )

    print(f"Specific search result: {result2}")


if __name__ == "__main__":
    test_code_search()
