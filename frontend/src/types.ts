export type LocationType = "start" | "route_info" | "detour" | "roadblock" | "pit_stop" | "finish_line";

export interface Season {
  season: number;
  title: string;
  year?: number | null;
  color: string;
  episode_count: number;
  location_count: number;
}

export interface RaceLocation {
  id: string;
  season: number;
  episode?: number | null;
  leg?: number | null;
  country: string;
  city: string;
  location_name: string;
  lat: number;
  lng: number;
  type: LocationType;
  order: number;
  continent?: string | null;
  source_url?: string | null;
}

export interface RaceRoute {
  id: string;
  season: number;
  episode?: number | null;
  leg?: number | null;
  from_location_id: string;
  to_location_id: string;
  from_city: string;
  to_city: string;
  from_country: string;
  to_country: string;
  from_lat: number;
  from_lng: number;
  to_lat: number;
  to_lng: number;
  order: number;
  distance_km: number;
}

export interface CountryAggregate {
  country: string;
  visits: number;
  seasons: number[];
  episodes: string[];
  cities: string[];
  pit_stops: string[];
  task_locations: string[];
  continent?: string | null;
  lat: number;
  lng: number;
}

export interface Stats {
  seasonCount: number;
  locationCount: number;
  routeCount: number;
  countryCount: number;
  totalDistanceKm: number;
  mostVisitedCountries: CountryAggregate[];
  mostVisitedCities: { city: string; visits: number }[];
  countriesNeverRevisited: string[];
  uniqueContinents: string[];
}

export type HighlightMode = "country" | "city" | "location";
export type QueryMode = "forward" | "reverse";
