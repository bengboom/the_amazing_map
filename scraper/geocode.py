from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from .config import CACHE, USER_AGENT


class Geocoder:
    def __init__(self, cache_path: Path | None = None) -> None:
        self.cache_path = cache_path or CACHE / "geocode_cache.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        if self.cache_path.exists():
            self.cache: dict[str, Any] = json.loads(self.cache_path.read_text(encoding="utf-8"))
        else:
            self.cache = {}

    def save(self) -> None:
        self.cache_path.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")

    def geocode(self, location_name: str, city: str, country: str) -> dict[str, float] | None:
        candidates = [
            f"{location_name}, {city}, {country}",
            f"{city}, {country}",
            country,
        ]
        for query in candidates:
            cached = self.cache.get(query)
            if cached:
                return cached
            result = self._lookup(query)
            if result:
                self.cache[query] = result
                self.save()
                time.sleep(1.05)
                return result
        return None

    def _lookup(self, query: str) -> dict[str, float] | None:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return {"lat": float(rows[0]["lat"]), "lng": float(rows[0]["lon"])}
