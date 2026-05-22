from __future__ import annotations

import re
import unicodedata

COUNTRY_ALIASES = {
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "uae": "United Arab Emirates",
    "south korea": "South Korea",
    "republic of korea": "South Korea",
    "czech republic": "Czech Republic",
}

CITY_ALIASES = {
    "nyc": "New York City",
    "new york": "New York City",
    "bombay": "Mumbai",
    "saigon": "Ho Chi Minh City",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"\[[^\]]+\]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(" \n\t:-")


def canonical_country(value: str) -> str:
    cleaned = clean_text(value)
    key = cleaned.casefold()
    return COUNTRY_ALIASES.get(key, cleaned)


def canonical_city(value: str) -> str:
    cleaned = clean_text(value)
    key = cleaned.casefold()
    return CITY_ALIASES.get(key, cleaned)


def canonical_location(value: str) -> str:
    cleaned = clean_text(value)
    cleaned = re.sub(r"^(pit stop|roadblock|detour|route info)\s*[:\-]\s*", "", cleaned, flags=re.I)
    return cleaned or "Unknown location"


def stable_id(*parts: object) -> str:
    raw = "-".join(str(part) for part in parts if part is not None)
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    raw = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return raw
