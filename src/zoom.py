"""Вспомогательные функции для работы с Zoom API."""

from __future__ import annotations

from typing import Any, Mapping

import base64
import time

import requests

from . import config

_API_URL = "https://api.zoom.us/v2"

_TOKEN: str | None = None
_EXPIRES_AT: float = 0.0


class ZoomAPIError(Exception):
    """Вызывается, когда Zoom API возвращает ошибку."""


def get_access_token() -> str:
    """Вернуть действительный OAuth‑токен, обновляя его при необходимости."""
    global _TOKEN, _EXPIRES_AT

    now = time.time()
    if _TOKEN and now < _EXPIRES_AT - 30:
        return _TOKEN

    client_id = config.get("ZOOM_CLIENT_ID") or config.get("zoom_client_id")
    client_secret = config.get("ZOOM_CLIENT_SECRET") or config.get("zoom_client_secret")
    account_id = config.get("ZOOM_ACCOUNT_ID") or config.get("zoom_account_id")

    if not (client_id and client_secret and account_id):
        raise ZoomAPIError("Zoom OAuth credentials not configured")

    creds = f"{client_id}:{client_secret}".encode()
    headers = {
        "Authorization": f"Basic {base64.b64encode(creds).decode()}",
    }

    params = {
        "grant_type": "account_credentials",
        "account_id": account_id,
    }

    url = "https://zoom.us/oauth/token"
    resp = requests.post(url, headers=headers, params=params, timeout=10)
    if resp.status_code >= 400:
        raise ZoomAPIError(f"Token request failed: {resp.text}")

    data = resp.json()
    _TOKEN = data.get("access_token")
    expires_in = int(data.get("expires_in", 0))
    _EXPIRES_AT = now + expires_in
    if not _TOKEN:
        raise ZoomAPIError("Zoom token missing in response")

    return _TOKEN

def _auth_headers() -> dict[str, str]:
    token = get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_meeting(payload: Mapping[str, Any]) -> str:
    """Создать встречу в Zoom и вернуть ссылку для подключения."""
    url = f"{_API_URL}/users/me/meetings"
    response = requests.post(url, headers=_auth_headers(), json=payload, timeout=10)
    if response.status_code >= 400:
        raise ZoomAPIError(f"Zoom API error: {response.text}")
    data = response.json()
    return data.get("join_url", "")


def schedule_meeting(user_info: Mapping[str, Any]) -> str:
    """Запланировать встречу для пользователя и вернуть ссылку."""
    payload = {
        "topic": f"Interview with {user_info.get('name', '')}",
        "type": 1,  # мгновенная встреча
    }
    return create_meeting(payload)
