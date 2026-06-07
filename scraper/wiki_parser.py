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

KNOWN_COUNTRIES = {
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Barbados",
    "Belgium", "Bolivia", "Botswana", "Brazil", "Bulgaria", "Burkina Faso", "Cambodia", "Canada",
    "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Czech Republic", "Denmark", "Dominican Republic",
    "Ecuador", "Egypt", "Estonia", "Ethiopia", "Finland", "France", "French Polynesia", "Georgia",
    "Germany", "Ghana", "Greece", "Guam", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia",
    "Ireland", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Laos",
    "Liechtenstein", "Lithuania", "Macau", "Madagascar", "Malawi", "Malaysia", "Malta", "Mauritius",
    "Mexico", "Monaco", "Mongolia", "Morocco", "Mozambique", "Namibia", "Netherlands", "New Zealand",
    "Norway", "Oman", "Panama", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Puerto Rico", "Romania", "Russia", "Senegal", "Seychelles", "Singapore", "Slovenia", "South Africa",
    "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Taiwan", "Tanzania", "Thailand",
    "Trinidad and Tobago", "Tunisia", "Turkey", "U.S. Virgin Islands", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Vietnam", "Zambia", "Zimbabwe",
}

US_STATE_OR_DISTRICT = {
    "Alabama", "Alaska", "Arizona", "California", "Colorado", "Florida", "Georgia", "Hawaii", "Illinois",
    "Louisiana", "Massachusetts", "Michigan", "Mississippi", "Montana", "Nevada", "New Jersey", "New York",
    "North Carolina", "Oregon", "Pennsylvania", "South Carolina", "Tennessee", "Texas", "Utah", "Virginia",
    "Washington", "Washington, D.C.", "Wyoming",
}

UK_NATIONS = {"England", "Scotland", "Wales", "Northern Ireland"}


def parse_season_html(season: int, html: str, source_url: str) -> list[ParsedLocation]:
    soup = BeautifulSoup(html, "html.parser")
    rows = _parse_leg_location_lists(season, soup, source_url)
    if rows:
        return rows
    rows = _parse_leg_tables(season, soup, source_url)
    if rows:
        return rows
    return _parse_route_summary_text(season, soup, source_url)


def _parse_leg_location_lists(season: int, soup: BeautifulSoup, source_url: str) -> list[ParsedLocation]:
    parsed: list[ParsedLocation] = []
    order = 1
    for heading in soup.select("h3, h4"):
        heading_text = clean_text(heading.get_text(" "))
        if not re.match(r"Leg\s+\d+\b", heading_text, flags=re.I):
            continue
        leg = _first_int(heading_text)
        leg_countries = _countries_from_leg_heading(heading_text)
        location_list = _find_locations_list(heading)
        if not location_list:
            continue
        current_country = leg_countries[0] if leg_countries else None
        for item in location_list.find_all("li", recursive=False):
            row = _parse_location_item(item, current_country, leg_countries)
            if not row:
                continue
            country, city, location_name, loc_type = row
            current_country = country
            parsed.append(
                ParsedLocation(
                    season=season,
                    episode=leg,
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


def _countries_from_leg_heading(text: str) -> list[str]:
    match = re.search(r"\((?P<countries>[^)]+)\)", text)
    if not match:
        return []
    countries = []
    for part in re.split(r"\s*(?:→|&)\s*", match.group("countries")):
        country = _country_from_heading_part(part)
        if country and country not in countries:
            countries.append(country)
    return countries


def _country_from_heading_part(part: str) -> str | None:
    cleaned = canonical_country(part.strip())
    if not cleaned:
        return None
    if cleaned in US_STATE_OR_DISTRICT:
        return "United States"
    if cleaned in UK_NATIONS:
        return "United Kingdom"
    if cleaned in KNOWN_COUNTRIES:
        return cleaned
    return cleaned


def _find_locations_list(heading) -> object | None:
    for sibling in heading.find_all_next():
        if sibling.name in {"h2", "h3", "h4"}:
            return None
        if sibling.name == "dt" and clean_text(sibling.get_text(" ")).casefold() == "locations":
            for candidate in sibling.find_all_next():
                if candidate.name in {"h2", "h3", "h4", "dt"}:
                    return None
                if candidate.name == "ul":
                    return candidate
    return None


def _parse_location_item(item, current_country: str | None, leg_countries: list[str]) -> tuple[str, str, str, str] | None:
    text = clean_text(item.get_text(" "))
    if not text:
        return None
    loc_type = _location_type_from_item(item, text)
    destination_text = _destination_text(text)
    city, country = _city_country_from_links(item, leg_countries)
    if not country:
        country = current_country or (leg_countries[-1] if leg_countries else "")
    if not city:
        city = _city_from_text(destination_text)
    city = canonical_city(city)
    if city in KNOWN_COUNTRIES and city in leg_countries:
        country = city
    if not country or not city:
        return None
    location_name = _location_name_from_text(destination_text, city)
    return canonical_country(country), city, canonical_location(location_name), loc_type


def _location_type_from_item(item, text: str) -> str:
    marker_text = " ".join(
        clean_text(value)
        for tag in item.select("[alt], [title]")
        for value in [tag.get("alt"), tag.get("title")]
        if value
    )
    lowered = f"{text} {marker_text}".casefold()
    if "starting line" in lowered or "start line" in lowered:
        return "start"
    if "finish line" in lowered:
        return "finish_line"
    if "pit stop" in lowered:
        return "pit_stop"
    if "roadblock" in lowered:
        return "roadblock"
    if "detour" in lowered:
        return "detour"
    return "route_info"


def _destination_text(text: str) -> str:
    without_markers = re.sub(r"\b(?:Flight|Train|Bus|Boat|Ferry|Helicopter|Bicycle|Gondola):\s*", "", text, flags=re.I)
    destination = re.split(r"\s+→\s+", without_markers)[-1]
    destination = re.sub(r"\s+(?:Starting Line|Finish Line)\b", "", destination, flags=re.I)
    return clean_text(destination)


def _city_country_from_links(item, leg_countries: list[str]) -> tuple[str | None, str | None]:
    for link in item.find_all("a"):
        label = clean_text(link.get("title") or link.get_text(" "))
        if "," not in label:
            continue
        left, right = [part.strip() for part in label.rsplit(",", 1)]
        country = canonical_country(right)
        if country in leg_countries or country in KNOWN_COUNTRIES:
            return left, country
    return None, None


def _city_from_text(text: str) -> str:
    main = re.split(r"\s*\(", text, maxsplit=1)[0]
    main = re.split(r"\s+[–-]\s+", main)[0]
    if "," in main:
        main = main.rsplit(",", 1)[0]
    return canonical_city(main)


def _location_name_from_text(text: str, city: str) -> str:
    match = re.search(r"\((?P<place>[^)]+)\)", text)
    if not match:
        return city
    place = re.split(r"\s+[–-]\s+", match.group("place"))[-1]
    return place


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
