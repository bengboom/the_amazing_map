from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .data_store import aggregate_countries, feature_collection, filter_rows, load_data, stats

app = FastAPI(title="The Amazing Race World Map Explorer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    data = load_data()
    return {
        "status": "ok",
        "locations": len(data["locations"]),
        "routes": len(data["routes"]),
        "seasons": len(data["seasons"]),
    }


@app.get("/seasons")
def seasons(season: list[int] | None = Query(default=None)) -> list[dict[str, object]]:
    rows = load_data()["seasons"]
    if season:
        wanted = set(season)
        rows = [row for row in rows if int(row["season"]) in wanted]
    return rows


@app.get("/countries")
def countries(season: list[int] | None = Query(default=None), country: str | None = None) -> list[dict[str, object]]:
    locations = filter_rows(load_data()["locations"], season=season, country=country)
    return aggregate_countries(locations)


@app.get("/locations")
def locations(season: list[int] | None = Query(default=None), country: str | None = None, episode: int | None = None) -> list[dict[str, object]]:
    return filter_rows(load_data()["locations"], season=season, country=country, episode=episode)


@app.get("/routes")
def routes(season: list[int] | None = Query(default=None), country: str | None = None, episode: int | None = None) -> list[dict[str, object]]:
    return filter_rows(load_data()["routes"], season=season, country=country, episode=episode)


@app.get("/stats")
def global_stats(season: list[int] | None = Query(default=None), country: str | None = None, episode: int | None = None) -> dict[str, object]:
    data = load_data()
    locations = filter_rows(data["locations"], season=season, country=country, episode=episode)
    routes = filter_rows(data["routes"], season=season, country=country, episode=episode)
    return stats(locations, routes)


@app.get("/countries.geojson")
def countries_geojson() -> dict[str, object]:
    return load_data()["countries_geojson"]


@app.get("/export/geojson")
def export_geojson(season: list[int] | None = Query(default=None), country: str | None = None, episode: int | None = None) -> dict[str, object]:
    data = load_data()
    locations = filter_rows(data["locations"], season=season, country=country, episode=episode)
    routes = filter_rows(data["routes"], season=season, country=country, episode=episode)
    return feature_collection(locations, routes)
