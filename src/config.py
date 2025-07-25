"""Configuration loading utilities."""

from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def _load_file() -> dict:
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError:
            return {}
    return {}


_FILE_CONFIG = _load_file()


def get(key: str, default: str | None = None) -> str | None:
    """Return configuration value from environment or config.json."""
    if key in os.environ:
        return os.environ[key]
    return _FILE_CONFIG.get(key, default)
