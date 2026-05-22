from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper.config import PROCESSED, RAW, SEASON_COLORS, WIKIPEDIA_SEASON_URL
from scraper.fandom import fetch_fandom_locations
from scraper.geocode import Geocoder
from scraper.http_client import cached_get
from scraper.normalize import stable_id
from scraper.wiki_parser import ParsedLocation, parse_season_html

MAX_SEASONS_TO_PROBE = 60


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
        if not parsed:
            parsed = fetch_fandom_locations(season)
        locations.extend(enrich_locations(parsed, geocoder))
    if not locations:
        print("No locations parsed; leaving existing processed data untouched.")
        return
    routes = build_routes(locations)
    season_rows = build_seasons(locations)
    write_json(PROCESSED / "locations.json", locations)
    write_json(PROCESSED / "routes.json", routes)
    write_json(PROCESSED / "seasons.json", season_rows)
    write_json(PROCESSED / "countries.geojson", build_country_centroid_geojson(locations))
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
        coords = geocoder.geocode(row.location_name, row.city, row.country) or {"lat": 0.0, "lng": 0.0}
        enriched.append(
            {
                **asdict(row),
                "id": stable_id("s", row.season, "o", row.order, row.country, row.city, row.location_name),
                "lat": coords["lat"],
                "lng": coords["lng"],
                "continent": continent_for_country(row.country),
            }
        )
    return enriched


def build_routes(locations: list[dict[str, object]]) -> list[dict[str, object]]:
    routes = []
    for season, rows in pd.DataFrame(locations).sort_values(["season", "order"]).groupby("season"):
        records = rows.to_dict("records")
        for index in range(len(records) - 1):
            start = records[index]
            end = records[index + 1]
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
        "United States": "North America",
        "Japan": "Asia",
        "Brazil": "South America",
        "South Africa": "Africa",
        "India": "Asia",
        "France": "Europe",
        "Australia": "Oceania",
        "United Kingdom": "Europe",
        "China": "Asia",
        "Thailand": "Asia",
    }
    return lookup.get(country)


def write_json(path: Path, rows: object) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
