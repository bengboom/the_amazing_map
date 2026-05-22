from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
CACHE = DATA / "cache"

USER_AGENT = "AmazingRaceWorldMapExplorer/1.0 (local research dataset builder)"
WIKIPEDIA_SEASON_URL = "https://en.wikipedia.org/wiki/The_Amazing_Race_{season}"
FANDOM_SEARCH_URL = "https://amazingrace.fandom.com/wiki/The_Amazing_Race_{season}"

SEASON_COLORS = [
    "#66e3ff",
    "#f97316",
    "#a78bfa",
    "#34d399",
    "#f43f5e",
    "#facc15",
    "#38bdf8",
    "#fb7185",
    "#4ade80",
    "#c084fc",
]
