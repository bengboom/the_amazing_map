from __future__ import annotations

import time
from pathlib import Path

import requests

from .config import USER_AGENT


def get_with_retries(url: str, attempts: int = 4, timeout: int = 30) -> requests.Response:
    last_error: Exception | None = None
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as exc:  # requests raises several concrete network exceptions.
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def cached_get(url: str, path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    response = get_with_retries(url)
    path.write_text(response.text, encoding="utf-8")
    return response.text
