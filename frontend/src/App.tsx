import { useEffect, useMemo, useState } from "react";
import { MapView } from "./components/MapView";
import { RightPanel } from "./components/RightPanel";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { loadExplorerData } from "./api";
import type { CountryAggregate, HighlightMode, QueryMode, RaceLocation, RaceRoute, Season, Stats } from "./types";
import { countryDetails, filteredData } from "./utils";

export function App() {
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [locations, setLocations] = useState<RaceLocation[]>([]);
  const [routes, setRoutes] = useState<RaceRoute[]>([]);
  const [countries, setCountries] = useState<CountryAggregate[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [highlightMode, setHighlightMode] = useState<HighlightMode>("country");
  const [queryMode, setQueryMode] = useState<QueryMode>("forward");
  const [seasonSearch, setSeasonSearch] = useState("");
  const [globalSearch, setGlobalSearch] = useState("");
  const [timelineOrder, setTimelineOrder] = useState(99);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hoveredRoute, setHoveredRoute] = useState<RaceRoute | null>(null);
  const [dataSource, setDataSource] = useState<"api" | "static" | "loading">("loading");

  useEffect(() => {
    loadExplorerData().then((data) => {
      setSeasons(data.seasons);
      setLocations(data.locations);
      setRoutes(data.routes);
      setCountries(data.countries);
      setStats(data.stats);
      setSelectedSeasons(data.seasons.map((season) => season.season));
      setTimelineOrder(Math.max(...data.locations.map((location) => location.order), 1));
      setDataSource(data.source);
    });
  }, []);

  const maxOrder = useMemo(() => Math.max(...locations.map((location) => location.order), 1), [locations]);

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setTimelineOrder((current) => (current >= maxOrder ? 1 : current + 1));
    }, 950);
    return () => window.clearInterval(timer);
  }, [isPlaying, maxOrder]);

  const filtered = useMemo(
    () => filteredData(locations, routes, selectedSeasons, queryMode === "reverse" ? selectedCountry : null, timelineOrder),
    [locations, routes, selectedSeasons, selectedCountry, timelineOrder, queryMode]
  );

  const visibleCountries = useMemo(() => {
    const byCountry = new Map(countries.map((country) => [country.country, { ...country, visits: 0, seasons: new Set<number>(), episodes: new Set<string>(), cities: new Set<string>(), pit_stops: new Set<string>(), task_locations: new Set<string>() }]));
    for (const location of filtered.filteredLocations) {
      const row = byCountry.get(location.country);
      if (!row) continue;
      row.visits += 1;
      row.seasons.add(location.season);
      if (location.episode) row.episodes.add(`S${location.season}E${location.episode}`);
      row.cities.add(location.city);
      if (location.type === "pit_stop") row.pit_stops.add(location.location_name);
      if (!["start", "pit_stop", "finish_line"].includes(location.type)) row.task_locations.add(location.location_name);
    }
    return [...byCountry.values()]
      .filter((country) => country.visits > 0)
      .map((country) => ({
        ...country,
        seasons: [...country.seasons].sort((a, b) => a - b),
        episodes: [...country.episodes].sort(),
        cities: [...country.cities].sort(),
        pit_stops: [...country.pit_stops].sort(),
        task_locations: [...country.task_locations].sort()
      }));
  }, [countries, filtered.filteredLocations]);

  const detail = useMemo(() => countryDetails(selectedCountry, countries, locations, routes), [selectedCountry, countries, locations, routes]);

  return (
    <div className="app-frame">
      <TopBar
        countries={countries}
        seasons={seasons}
        selectedSeasons={selectedSeasons}
        selectedCountry={selectedCountry}
        setSelectedCountry={setSelectedCountry}
        setSelectedSeasons={setSelectedSeasons}
        globalSearch={globalSearch}
        setGlobalSearch={setGlobalSearch}
        locations={filtered.filteredLocations}
        routes={filtered.filteredRoutes}
      />
      <main className="workspace">
        <Sidebar
          seasons={seasons}
          selectedSeasons={selectedSeasons}
          setSelectedSeasons={setSelectedSeasons}
          queryMode={queryMode}
          setQueryMode={setQueryMode}
          highlightMode={highlightMode}
          setHighlightMode={setHighlightMode}
          seasonSearch={seasonSearch}
          setSeasonSearch={setSeasonSearch}
          timelineOrder={timelineOrder}
          maxOrder={maxOrder}
          setTimelineOrder={setTimelineOrder}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
        />
        <section className="map-stage">
          <div className="status-ribbon">
            <span>{queryMode === "forward" ? "Forward Query" : "Reverse Query"}</span>
            <span>{selectedSeasons.length} seasons selected</span>
            <span>{dataSource === "api" ? "Live API" : dataSource === "static" ? "Static fallback" : "Loading"}</span>
          </div>
          <MapView
            countries={visibleCountries}
            locations={filtered.filteredLocations}
            routes={filtered.filteredRoutes}
            seasons={seasons}
            selectedCountry={selectedCountry}
            setSelectedCountry={(country) => {
              setSelectedCountry(country);
              setQueryMode("reverse");
            }}
            setSelectedSeasons={setSelectedSeasons}
            highlightMode={highlightMode}
            setHoveredRoute={setHoveredRoute}
          />
        </section>
        <RightPanel selectedCountry={selectedCountry} detail={detail} stats={stats} hoveredRoute={hoveredRoute} />
      </main>
    </div>
  );
}
