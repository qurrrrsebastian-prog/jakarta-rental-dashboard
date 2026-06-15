"""
Security utilities. Author: Avatar Putra Sigit.
"""
import re
import html
import hashlib
from typing import Optional


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitize user input to prevent XSS and injection."""
    if not isinstance(text, str):
        return ""
    # HTML escape
    text = html.escape(text)
    # Remove potential SQL injection patterns (basic)
    text = re.sub(r"(--|;|/\*|\*/|DROP|DELETE|INSERT|UPDATE)", "", text, flags=re.IGNORECASE)
    # Length limit
    return text.strip()[:max_length]


def mask_api_key(key: Optional[str]) -> str:
    """Mask API key for display/logging."""
    if not key or len(key) < 12:
        return "***"
    return key[:8] + "..." + key[-4:]


def validate_file_upload(filename: str) -> bool:
    """Validate uploaded file extension."""
    allowed = {".csv", ".txt", ".json", ".pdf", ".png", ".jpg"}
    return any(filename.lower().endswith(ext) for ext in allowed)


def generate_session_id() -> str:
    """Generate random session ID."""
    import secrets
    return secrets.token_hex(8)
