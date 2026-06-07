import { useEffect } from "react";
import L from "leaflet";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { CountryAggregate, HighlightMode, RaceLocation, RaceRoute, Season } from "../types";
import { routeArcPath, seasonColor } from "../utils";

interface MapViewProps {
  countries: CountryAggregate[];
  locations: RaceLocation[];
  routes: RaceRoute[];
  seasons: Season[];
  selectedCountry: string | null;
  setSelectedCountry: (country: string | null) => void;
  setSelectedSeasons: (seasons: number[]) => void;
  highlightMode: HighlightMode;
  setHoveredRoute: (route: RaceRoute | null) => void;
}

export function MapView({ countries, locations, routes, seasons, selectedCountry, setSelectedCountry, setSelectedSeasons, highlightMode, setHoveredRoute }: MapViewProps) {
  const maxVisits = Math.max(1, ...countries.map((country) => country.visits));
  const visibleLocationIds = new Set(locations.map((location) => location.id));
  const countryByName = new Map(countries.map((country) => [country.country, country]));

  function clickCountry(country: CountryAggregate) {
    setSelectedCountry(country.country);
    setSelectedSeasons(country.seasons);
  }

  return (
    <div className="map-shell">
      <MapContainer className="map" center={[18, 18]} zoom={2.2} minZoom={2} worldCopyJump>
        <TileLayer
          attribution="&copy; OpenStreetMap contributors &copy; CARTO"
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <FitSelectedCountry country={selectedCountry ? countryByName.get(selectedCountry) : undefined} />

        {routes.map((route, index) => {
          const color = seasonColor(route.season, seasons);
          const weight = selectedCountry && (route.from_country === selectedCountry || route.to_country === selectedCountry) ? 4.5 : 2.2;
          const offset = (index % 4) * 0.45;
          const arc = routeArcPath(route.from_lat + offset, route.from_lng + offset, route.to_lat + offset, route.to_lng + offset, route.distance_km);
          return (
            <Polyline
              key={route.id}
              positions={arc}
              pathOptions={{ color, weight, opacity: 0.82, className: "animated-route" }}
              eventHandlers={{ mouseover: () => setHoveredRoute(route), mouseout: () => setHoveredRoute(null) }}
            >
              <Tooltip sticky>
                <strong>{route.from_city} → {route.to_city}</strong><br />
                Season {route.season} • Episode {route.episode ?? "TBD"}
              </Tooltip>
            </Polyline>
          );
        })}

        {countries.map((country) => {
          const intensity = country.visits / maxVisits;
          const selected = selectedCountry === country.country;
          return (
            <CircleMarker
              key={country.country}
              center={[country.lat, country.lng]}
              radius={12 + intensity * 22}
              pathOptions={{
                color: selected ? "#ffffff" : "#66e3ff",
                fillColor: selected ? "#facc15" : "#0ea5e9",
                fillOpacity: 0.24 + intensity * 0.46,
                opacity: 0.88,
                weight: selected ? 3 : 1.5,
                className: "country-glow"
              }}
              eventHandlers={{ click: () => clickCountry(country) }}
            >
              <Tooltip sticky>
                <strong>{country.country}</strong><br />
                {country.visits} visits<br />
                Seasons {country.seasons.join(", ")}<br />
                Episodes {country.episodes.slice(0, 5).join(", ")}
              </Tooltip>
            </CircleMarker>
          );
        })}

        {highlightMode !== "country" && locations.filter((location) => visibleLocationIds.has(location.id)).map((location) => (
          <Marker key={location.id} position={[location.lat, location.lng]} icon={markerIcon(location.type, seasonColor(location.season, seasons))}>
            <Popup>
              <strong>{location.location_name}</strong><br />
              {location.city}, {location.country}<br />
              Season {location.season} • Episode {location.episode ?? "TBD"} • {location.type.replace("_", " ")}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      <div className="map-legend">
        <span className="pulse-dot" /> Visit intensity
        <span className="line-sample" /> Chronological route
      </div>
    </div>
  );
}

function markerIcon(type: string, color: string) {
  const label = type === "pit_stop" ? "P" : type === "roadblock" ? "R" : type === "detour" ? "D" : type === "finish_line" ? "F" : "•";
  return L.divIcon({
    className: "task-marker",
    html: `<span style="--marker-color:${color}">${label}</span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  });
}

function FitSelectedCountry({ country }: { country?: CountryAggregate }) {
  const map = useMap();
  useEffect(() => {
    if (country) {
      map.flyTo([country.lat, country.lng], 4, { duration: 0.8 });
    }
  }, [country, map]);
  return null;
}
