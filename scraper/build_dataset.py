from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper.config import PROCESSED, RAW, ROOT, SEASON_COLORS, WIKIPEDIA_SEASON_URL
from scraper.fandom import fetch_fandom_locations
from scraper.geocode import Geocoder
from scraper.http_client import cached_get
from scraper.normalize import stable_id
from scraper.wiki_parser import ParsedLocation, parse_season_html
from backend.app.data_store import aggregate_countries, stats

MAX_SEASONS_TO_PROBE = 60
MIN_LOCATIONS_PER_SEASON = 10
FRONTEND_DATA = ROOT / "frontend" / "public" / "data"
LOCATION_OVERRIDES = {
    (1, "Trapper Creek"): {
        "country": "United States",
        "lat": 62.3463115,
        "lng": -150.3925522,
    }
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    seasons = discover_available_seasons()
    geocoder = Geocoder()
    locations = []
    for season in seasons:
        url = WIKIPEDIA_SEASON_URL.format(season=season)
        html = cached_get(url, RAW / f"wiki_season_{season}.html")
        parsed = parse_season_html(season, html, url)
        if len(parsed) < MIN_LOCATIONS_PER_SEASON:
            try:
                parsed = fetch_fandom_locations(season)
            except Exception as exc:
                print(f"Skipping season {season}: Wikipedia yielded {len(parsed)} locations and Fandom fallback failed ({exc}).")
                parsed = []
        if len(parsed) < MIN_LOCATIONS_PER_SEASON:
            print(f"Skipping season {season}: only {len(parsed)} parsed locations.")
            continue
        locations.extend(enrich_locations(parsed, geocoder))
    if not locations:
        print("No locations parsed; leaving existing processed data untouched.")
        return
    locations = collapse_consecutive_city_locations(locations)
    routes = build_routes(locations)
    season_rows = build_seasons(locations)
    countries_geojson = build_country_centroid_geojson(locations)
    country_rows = aggregate_countries(locations)
    stats_row = stats(locations, routes)
    write_json(PROCESSED / "locations.json", locations)
    write_json(PROCESSED / "routes.json", routes)
    write_json(PROCESSED / "seasons.json", season_rows)
    write_json(PROCESSED / "countries.geojson", countries_geojson)
    write_static_frontend_data(season_rows, locations, routes, country_rows, stats_row)
    pd.DataFrame(locations).to_csv(PROCESSED / "locations.csv", index=False)
    pd.DataFrame(routes).to_csv(PROCESSED / "routes.csv", index=False)
    print(f"Wrote {len(locations)} locations, {len(routes)} routes, {len(season_rows)} seasons.")


def discover_available_seasons() -> list[int]:
    available = []
    misses = 0
    for season in range(1, MAX_SEASONS_TO_PROBE + 1):
        try:
            cached_get(WIKIPEDIA_SEASON_URL.format(season=season), RAW / f"wiki_season_{season}.html")
            available.append(season)
            misses = 0
        except Exception:
            misses += 1
            if misses >= 4 and season > 35:
                break
    return available


def enrich_locations(rows: list[ParsedLocation], geocoder: Geocoder) -> list[dict[str, object]]:
    enriched = []
    for row in rows:
        row_data = asdict(row)
        override = LOCATION_OVERRIDES.get((row.season, row.city))
        if override:
            row_data.update({key: value for key, value in override.items() if key not in {"lat", "lng"}})
            coords = {"lat": override["lat"], "lng": override["lng"]}
        else:
            coords = geocoder.geocode(row.location_name, row.city, row.country) or {"lat": 0.0, "lng": 0.0}
        enriched.append(
            {
                **row_data,
                "id": stable_id("s", row.season, "o", row.order, row_data["country"], row.city, row.location_name),
                "lat": coords["lat"],
                "lng": coords["lng"],
                "continent": continent_for_country(str(row_data["country"])),
            }
        )
    return enriched


def collapse_consecutive_city_locations(locations: list[dict[str, object]]) -> list[dict[str, object]]:
    collapsed: list[dict[str, object]] = []
    for season in sorted({int(row["season"]) for row in locations}):
        rows = sorted((row for row in locations if int(row["season"]) == season), key=lambda row: int(row["order"]))
        selected: list[dict[str, object]] = []
        start_row = next((row for row in rows if row.get("type") == "start"), rows[0] if rows else None)
        if start_row:
            selected.append({**start_row, "type": "start"})
        for leg in sorted({int(row["leg"]) for row in rows if row.get("leg") is not None}):
            leg_rows = [row for row in rows if row.get("leg") == leg]
            terminal = _terminal_city_for_leg(leg_rows)
            if terminal:
                selected.append(terminal)
        for row in rows:
            if row.get("type") == "finish_line" and row not in selected:
                selected.append(row)

        city_rows: list[dict[str, object]] = []
        for row in selected:
            if city_rows and _same_city(city_rows[-1], row):
                city_rows[-1] = _merge_city_rows(city_rows[-1], row)
            else:
                city_rows.append(row)

        for order, row in enumerate(city_rows, start=1):
            city = str(row["city"])
            country = str(row["country"])
            collapsed.append(
                {
                    "id": stable_id("s", season, "city", order, country, city),
                    "season": season,
                    "episode": row.get("episode"),
                    "leg": row.get("leg"),
                    "country": country,
                    "city": city,
                    "location_name": city,
                    "lat": row["lat"],
                    "lng": row["lng"],
                    "type": row.get("type", "route_info"),
                    "order": order,
                    "continent": row.get("continent"),
                    "source_url": row.get("source_url"),
                }
            )
    return collapsed


def _terminal_city_for_leg(rows: list[dict[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    for wanted_type in ("finish_line", "pit_stop"):
        matches = [row for row in rows if row.get("type") == wanted_type]
        if matches:
            return matches[-1]
    return rows[-1]


def _merge_city_rows(previous: dict[str, object], current: dict[str, object]) -> dict[str, object]:
    merged = dict(previous)
    if current.get("type") == "finish_line" or previous.get("type") == "start":
        merged["type"] = current.get("type")
        merged["episode"] = current.get("episode")
        merged["leg"] = current.get("leg")
    return merged


def _same_city(left: dict[str, object], right: dict[str, object]) -> bool:
    return str(left.get("city", "")).casefold() == str(right.get("city", "")).casefold() and str(left.get("country", "")).casefold() == str(right.get("country", "")).casefold()


def build_routes(locations: list[dict[str, object]]) -> list[dict[str, object]]:
    routes = []
    for season, rows in pd.DataFrame(locations).sort_values(["season", "order"]).groupby("season"):
        records = rows.to_dict("records")
        for index in range(len(records) - 1):
            start = records[index]
            end = records[index + 1]
            if _same_city(start, end):
                continue
            routes.append(
                {
                    "id": stable_id("route", season, start["order"], end["order"]),
                    "season": int(season),
                    "episode": end.get("episode"),
                    "leg": end.get("leg"),
                    "from_location_id": start["id"],
                    "to_location_id": end["id"],
                    "from_city": start["city"],
                    "to_city": end["city"],
                    "from_country": start["country"],
                    "to_country": end["country"],
                    "from_lat": start["lat"],
                    "from_lng": start["lng"],
                    "to_lat": end["lat"],
                    "to_lng": end["lng"],
                    "order": int(end["order"]),
                    "distance_km": haversine_km(start["lat"], start["lng"], end["lat"], end["lng"]),
                }
            )
    return routes


def build_seasons(locations: list[dict[str, object]]) -> list[dict[str, object]]:
    df = pd.DataFrame(locations)
    rows = []
    for season, group in df.groupby("season"):
        rows.append(
            {
                "season": int(season),
                "title": f"The Amazing Race {season}",
                "year": None,
                "color": SEASON_COLORS[(int(season) - 1) % len(SEASON_COLORS)],
                "episode_count": int(group["episode"].nunique()),
                "location_count": int(len(group)),
            }
        )
    return rows


def build_country_centroid_geojson(locations: list[dict[str, object]]) -> dict[str, object]:
    features = []
    df = pd.DataFrame(locations)
    for country, group in df.groupby("country"):
        lng = float(group["lng"].mean())
        lat = float(group["lat"].mean())
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
                "properties": {"name": country, "visits": int(len(group)), "seasons": sorted(group["season"].unique().tolist())},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def haversine_km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    radius = 6371.0088
    phi_1 = math.radians(a_lat)
    phi_2 = math.radians(b_lat)
    delta_phi = math.radians(b_lat - a_lat)
    delta_lambda = math.radians(b_lng - a_lng)
    h = math.sin(delta_phi / 2) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2) ** 2
    return round(2 * radius * math.asin(math.sqrt(h)), 1)


def continent_for_country(country: str) -> str | None:
    lookup = {
        "Argentina": "South America", "Australia": "Oceania", "Austria": "Europe", "Azerbaijan": "Asia",
        "Bahrain": "Asia", "Bangladesh": "Asia", "Barbados": "North America", "Belgium": "Europe",
        "Bolivia": "South America", "Botswana": "Africa", "Brazil": "South America", "Bulgaria": "Europe",
        "Burkina Faso": "Africa", "Cambodia": "Asia", "Canada": "North America", "Chile": "South America",
        "China": "Asia", "Colombia": "South America", "Costa Rica": "North America", "Croatia": "Europe",
        "Czech Republic": "Europe", "Denmark": "Europe", "Dominican Republic": "North America",
        "Ecuador": "South America", "Egypt": "Africa", "Estonia": "Europe", "Ethiopia": "Africa",
        "Finland": "Europe", "France": "Europe", "French Polynesia": "Oceania", "Georgia": "Asia",
        "Germany": "Europe", "Ghana": "Africa", "Greece": "Europe", "Guam": "Oceania",
        "Hong Kong": "Asia", "Hungary": "Europe", "Iceland": "Europe", "India": "Asia",
        "Indonesia": "Asia", "Ireland": "Europe", "Italy": "Europe", "Jamaica": "North America",
        "Japan": "Asia", "Jordan": "Asia", "Kazakhstan": "Asia", "Kenya": "Africa", "Kuwait": "Asia",
        "Laos": "Asia", "Liechtenstein": "Europe", "Lithuania": "Europe", "Macau": "Asia",
        "Madagascar": "Africa", "Malawi": "Africa", "Malaysia": "Asia", "Malta": "Europe",
        "Mauritius": "Africa", "Mexico": "North America", "Monaco": "Europe", "Mongolia": "Asia",
        "Morocco": "Africa", "Mozambique": "Africa", "Namibia": "Africa", "Netherlands": "Europe",
        "New Zealand": "Oceania", "Norway": "Europe", "Oman": "Asia", "Panama": "North America",
        "Paraguay": "South America", "Peru": "South America", "Philippines": "Asia", "Poland": "Europe",
        "Portugal": "Europe", "Puerto Rico": "North America", "Romania": "Europe", "Russia": "Europe",
        "Senegal": "Africa", "Seychelles": "Africa", "Singapore": "Asia", "Slovenia": "Europe",
        "South Africa": "Africa", "South Korea": "Asia", "Spain": "Europe", "Sri Lanka": "Asia",
        "Sweden": "Europe", "Switzerland": "Europe", "Taiwan": "Asia", "Tanzania": "Africa",
        "Thailand": "Asia", "Trinidad and Tobago": "North America", "Tunisia": "Africa", "Turkey": "Asia",
        "U.S. Virgin Islands": "North America", "Uganda": "Africa", "Ukraine": "Europe",
        "United Arab Emirates": "Asia", "United Kingdom": "Europe", "United States": "North America",
        "Uruguay": "South America", "Vietnam": "Asia", "Zambia": "Africa", "Zimbabwe": "Africa",
    }
    return lookup.get(country)


def write_static_frontend_data(seasons: list[dict[str, object]], locations: list[dict[str, object]], routes: list[dict[str, object]], countries: list[dict[str, object]], stats_row: dict[str, object]) -> None:
    FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
    write_json(FRONTEND_DATA / "seasons.json", seasons)
    write_json(FRONTEND_DATA / "locations.json", locations)
    write_json(FRONTEND_DATA / "routes.json", routes)
    write_json(FRONTEND_DATA / "countries.json", countries)
    write_json(FRONTEND_DATA / "stats.json", stats_row)


def write_json(path: Path, rows: object) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
