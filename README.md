# The Amazing Race World Map Explorer

A production-style interactive web application for exploring countries, cities, legs, episodes, pit stops, and routes across the US version of **The Amazing Race**.

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
