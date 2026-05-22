from pydantic import BaseModel


class Season(BaseModel):
    season: int
    title: str
    year: int | None = None
    color: str
    episode_count: int
    location_count: int


class Location(BaseModel):
    id: str
    season: int
    episode: int | None = None
    leg: int | None = None
    country: str
    city: str
    location_name: str
    lat: float
    lng: float
    type: str
    order: int
    continent: str | None = None
    source_url: str | None = None


class Route(BaseModel):
    id: str
    season: int
    episode: int | None = None
    leg: int | None = None
    from_location_id: str
    to_location_id: str
    from_city: str
    to_city: str
    from_country: str
    to_country: str
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    order: int
    distance_km: float


class CountryAggregate(BaseModel):
    country: str
    visits: int
    seasons: list[int]
    episodes: list[str]
    cities: list[str]
    pit_stops: list[str]
    task_locations: list[str]
    continent: str | None = None
    lat: float
    lng: float
