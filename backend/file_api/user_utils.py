"""
User identification utilities for multi-user support
"""
from typing import Optional
from fastapi import Request, WebSocket, HTTPException
import logging
import re

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "default"


def extract_user_id_from_email(email: str) -> str:
    """
    Extract user ID from email address.
    Converts namae.myouji@xxx.com to namae_myouji.

    Args:
        email: Email address from IAP authentication

    Returns:
        User ID in format namae_myouji
    """
    # Extract the local part (before @)
    local_part = email.split('@')[0]

    # Replace dots with underscores
    user_id = local_part.replace('.', '_')

    # Sanitize to allow only alphanumeric and underscores
    user_id = re.sub(r'[^a-zA-Z0-9_]', '_', user_id)

    return user_id


def get_email_from_iap_headers(request: Request) -> Optional[str]:
    """
    Extract email from IAP (Identity-Aware Proxy) headers.

    Cloud Run with IAP provides user email in the following headers:
    - X-Goog-Authenticated-User-Email: accounts.google.com:user@example.com
    - X-Goog-IAP-JWT-Assertion: JWT token containing email

    Args:
        request: FastAPI Request object

    Returns:
        Email address if found, None otherwise
    """
    # Try X-Goog-Authenticated-User-Email first
    auth_user = request.headers.get("x-goog-authenticated-user-email")
    if auth_user:
        # Format is "accounts.google.com:user@example.com"
        # Extract email part after the colon
        parts = auth_user.split(':', 1)
        if len(parts) == 2:
            email = parts[1]
            logger.info(f"Extracted email from X-Goog-Authenticated-User-Email: {email}")
            return email

    # Fallback to X-Goog-Authenticated-User-Id for development
    # In development, we might not have IAP headers
    logger.warning("No IAP headers found, using default")
    return None


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from request headers.
    Priority order:
    1. IAP headers (X-Goog-Authenticated-User-Email)
    2. X-User-Id header (for backward compatibility)
    3. DEFAULT_USER_ID

    Args:
        request: FastAPI Request object

    Returns:
        User ID string
    """
    # Try to get email from IAP headers first
    email = get_email_from_iap_headers(request)
    if email:
        user_id = extract_user_id_from_email(email)
        logger.info(f"User ID from IAP email: {user_id}")
        return user_id

    # Fallback to X-User-Id header
    user_id = request.headers.get("x-user-id")
    if user_id:
        logger.info(f"User ID from X-User-Id header: {user_id}")
        return user_id

    # Default user ID
    logger.warning("No user identification found, using default user ID")
    return DEFAULT_USER_ID


def get_user_id_from_websocket(websocket: WebSocket) -> str:
    """
    Extract user ID from WebSocket headers.
    Returns DEFAULT_USER_ID if X-User-Id header is not present.

    Args:
        websocket: FastAPI WebSocket object

    Returns:
        User ID string
    """
    user_id = websocket.headers.get("x-user-id")
    if not user_id:
        logger.warning("X-User-Id header not found in WebSocket, using default user ID")
        return DEFAULT_USER_ID
    return user_id


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID format.
    Currently allows alphanumeric characters and hyphens.

    Args:
        user_id: User ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not user_id:
        return False

    # Allow alphanumeric, hyphens, and underscores (UUID format)
    import re
    pattern = r'^[a-zA-Z0-9\-_]+$'
    return bool(re.match(pattern, user_id))


def require_user_id(request: Request) -> str:
    """
    Extract and validate user ID from request.
    Raises HTTPException if user ID is invalid.

    Args:
        request: FastAPI Request object

    Returns:
        Validated user ID string

    Raises:
        HTTPException: If user ID is missing or invalid
    """
    user_id = get_user_id_from_request(request)

    if not validate_user_id(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing X-User-Id header"
        )

    return user_id
