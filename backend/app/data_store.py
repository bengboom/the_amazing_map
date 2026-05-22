from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"


def _read_json(name: str, default: Any) -> Any:
    path = PROCESSED / name
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_data() -> dict[str, Any]:
    locations = _read_json("locations.json", [])
    routes = _read_json("routes.json", [])
    seasons = _read_json("seasons.json", [])
    countries_geojson = _read_json("countries.geojson", {"type": "FeatureCollection", "features": []})
    return {
        "locations": locations,
        "routes": routes,
        "seasons": seasons,
        "countries_geojson": countries_geojson,
    }


def filter_rows(rows: list[dict[str, Any]], season: list[int] | None = None, country: str | None = None, episode: int | None = None) -> list[dict[str, Any]]:
    result = rows
    if season:
        wanted = set(season)
        result = [row for row in result if int(row.get("season", -1)) in wanted]
    if country:
        key = country.casefold()
        result = [row for row in result if str(row.get("country", row.get("from_country", ""))).casefold() == key or str(row.get("to_country", "")).casefold() == key]
    if episode is not None:
        result = [row for row in result if row.get("episode") == episode]
    return result


def aggregate_countries(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for loc in locations:
        country = loc["country"]
        group = groups.setdefault(
            country,
            {
                "country": country,
                "visits": 0,
                "seasons": set(),
                "episodes": set(),
                "cities": set(),
                "pit_stops": set(),
                "task_locations": set(),
                "continent": loc.get("continent"),
                "lat_values": [],
                "lng_values": [],
            },
        )
        group["visits"] += 1
        group["seasons"].add(loc["season"])
        if loc.get("episode") is not None:
            group["episodes"].add(f"S{loc['season']}E{loc['episode']}")
        group["cities"].add(loc["city"])
        if loc["type"] == "pit_stop":
            group["pit_stops"].add(loc["location_name"])
        if loc["type"] not in {"start", "pit_stop", "finish_line"}:
            group["task_locations"].add(loc["location_name"])
        group["lat_values"].append(loc["lat"])
        group["lng_values"].append(loc["lng"])

    aggregates = []
    for group in groups.values():
        aggregates.append(
            {
                "country": group["country"],
                "visits": group["visits"],
                "seasons": sorted(group["seasons"]),
                "episodes": sorted(group["episodes"]),
                "cities": sorted(group["cities"]),
                "pit_stops": sorted(group["pit_stops"]),
                "task_locations": sorted(group["task_locations"]),
                "continent": group["continent"],
                "lat": sum(group["lat_values"]) / len(group["lat_values"]),
                "lng": sum(group["lng_values"]) / len(group["lng_values"]),
            }
        )
    return sorted(aggregates, key=lambda row: (-row["visits"], row["country"]))


def stats(locations: list[dict[str, Any]], routes: list[dict[str, Any]]) -> dict[str, Any]:
    country_rows = aggregate_countries(locations)
    city_counts: dict[str, int] = {}
    for loc in locations:
        key = f"{loc['city']}, {loc['country']}"
        city_counts[key] = city_counts.get(key, 0) + 1
    never_revisited = [row["country"] for row in country_rows if len(row["seasons"]) == 1]
    continents = sorted({loc.get("continent") for loc in locations if loc.get("continent")})
    return {
        "seasonCount": len({loc["season"] for loc in locations}),
        "locationCount": len(locations),
        "routeCount": len(routes),
        "countryCount": len(country_rows),
        "totalDistanceKm": round(sum(float(route.get("distance_km", 0)) for route in routes)),
        "mostVisitedCountries": country_rows[:10],
        "mostVisitedCities": [{"city": key, "visits": value} for key, value in sorted(city_counts.items(), key=lambda item: (-item[1], item[0]))[:10]],
        "countriesNeverRevisited": never_revisited,
        "uniqueContinents": continents,
    }


def feature_collection(locations: list[dict[str, Any]], routes: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for loc in locations:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [loc["lng"], loc["lat"]]},
                "properties": loc,
            }
        )
    for route in routes:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[route["from_lng"], route["from_lat"]], [route["to_lng"], route["to_lat"]]],
                },
                "properties": route,
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
