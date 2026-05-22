import { Check, Filter, Layers, Play, Pause, RotateCcw, Search } from "lucide-react";
import type { HighlightMode, QueryMode, Season } from "../types";
import { searchMatches } from "../utils";

interface SidebarProps {
  seasons: Season[];
  selectedSeasons: number[];
  setSelectedSeasons: (value: number[]) => void;
  queryMode: QueryMode;
  setQueryMode: (value: QueryMode) => void;
  highlightMode: HighlightMode;
  setHighlightMode: (value: HighlightMode) => void;
  seasonSearch: string;
  setSeasonSearch: (value: string) => void;
  timelineOrder: number;
  maxOrder: number;
  setTimelineOrder: (value: number) => void;
  isPlaying: boolean;
  setIsPlaying: (value: boolean) => void;
}

export function Sidebar({
  seasons,
  selectedSeasons,
  setSelectedSeasons,
  queryMode,
  setQueryMode,
  highlightMode,
  setHighlightMode,
  seasonSearch,
  setSeasonSearch,
  timelineOrder,
  maxOrder,
  setTimelineOrder,
  isPlaying,
  setIsPlaying
}: SidebarProps) {
  const filteredSeasons = seasons.filter((season) => searchMatches(`${season.title} ${season.year ?? ""}`, seasonSearch));
  const allSelected = selectedSeasons.length === seasons.length;

  function toggleSeason(season: number) {
    if (selectedSeasons.includes(season)) {
      setSelectedSeasons(selectedSeasons.filter((item) => item !== season));
    } else {
      setSelectedSeasons([...selectedSeasons, season].sort((a, b) => a - b));
    }
  }

  return (
    <aside className="sidebar left-panel">
      <div className="brand-block">
        <div className="eyebrow">US Edition</div>
        <h1>The Amazing Race World Map Explorer</h1>
      </div>

      <div className="mode-switch" aria-label="Query mode">
        <button className={queryMode === "forward" ? "active" : ""} onClick={() => setQueryMode("forward")}>Forward Query</button>
        <button className={queryMode === "reverse" ? "active" : ""} onClick={() => setQueryMode("reverse")}>Reverse Query</button>
      </div>

      <section className="panel-section">
        <div className="section-title"><Filter size={16} /> Seasons</div>
        <label className="search-box">
          <Search size={16} />
          <input value={seasonSearch} onChange={(event) => setSeasonSearch(event.target.value)} placeholder="Filter seasons" />
        </label>
        <button className="select-all" onClick={() => setSelectedSeasons(allSelected ? [] : seasons.map((season) => season.season))}>
          <Check size={16} /> {allSelected ? "Clear All" : "Select All"}
        </button>
        <div className="season-list">
          {filteredSeasons.map((season) => (
            <button key={season.season} className={`season-row ${selectedSeasons.includes(season.season) ? "selected" : ""}`} onClick={() => toggleSeason(season.season)}>
              <span className="season-swatch" style={{ backgroundColor: season.color }} />
              <span>
                <strong>Season {season.season}</strong>
                <small>{season.year ?? "Year TBD"} • {season.location_count} locations</small>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="panel-section">
        <div className="section-title"><Layers size={16} /> Highlight</div>
        <div className="segmented">
          {(["country", "city", "location"] as HighlightMode[]).map((mode) => (
            <button key={mode} className={highlightMode === mode ? "active" : ""} onClick={() => setHighlightMode(mode)}>
              {mode === "location" ? "Task" : mode[0].toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </section>

      <section className="panel-section">
        <div className="section-title">Timeline</div>
        <div className="timeline-actions">
          <button className="icon-button" onClick={() => setIsPlaying(!isPlaying)} title={isPlaying ? "Pause playback" : "Play playback"}>
            {isPlaying ? <Pause size={17} /> : <Play size={17} />}
          </button>
          <button className="icon-button" onClick={() => setTimelineOrder(maxOrder)} title="Reset to full route">
            <RotateCcw size={17} />
          </button>
          <span>Order {timelineOrder} / {maxOrder}</span>
        </div>
        <input className="range" type="range" min={1} max={maxOrder} value={timelineOrder} onChange={(event) => setTimelineOrder(Number(event.target.value))} />
      </section>
    </aside>
  );
}
