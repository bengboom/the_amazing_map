import type { CountryAggregate, RaceLocation, RaceRoute, Season } from "./types";

export function seasonColor(season: number, seasons: Season[]) {
  return seasons.find((item) => item.season === season)?.color ?? "#66e3ff";
}

export function formatKm(value: number) {
  return `${Math.round(value).toLocaleString()} km`;
}

export function countryDetails(country: string | null, countries: CountryAggregate[], locations: RaceLocation[], routes: RaceRoute[]) {
  if (!country) return null;
  const aggregate = countries.find((item) => item.country === country);
  const countryLocations = locations
    .filter((location) => location.country === country)
    .sort((a, b) => a.season - b.season || (a.episode ?? 0) - (b.episode ?? 0) || a.order - b.order);
  const countryRoutes = routes.filter((route) => route.from_country === country || route.to_country === country);
  return { aggregate, locations: countryLocations, routes: countryRoutes };
}

export function routeArcPath(fromLat: number, fromLng: number, toLat: number, toLng: number, distanceKm: number): [number, number][] {
  const points: [number, number][] = [];
  const steps = 36;
  const curveHeight = Math.min(7, Math.max(0, (distanceKm - 500) / 1400));
  const rawLngDelta = toLng - fromLng;
  const lngDelta = Math.abs(rawLngDelta) > 180 ? rawLngDelta - Math.sign(rawLngDelta) * 360 : rawLngDelta;
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const lat = fromLat + (toLat - fromLat) * t + Math.sin(Math.PI * t) * curveHeight;
    const lng = fromLng + lngDelta * t;
    points.push([lat, lng]);
  }
  return points;
}

export function filteredData(locations: RaceLocation[], routes: RaceRoute[], selectedSeasons: number[], selectedCountry: string | null, timelineOrder: number) {
  const seasonSet = new Set(selectedSeasons);
  const filteredLocations = locations.filter((location) => seasonSet.has(location.season) && location.order <= timelineOrder);
  const filteredRoutes = routes.filter((route) => {
    const seasonMatch = seasonSet.has(route.season);
    const orderMatch = route.order <= timelineOrder;
    const countryMatch = !selectedCountry || route.from_country === selectedCountry || route.to_country === selectedCountry;
    return seasonMatch && orderMatch && countryMatch;
  });
  return { filteredLocations, filteredRoutes };
}

export function searchMatches(value: string, query: string) {
  return value.toLowerCase().includes(query.trim().toLowerCase());
}
