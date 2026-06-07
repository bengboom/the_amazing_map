from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path
from typing import Any

import geonamescache
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
        self._offline_index, self._country_index = self._build_offline_index()

    def save(self) -> None:
        self.cache_path.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")

    def geocode(self, location_name: str, city: str, country: str) -> dict[str, float] | None:
        query = f"{city}, {country}"
        cached = self.cache.get(query)
        if cached and not _is_zero_coord(cached):
            return cached
        result = self._lookup_offline(city, country) or self.cache.get(country) or self._country_index.get(country)
        if result:
            self.cache[query] = result
            self.save()
            return result
        return None

    def _build_offline_index(self) -> tuple[dict[tuple[str, str], dict[str, float]], dict[str, dict[str, float]]]:
        cache = geonamescache.GeonamesCache()
        countries_by_name = cache.get_countries_by_names()
        country_codes = {name: row["iso"] for name, row in countries_by_name.items()}
        country_codes.update(
            {
                "Czech Republic": "CZ",
                "French Polynesia": "PF",
                "Guam": "GU",
                "Hong Kong": "HK",
                "Macau": "MO",
                "Puerto Rico": "PR",
                "Russia": "RU",
                "South Korea": "KR",
                "Taiwan": "TW",
                "U.S. Virgin Islands": "VI",
                "United States": "US",
            }
        )
        names_by_iso: dict[str, list[str]] = {}
        for country_name, iso in country_codes.items():
            names_by_iso.setdefault(iso, []).append(country_name)

        index: dict[tuple[str, str], dict[str, float]] = {}
        cities = cache.get_cities().values()
        for city in cities:
            country_code = city.get("countrycode")
            names = [city.get("name", ""), *city.get("alternatenames", [])]
            coords = {"lat": float(city["latitude"]), "lng": float(city["longitude"])}
            for country_name in names_by_iso.get(country_code, []):
                for name in names:
                    key = (_fold(str(name)), country_name)
                    index.setdefault(key, coords)

        country_index: dict[str, dict[str, float]] = {}
        for country_name, row in countries_by_name.items():
            capital = row.get("capital")
            if not capital:
                continue
            coords = index.get((_fold(capital), country_name))
            if coords:
                country_index[country_name] = coords
        manual_country_coords = {
            "Hong Kong": {"lat": 22.3193, "lng": 114.1694},
            "Macau": {"lat": 22.1987, "lng": 113.5439},
            "Netherlands": {"lat": 52.3676, "lng": 4.9041},
        }
        country_index.update(manual_country_coords)
        for alias, canonical in {"Czech Republic": "Czechia", "Russia": "Russian Federation", "South Korea": "South Korea"}.items():
            if canonical in country_index:
                country_index[alias] = country_index[canonical]
        return index, country_index

    def _lookup_offline(self, city: str, country: str) -> dict[str, float] | None:
        return self._offline_index.get((_fold(city), country))

    def _lookup(self, query: str) -> dict[str, float] | None:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
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
            except Exception as exc:
                last_error = exc
                time.sleep(2**attempt)
        print(f"Geocoding failed for {query}: {last_error}")
        return None


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return normalized.casefold().strip()


def _is_zero_coord(value: Any) -> bool:
    return isinstance(value, dict) and float(value.get("lat", 0)) == 0 and float(value.get("lng", 0)) == 0
