import { BarChart3, Flag, MapPin, Route, Trophy } from "lucide-react";
import type { CountryAggregate, RaceLocation, RaceRoute, Stats } from "../types";
import { formatKm } from "../utils";

interface RightPanelProps {
  selectedCountry: string | null;
  detail: { aggregate?: CountryAggregate; locations: RaceLocation[]; routes: RaceRoute[] } | null;
  stats: Stats | null;
  hoveredRoute: RaceRoute | null;
}

export function RightPanel({ selectedCountry, detail, stats, hoveredRoute }: RightPanelProps) {
  return (
    <aside className="sidebar right-panel">
      <section className="panel-section hero-stat">
        <div className="section-title"><BarChart3 size={16} /> Global Footprint</div>
        <div className="stat-grid">
          <Metric label="Seasons" value={stats?.seasonCount ?? 0} />
          <Metric label="Countries" value={stats?.countryCount ?? 0} />
          <Metric label="Locations" value={stats?.locationCount ?? 0} />
          <Metric label="Distance" value={formatKm(stats?.totalDistanceKm ?? 0)} />
        </div>
      </section>

      {hoveredRoute && (
        <section className="panel-section focus-card">
          <div className="section-title"><Route size={16} /> Route Hover</div>
          <strong>{hoveredRoute.from_city} → {hoveredRoute.to_city}</strong>
          <span>Season {hoveredRoute.season} • Episode {hoveredRoute.episode ?? "TBD"} • Leg {hoveredRoute.leg ?? "TBD"}</span>
          <span>{formatKm(hoveredRoute.distance_km)}</span>
        </section>
      )}

      <section className="panel-section">
        <div className="section-title"><Flag size={16} /> Reverse Query</div>
        {!selectedCountry || !detail ? (
          <p className="muted">Click a country marker to reveal seasons, exact episodes, cities, pit stops, and route sequence.</p>
        ) : (
          <div className="country-detail">
            <h2>{selectedCountry}</h2>
            <div className="chips">
              {detail.aggregate?.seasons.map((season) => <span key={season}>Season {season}</span>)}
            </div>
            <div className="detail-list">
              {detail.locations.map((location) => (
                <div key={location.id} className="detail-row">
                  <MapPin size={15} />
                  <div>
                    <strong>S{location.season} E{location.episode ?? "?"} • Leg {location.leg ?? "?"}</strong>
                    <span>{location.city} — {location.location_name}</span>
                    <small>{location.type.replace("_", " ")}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="panel-section">
        <div className="section-title"><Trophy size={16} /> Rankings</div>
        <ol className="ranking">
          {(stats?.mostVisitedCountries ?? []).slice(0, 6).map((country) => (
            <li key={country.country}>
              <span>{country.country}</span>
              <strong>{country.visits}</strong>
            </li>
          ))}
        </ol>
      </section>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
