# The Amazing Race World Map Explorer

A production-style interactive web application for exploring countries, cities, legs, episodes, pit stops, and routes across the US version of **The Amazing Race**.

This is an unofficial fan-made research and visualization project. It is not affiliated with, endorsed by, or sponsored by CBS, World Race Productions, or the producers, owners, or distributors of The Amazing Race.

The project includes:

- React + TypeScript + Leaflet frontend
- FastAPI backend
- Python scraping and dataset-building pipeline
- Normalized JSON sample data
- Geocoding cache support via Nominatim
- Docs for scraping, API usage, and deployment

## Quick Start

Install JavaScript dependencies:

```bash
npm install
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python main.py
```

Start the frontend in a second terminal:

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```


## Deploy to GitHub Pages

This project can be published as a static site to GitHub Pages (frontend only).

1. Push to your `main` branch (or trigger the workflow manually).
2. In GitHub repository settings, open **Pages** and set **Source** to **GitHub Actions**.
3. The workflow in `.github/workflows/deploy-gh-pages.yml` will build with `npm run build` and publish `frontend/dist`.

Local production build test:

```bash
npm run build
```

Optional manual publish from local machine:

```bash
npm run deploy
```

## Regenerate The Dataset

The repository ships with sample processed data so the app runs immediately. To scrape and rebuild the full dataset:

```bash
npm run scrape
```

The scraper writes:

- `data/raw/wiki_season_*.html`
- `data/processed/locations.json`
- `data/processed/routes.json`
- `data/processed/seasons.json`
- `data/processed/countries.geojson`
- `data/cache/geocode_cache.json`

The scraper is designed to handle Wikipedia table differences, Amazing Race Fandom fallbacks, name normalization, route ordering, retry handling, and cached Nominatim geocoding.

## Project Structure

```text
/backend       FastAPI application and query services
/frontend      React + TypeScript visualization product
/scraper       Data crawling, parsing, cleaning, geocoding, and exporting
/data          Raw, processed, and cached data
/docs          API, scraper, and deployment notes
```

## Data Accuracy Note

The included sample dataset is intentionally compact and representative. Full historical coverage requires running the scraper with internet access. When exact task coordinates are unavailable, the pipeline geocodes the most precise available location, then falls back to city center.


## License, Data Sources, and Attribution

The original source code in this repository is licensed under the MIT License. See [LICENSE](LICENSE).

The included and generated datasets are compiled from publicly available information and may include transformed or normalized information from Wikipedia, Amazing Race Wiki / Fandom, Wikimedia Commons references, and OpenStreetMap geocoding data accessed through Nominatim. Source URLs are retained in exported records where practical through the `source_url` field.

Wikipedia, Wikimedia, Fandom, OpenStreetMap, and Nominatim content may carry their own license and attribution requirements. See [NOTICE.md](NOTICE.md) for the full attribution and reuse notes.
