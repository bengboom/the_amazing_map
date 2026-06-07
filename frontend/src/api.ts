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

const TRAPPER_CREEK_ID = "s-1-city-13-united-states-trapper-creek";
const TRAPPER_CREEK = {
  id: TRAPPER_CREEK_ID,
  country: "United States",
  lat: 62.3463115,
  lng: -150.3925522,
  continent: "North America"
};

function normalizeExplorerData(seasons: Season[], locations: RaceLocation[], routes: RaceRoute[], source: "api" | "static") {
  const normalizedLocations = locations.map((location) => {
    if (location.season !== 1 || location.city !== "Trapper Creek") return location;
    return { ...location, ...TRAPPER_CREEK };
  });
  const normalizedRoutes = routes.map((route) => {
    if (route.id === "route-1-12-13") {
      return { ...route, to_location_id: TRAPPER_CREEK_ID, to_country: TRAPPER_CREEK.country, to_lat: TRAPPER_CREEK.lat, to_lng: TRAPPER_CREEK.lng, distance_km: 6310.5 };
    }
    if (route.id === "route-1-13-14") {
      return { ...route, from_location_id: TRAPPER_CREEK_ID, from_country: TRAPPER_CREEK.country, from_lat: TRAPPER_CREEK.lat, from_lng: TRAPPER_CREEK.lng, distance_km: 5410.4 };
    }
    return route;
  });
  const countries = buildCountryAggregates(normalizedLocations);
  const stats = buildStats(normalizedLocations, normalizedRoutes, countries);
  return { seasons, locations: normalizedLocations, routes: normalizedRoutes, countries, stats, source };
}

function buildCountryAggregates(locations: RaceLocation[]): CountryAggregate[] {
  const groups = new Map<string, { country: string; visits: number; seasons: Set<number>; episodes: Set<string>; cities: Set<string>; pit_stops: Set<string>; task_locations: Set<string>; continent?: string | null; lat_values: number[]; lng_values: number[] }>();
  for (const location of locations) {
    const group = groups.get(location.country) ?? { country: location.country, visits: 0, seasons: new Set<number>(), episodes: new Set<string>(), cities: new Set<string>(), pit_stops: new Set<string>(), task_locations: new Set<string>(), continent: location.continent, lat_values: [], lng_values: [] };
    group.visits += 1;
    group.seasons.add(location.season);
    if (location.episode != null) group.episodes.add(`S${location.season}E${location.episode}`);
    group.cities.add(location.city);
    if (location.type === "pit_stop") group.pit_stops.add(location.location_name);
    if (!["start", "pit_stop", "finish_line"].includes(location.type)) group.task_locations.add(location.location_name);
    group.lat_values.push(location.lat);
    group.lng_values.push(location.lng);
    groups.set(location.country, group);
  }
  return [...groups.values()].map((group) => ({
    country: group.country,
    visits: group.visits,
    seasons: [...group.seasons].sort((a, b) => a - b),
    episodes: [...group.episodes].sort(),
    cities: [...group.cities].sort(),
    pit_stops: [...group.pit_stops].sort(),
    task_locations: [...group.task_locations].sort(),
    continent: group.continent,
    lat: group.lat_values.reduce((sum, value) => sum + value, 0) / group.lat_values.length,
    lng: group.lng_values.reduce((sum, value) => sum + value, 0) / group.lng_values.length
  })).sort((a, b) => b.visits - a.visits || a.country.localeCompare(b.country));
}

function buildStats(locations: RaceLocation[], routes: RaceRoute[], countries: CountryAggregate[]): Stats {
  const cityCounts = new Map<string, number>();
  for (const location of locations) {
    const key = `${location.city}, ${location.country}`;
    cityCounts.set(key, (cityCounts.get(key) ?? 0) + 1);
  }
  return {
    seasonCount: new Set(locations.map((location) => location.season)).size,
    locationCount: locations.length,
    routeCount: routes.length,
    countryCount: countries.length,
    totalDistanceKm: Math.round(routes.reduce((sum, route) => sum + route.distance_km, 0)),
    mostVisitedCountries: countries.slice(0, 10),
    mostVisitedCities: [...cityCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 10).map(([city, visits]) => ({ city, visits })),
    countriesNeverRevisited: countries.filter((country) => country.seasons.length === 1).map((country) => country.country),
    uniqueContinents: [...new Set(locations.map((location) => location.continent).filter((continent): continent is string => Boolean(continent)))].sort()
  };
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
    void countries;
    void stats;
    return normalizeExplorerData(seasons, locations, routes, "api");
  } catch {
    const [seasons, locations, routes, countries, stats] = await Promise.all([
      fetch(`${STATIC_BASE}data/seasons.json`).then((r) => r.json() as Promise<Season[]>),
      fetch(`${STATIC_BASE}data/locations.json`).then((r) => r.json() as Promise<RaceLocation[]>),
      fetch(`${STATIC_BASE}data/routes.json`).then((r) => r.json() as Promise<RaceRoute[]>),
      fetch(`${STATIC_BASE}data/countries.json`).then((r) => r.json() as Promise<CountryAggregate[]>),
      fetch(`${STATIC_BASE}data/stats.json`).then((r) => r.json() as Promise<Stats>)
    ]);
    void countries;
    void stats;
    return normalizeExplorerData(seasons, locations, routes, "static");
  }
}

export function exportGeoJsonUrl(seasons: number[], country?: string) {
  const params = new URLSearchParams();
  seasons.forEach((season) => params.append("season", String(season)));
  if (country) params.set("country", country);
  return `${API_BASE}/export/geojson?${params.toString()}`;
}
