#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_repo_access():
    """Test direct repository access via GitHub API"""

    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")
    github_token = os.environ.get("GITHUB_TOKEN")

    print(f"Testing repository access: {repo_owner}/{repo_name}")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Poke-Bridge",
    }

    # Test 1: Check if repo exists and is accessible
    print("\n1. Testing repository access...")
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(repo_url, headers=headers)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        repo_data = response.json()
        print(f"✅ Repository exists: {repo_data.get('full_name')}")
        print(f"   Default branch: {repo_data.get('default_branch')}")
        print(f"   Private: {repo_data.get('private')}")
        print(f"   Size: {repo_data.get('size')} KB")
    else:
        print(f"❌ Repository access failed: {response.text}")
        return

    # Test 2: Check repository contents
    print("\n2. Testing repository contents...")
    contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
    response = requests.get(contents_url, headers=headers)

    if response.status_code == 200:
        contents = response.json()
        print(f"✅ Repository contents ({len(contents)} items):")
        for item in contents[:10]:  # Show first 10 items
            print(f"   {item.get('type')}: {item.get('name')}")
    else:
        print(f"❌ Contents access failed: {response.text}")

    # Test 3: Test GitHub Code Search API directly
    print("\n3. Testing GitHub Code Search API...")
    search_url = "https://api.github.com/search/code"

    # Try a simple search
    params = {"q": f"repo:{repo_owner}/{repo_name}", "per_page": 5}

    response = requests.get(search_url, headers=headers, params=params)
    print(f"Search status: {response.status_code}")

    if response.status_code == 200:
        search_data = response.json()
        total_count = search_data.get("total_count", 0)
        items = search_data.get("items", [])
        print(f"✅ Search API working. Total indexed files: {total_count}")

        if total_count > 0:
            print(f"   Sample results:")
            for item in items[:3]:
                print(f"   - {item.get('path')} (score: {item.get('score')})")
        else:
            print("   ℹ️ No indexed content found in this repository")
    else:
        print(f"❌ Search API failed: {response.text}")

    # Test 4: Check if repo has any Python files specifically
    print("\n4. Testing search for Python files...")
    params = {"q": f"extension:py repo:{repo_owner}/{repo_name}", "per_page": 5}

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        search_data = response.json()
        total_count = search_data.get("total_count", 0)
        print(f"Python files found: {total_count}")

        if total_count > 0:
            for item in search_data.get("items", [])[:3]:
                print(f"   - {item.get('path')}")


if __name__ == "__main__":
    test_repo_access()
