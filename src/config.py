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
    """Return configuration value from environment or config.json.

    The lookup is case insensitive and checks environment variables first.
    """
    variations = {key, key.upper(), key.lower()}
    for variant in variations:
        if variant in os.environ:
            return os.environ[variant]

    for variant in variations:
        if variant in _FILE_CONFIG:
            return _FILE_CONFIG[variant]

    return default
