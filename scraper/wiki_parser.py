from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from .normalize import canonical_city, canonical_country, canonical_location, clean_text, stable_id


@dataclass
class ParsedLocation:
    season: int
    episode: int | None
    leg: int | None
    country: str
    city: str
    location_name: str
    type: str
    order: int
    source_url: str


LOCATION_TYPES = {
    "pit stop": "pit_stop",
    "roadblock": "roadblock",
    "detour": "detour",
    "route info": "route_info",
    "start": "start",
    "finish": "finish_line",
}


def parse_season_html(season: int, html: str, source_url: str) -> list[ParsedLocation]:
    soup = BeautifulSoup(html, "html.parser")
    rows = _parse_leg_tables(season, soup, source_url)
    if rows:
        return rows
    return _parse_route_summary_text(season, soup, source_url)


def _parse_leg_tables(season: int, soup: BeautifulSoup, source_url: str) -> list[ParsedLocation]:
    parsed: list[ParsedLocation] = []
    order = 1
    for table in soup.select("table.wikitable"):
        headers = [clean_text(cell.get_text(" ")) for cell in table.select("tr th")]
        header_text = " ".join(headers).casefold()
        if not any(token in header_text for token in ["leg", "destination", "pit stop", "episode", "airdate", "roadblock", "detour"]):
            continue
        for row in table.select("tr"):
            cells = [clean_text(cell.get_text(" ")) for cell in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            leg = _first_int(cells[0])
            episode = _find_labeled_int(cells, "episode") or leg
            row_text = " | ".join(cells)
            for country, city, location_name, loc_type in _extract_locations_from_row(row_text):
                parsed.append(
                    ParsedLocation(
                        season=season,
                        episode=episode,
                        leg=leg,
                        country=country,
                        city=city,
                        location_name=location_name,
                        type=loc_type,
                        order=order,
                        source_url=source_url,
                    )
                )
                order += 1
    return _dedupe(parsed)


def _parse_route_summary_text(season: int, soup: BeautifulSoup, source_url: str) -> list[ParsedLocation]:
    parsed: list[ParsedLocation] = []
    order = 1
    route_heading = soup.find(id=re.compile("Route|Locations|Results", re.I))
    container = route_heading.find_parent() if route_heading else soup
    text = clean_text(container.get_text(" "))
    for country, city, location_name, loc_type in _extract_locations_from_row(text):
        parsed.append(
            ParsedLocation(
                season=season,
                episode=order,
                leg=order,
                country=country,
                city=city,
                location_name=location_name,
                type=loc_type,
                order=order,
                source_url=source_url,
            )
        )
        order += 1
    return _dedupe(parsed)


def _extract_locations_from_row(text: str) -> list[tuple[str, str, str, str]]:
    found: list[tuple[str, str, str, str]] = []
    segments = re.split(r"\s*(?:→|–|—|;|\||\n)\s*", text)
    for segment in segments:
        if not segment or len(segment) < 4:
            continue
        loc_type = "route_info"
        lowered = segment.casefold()
        for token, mapped in LOCATION_TYPES.items():
            if token in lowered:
                loc_type = mapped
                break
        # Common page phrasing: "Tokyo, Japan (Shibuya Crossing)".
        match = re.search(r"(?P<city>[A-Z][A-Za-z .'\-]+),\s*(?P<country>[A-Z][A-Za-z .'\-]+)(?:\s*\((?P<place>[^)]+)\))?", segment)
        if match:
            city = canonical_city(match.group("city"))
            country = canonical_country(match.group("country"))
            place = canonical_location(match.group("place") or city)
            found.append((country, city, place, loc_type))
    return found


def _dedupe(rows: list[ParsedLocation]) -> list[ParsedLocation]:
    seen: set[str] = set()
    result: list[ParsedLocation] = []
    for row in rows:
        key = stable_id(row.season, row.episode, row.leg, row.country, row.city, row.location_name, row.type)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _first_int(value: str) -> int | None:
    match = re.search(r"\d+", value)
    return int(match.group()) if match else None


def _find_labeled_int(cells: list[str], label: str) -> int | None:
    for cell in cells:
        if label.casefold() in cell.casefold():
            return _first_int(cell)
    return None
