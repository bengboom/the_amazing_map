import { Download, MapPinned, Search } from "lucide-react";
import { exportGeoJsonUrl } from "../api";
import type { CountryAggregate, Season } from "../types";

interface TopBarProps {
  countries: CountryAggregate[];
  seasons: Season[];
  selectedSeasons: number[];
  selectedCountry: string | null;
  setSelectedCountry: (value: string | null) => void;
  setSelectedSeasons: (value: number[]) => void;
  globalSearch: string;
  setGlobalSearch: (value: string) => void;
}

export function TopBar({ countries, seasons, selectedSeasons, selectedCountry, setSelectedCountry, setSelectedSeasons, globalSearch, setGlobalSearch }: TopBarProps) {
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

  return (
    <nav className="topbar">
      <div className="product-mark"><MapPinned size={19} /> Race Atlas</div>
      <label className="global-search">
        <Search size={17} />
        <input value={globalSearch} onChange={(event) => runSearch(event.target.value)} placeholder="Search country, city, or season" />
      </label>
      <a className="export-link" href={exportGeoJsonUrl(selectedSeasons, selectedCountry ?? undefined)} target="_blank" rel="noreferrer">
        <Download size={17} /> Export GeoJSON
      </a>
    </nav>
  );
}
