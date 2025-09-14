#!/usr/bin/env python3
"""
Security utilities for webhook validation and request sanitization.
"""
import hashlib
import hmac
from typing import Dict, Any


def validate_github_signature(
    payload_body: bytes, signature_header: str, secret: str
) -> bool:
    """Validate GitHub webhook signature using HMAC-SHA256"""
    if not signature_header:
        return False

    try:
        hash_object = hmac.new(
            secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception:
        return False


def sanitize_payload(payload: dict) -> Dict[str, Any]:
    """Basic payload sanitization and validation"""
    if not isinstance(payload, dict):
        return {}

    # Ensure required fields exist and are strings
    safe_payload = {}
    string_fields = ["repository.name", "repository.owner.login", "sender.login"]

    for field_path in string_fields:
        keys = field_path.split(".")
        value = payload
        try:
            for key in keys:
                value = value.get(key, {})
            if isinstance(value, str) and len(value) < 100:  # Length limit
                safe_payload[field_path] = value[:100]  # Truncate if needed
        except (AttributeError, TypeError):
            continue

    return safe_payload
