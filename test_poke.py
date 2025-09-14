#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_poke_api():
    api_key = os.environ.get("POKE_API_KEY")
    api_url = os.environ.get("POKE_API_URL")

    if not api_key or not api_url:
        print("ERROR: Missing POKE_API_KEY or POKE_API_URL in .env file")
        return

    print(f"Testing Poke API...")
    print(f"URL: {api_url}")
    print(f"API Key: {api_key[:8]}...")

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "message": "🚀 Hello from GitHub-Poke Bridge test! This is STILL working, right?"
            },
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS: Message sent to Poke!")
        else:
            print("❌ FAILED: Check your API key and try again")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


if __name__ == "__main__":
    test_poke_api()
