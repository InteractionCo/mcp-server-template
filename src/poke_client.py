#!/usr/bin/env python3
"""
Poke API client for sending notifications.
"""
import os
import requests
from typing import Dict, Any


class PokeClient:
    """Client for sending messages to Poke API"""

    def __init__(self):
        self.api_key = os.environ.get("POKE_API_KEY")
        self.api_url = os.environ.get("POKE_API_URL")

    def send_message(self, message: str) -> bool:
        """
        Send a message to Poke API.
        Returns True if message sent successfully, False otherwise.
        """
        if not self.api_key or not self.api_url:
            print("ERROR: Missing Poke API credentials")
            return False

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"message": message}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send to Poke: {e}")
            return False

    def test_connection(self, test_message: str) -> Dict[str, Any]:
        """
        Test function to send a message directly to Poke API.
        Used for debugging and verifying the Poke integration works.
        """
        if not self.api_key or not self.api_url:
            return {"error": "Missing POKE_API_KEY or POKE_API_URL in environment"}

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"message": test_message}
            )

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json() if response.content else "No content"
            }
        except Exception as e:
            return {"error": f"Failed to send message: {str(e)}"}