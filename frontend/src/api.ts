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

type LocationOverride = Pick<RaceLocation, "country" | "lat" | "lng" | "continent">;

const CITY_LOCATION_OVERRIDES: Record<string, LocationOverride> = {
  "Hong Kong": { country: "Hong Kong", lat: 22.2818333, lng: 114.1582831, continent: "Asia" },
  Macau: { country: "Macau", lat: 22.20056, lng: 113.54611, continent: "Asia" },
  Singapore: { country: "Singapore", lat: 1.2899175, lng: 103.8519072, continent: "Asia" }
};

const SEASON_LOCATION_OVERRIDES: Record<string, LocationOverride> = {
  "1:Trapper Creek": { country: "United States", lat: 62.3463115, lng: -150.3925522, continent: "North America" }
};

function normalizeExplorerData(seasons: Season[], locations: RaceLocation[], routes: RaceRoute[], source: "api" | "static") {
  const normalizedLocations = locations.map((location) => {
    const override = locationOverride(location.season, location.city);
    if (!override) return location;
    return { ...location, ...override, id: locationId(location.season, location.order, override.country, location.city) };
  });
  const normalizedRoutes = routes.map((route) => {
    const from = routeEndpointOverride(route.season, route.order - 1, route.from_city);
    const to = routeEndpointOverride(route.season, route.order, route.to_city);
    const normalizedRoute = {
      ...route,
      ...(from ? { from_location_id: from.id, from_country: from.country, from_lat: from.lat, from_lng: from.lng } : {}),
      ...(to ? { to_location_id: to.id, to_country: to.country, to_lat: to.lat, to_lng: to.lng } : {})
    };
    if (!from && !to) return normalizedRoute;
    return {
      ...normalizedRoute,
      distance_km: haversineKm(normalizedRoute.from_lat, normalizedRoute.from_lng, normalizedRoute.to_lat, normalizedRoute.to_lng)
    };
  });
  const countries = buildCountryAggregates(normalizedLocations);
  const stats = buildStats(normalizedLocations, normalizedRoutes, countries);
  return { seasons, locations: normalizedLocations, routes: normalizedRoutes, countries, stats, source };
}

function locationOverride(season: number, city: string): LocationOverride | undefined {
  return SEASON_LOCATION_OVERRIDES[`${season}:${city}`] ?? CITY_LOCATION_OVERRIDES[city];
}

function routeEndpointOverride(season: number, order: number, city: string) {
  const override = locationOverride(season, city);
  if (!override) return null;
  return { ...override, id: locationId(season, order, override.country, city) };
}

function locationId(season: number, order: number, country: string, city: string) {
  return `s-${season}-city-${order}-${slug(country)}-${slug(city)}`;
}

function slug(value: string) {
  return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function haversineKm(aLat: number, aLng: number, bLat: number, bLng: number) {
  const radius = 6371.0088;
  const phi1 = toRadians(aLat);
  const phi2 = toRadians(bLat);
  const deltaPhi = toRadians(bLat - aLat);
  const deltaLambda = toRadians(bLng - aLng);
  const h = Math.sin(deltaPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
  return Math.round(2 * radius * Math.asin(Math.sqrt(h)) * 10) / 10;
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
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
