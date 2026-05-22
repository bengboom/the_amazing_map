from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .http_client import get_with_retries


def discover_commons_route_maps(season: int) -> list[str]:
    """Find candidate Wikimedia Commons route map assets for a season.

    Route map file names vary, so this function returns candidate URLs rather
    than treating Commons as an authoritative structured source.
    """
    query = f"The Amazing Race {season} route map"
    url = "https://commons.wikimedia.org/w/index.php"
    response = get_with_retries(f"{url}?search={query.replace(' ', '+')}&title=Special:MediaSearch&type=image")
    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[str] = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        label = link.get_text(" ")
        if re.search(r"route|map|amazing race", f"{href} {label}", re.I) and href.startswith("/wiki/"):
            candidates.append(f"https://commons.wikimedia.org{href}")
    return sorted(set(candidates))
