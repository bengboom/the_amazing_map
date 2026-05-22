from __future__ import annotations

from bs4 import BeautifulSoup

from .config import FANDOM_SEARCH_URL, RAW
from .http_client import cached_get
from .wiki_parser import ParsedLocation, parse_season_html


def fetch_fandom_locations(season: int) -> list[ParsedLocation]:
    """Fallback parser for Amazing Race Fandom season pages.

    Fandom pages are less consistent than Wikipedia pages, so this intentionally
    reuses the broad text/table parser after stripping script-heavy markup.
    """
    url = FANDOM_SEARCH_URL.format(season=season)
    html = cached_get(url, RAW / f"fandom_season_{season}.html")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script, style, nav, aside"):
        tag.decompose()
    return parse_season_html(season, str(soup), url)
