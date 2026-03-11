"""
Security Middleware
Provides rate limiting, API key authentication, and request validation.
"""

import os
from typing import Optional, List
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address


# ── Rate Limiter ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── API Key Authentication (optional) ────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> Optional[str]:
    """
    Verify the API key if API_KEY_REQUIRED is set to 'true'.
    If not required, allows unauthenticated access.
    """
    require_key = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"

    if not require_key:
        return None

    expected_key = os.getenv("API_KEY", "")
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API key authentication is enabled but no API_KEY is configured.",
        )

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key.",
        )

    return api_key


# ── Trusted Host Check ───────────────────────────────────────
ALLOWED_HOSTS_RAW = os.getenv("ALLOWED_HOSTS", "*")


def get_allowed_hosts() -> List[str]:
    """Parse allowed hosts from environment."""
    raw = os.getenv("ALLOWED_HOSTS", "*")
    if raw == "*":
        return ["*"]
    return [h.strip() for h in raw.split(",") if h.strip()]


# ── File Validation Constants ────────────────────────────────
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",  # Some browsers send this
}
