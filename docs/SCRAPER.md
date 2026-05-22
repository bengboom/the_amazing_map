# Scraper

The scraper is located in `scraper/` and can be run with:

```bash
python scraper/build_dataset.py
```

## Sources

The pipeline is structured around:

- Wikipedia season pages such as `https://en.wikipedia.org/wiki/The_Amazing_Race_1`
- Wikipedia route and leg summary tables
- Amazing Race Fandom pages as fallback enrichment
- Wikimedia Commons route map references when available
- Nominatim OpenStreetMap geocoding

## Pipeline

1. Discover season pages from Wikipedia.
2. Download HTML to `data/raw`.
3. Parse route summaries, leg tables, country/city/location labels, episodes, legs, and pit stops.
4. Normalize country, city, and landmark aliases.
5. Deduplicate locations.
6. Geocode exact locations, then city centers as fallback.
7. Infer chronological route segments.
8. Export processed JSON and country GeoJSON.

## Reliability

- HTTP retries with exponential backoff
- Local raw HTML cache
- Local geocoding cache
- Conservative parsing fallbacks for inconsistent tables
- Canonical naming rules for countries, city aliases, and landmark duplicates

## Nominatim Etiquette

The geocoder uses a descriptive User-Agent and throttles requests. Avoid deleting `data/cache/geocode_cache.json`; it prevents repeated lookups.
