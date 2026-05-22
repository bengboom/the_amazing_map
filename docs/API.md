# API

Base URL:

```text
http://127.0.0.1:8000
```

## Endpoints

### `GET /health`

Returns service status and dataset counts.

### `GET /seasons`

Returns all seasons.

Query filters:

- `season`: one or more season numbers

### `GET /countries`

Returns country-level aggregates.

Query filters:

- `season`
- `country`

### `GET /locations`

Returns normalized visited locations.

Query filters:

- `season`
- `country`
- `episode`

### `GET /routes`

Returns chronological route segments.

Query filters:

- `season`
- `country`
- `episode`

### `GET /stats`

Returns global summary statistics including most visited countries, most visited cities, estimated total distance, countries never revisited, and unique continents.

### `GET /export/geojson`

Exports selected locations and routes as a GeoJSON FeatureCollection.

Query filters:

- `season`
- `country`
- `episode`
