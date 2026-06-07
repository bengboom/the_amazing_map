import type { CountryAggregate, RaceLocation, RaceRoute, Season, Stats } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const STATIC_BASE = import.meta.env.BASE_URL;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function loadExplorerData() {
  try {
    const [seasons, locations, routes, countries, stats] = await Promise.all([
      getJson<Season[]>("/seasons"),
      getJson<RaceLocation[]>("/locations"),
      getJson<RaceRoute[]>("/routes"),
      getJson<CountryAggregate[]>("/countries"),
      getJson<Stats>("/stats")
    ]);
    return { seasons, locations, routes, countries, stats, source: "api" as const };
  } catch {
    const [seasons, locations, routes, countries, stats] = await Promise.all([
      fetch(`${STATIC_BASE}data/seasons.json`).then((r) => r.json() as Promise<Season[]>),
      fetch(`${STATIC_BASE}data/locations.json`).then((r) => r.json() as Promise<RaceLocation[]>),
      fetch(`${STATIC_BASE}data/routes.json`).then((r) => r.json() as Promise<RaceRoute[]>),
      fetch(`${STATIC_BASE}data/countries.json`).then((r) => r.json() as Promise<CountryAggregate[]>),
      fetch(`${STATIC_BASE}data/stats.json`).then((r) => r.json() as Promise<Stats>)
    ]);
    return { seasons, locations, routes, countries, stats, source: "static" as const };
  }
}

export function exportGeoJsonUrl(seasons: number[], country?: string) {
  const params = new URLSearchParams();
  seasons.forEach((season) => params.append("season", String(season)));
  if (country) params.set("country", country);
  return `${API_BASE}/export/geojson?${params.toString()}`;
}
