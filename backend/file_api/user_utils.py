"""
User identification utilities for multi-user support
"""
from typing import Optional
from fastapi import Request, WebSocket, HTTPException
import logging

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "default"


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from request headers.
    Returns DEFAULT_USER_ID if X-User-Id header is not present.

    Args:
        request: FastAPI Request object

    Returns:
        User ID string
    """
    user_id = request.headers.get("x-user-id")
    if not user_id:
        logger.warning("X-User-Id header not found in request, using default user ID")
        return DEFAULT_USER_ID
    return user_id


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
