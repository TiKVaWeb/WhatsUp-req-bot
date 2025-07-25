"""Zoom API helper functions."""

from __future__ import annotations

from typing import Any, Mapping

import requests

from . import config

_API_URL = "https://api.zoom.us/v2"


class ZoomAPIError(Exception):
    """Raised when Zoom API returns an error."""


def _auth_headers() -> dict[str, str]:
    token = config.get("ZOOM_JWT_TOKEN") or config.get("zoom_jwt_token")
    if not token:
        raise ZoomAPIError("Zoom JWT token not configured")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_meeting(payload: Mapping[str, Any]) -> str:
    """Create a Zoom meeting and return the join URL."""
    url = f"{_API_URL}/users/me/meetings"
    response = requests.post(url, headers=_auth_headers(), json=payload, timeout=10)
    if response.status_code >= 400:
        raise ZoomAPIError(f"Zoom API error: {response.text}")
    data = response.json()
    return data.get("join_url", "")


def schedule_meeting(user_info: Mapping[str, Any]) -> str:
    """Schedule a meeting for a user and return the join link."""
    payload = {
        "topic": f"Interview with {user_info.get('name', '')}",
        "type": 1,  # instant meeting
    }
    return create_meeting(payload)
