import { Download, MapPinned, Search } from "lucide-react";
import type { CountryAggregate, RaceLocation, RaceRoute, Season } from "../types";

interface TopBarProps {
  countries: CountryAggregate[];
  seasons: Season[];
  selectedSeasons: number[];
  selectedCountry: string | null;
  locations: RaceLocation[];
  routes: RaceRoute[];
  setSelectedCountry: (value: string | null) => void;
  setSelectedSeasons: (value: number[]) => void;
  globalSearch: string;
  setGlobalSearch: (value: string) => void;
}

export function TopBar({ countries, seasons, selectedCountry, locations, routes, setSelectedCountry, setSelectedSeasons, globalSearch, setGlobalSearch }: TopBarProps) {
  function runSearch(value: string) {
    setGlobalSearch(value);
    const country = countries.find((item) => item.country.toLowerCase().includes(value.toLowerCase()));
    if (country && value.trim().length > 1) {
      setSelectedCountry(country.country);
      setSelectedSeasons(country.seasons);
    }
    const seasonMatch = value.match(/\d+/);
    if (/season/i.test(value) && seasonMatch) {
      const season = Number(seasonMatch[0]);
      if (seasons.some((item) => item.season === season)) {
        setSelectedSeasons([season]);
      }
    }
  }

  function exportGeoJson() {
    const features = locations.map((location) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [location.lng, location.lat] },
      properties: {
        id: location.id,
        season: location.season,
        episode: location.episode,
        leg: location.leg,
        country: location.country,
        city: location.city,
        location_name: location.location_name,
        type: location.type,
        order: location.order
      }
    }));
    const routeFeatures = routes.map((route) => ({
      type: "Feature" as const,
      geometry: {
        type: "LineString" as const,
        coordinates: [[route.from_lng, route.from_lat], [route.to_lng, route.to_lat]]
      },
      properties: {
        id: route.id,
        season: route.season,
        episode: route.episode,
        leg: route.leg,
        from: `${route.from_city}, ${route.from_country}`,
        to: `${route.to_city}, ${route.to_country}`,
        order: route.order,
        distance_km: route.distance_km
      }
    }));
    const geoJson = { type: "FeatureCollection", features: [...features, ...routeFeatures] };
    const blob = new Blob([JSON.stringify(geoJson, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = selectedCountry ? `amazing-race-${selectedCountry.toLowerCase().replace(/\s+/g, "-")}.geojson` : "amazing-race-map.geojson";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <nav className="topbar">
      <div className="product-mark"><MapPinned size={19} /> Race Atlas</div>
      <label className="global-search">
        <Search size={17} />
        <input value={globalSearch} onChange={(event) => runSearch(event.target.value)} placeholder="Search country, city, or season" />
      </label>
      <button className="export-link" type="button" onClick={exportGeoJson}>
        <Download size={17} /> Export GeoJSON
      </button>
    </nav>
  );
}
