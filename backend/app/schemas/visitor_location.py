from pydantic import BaseModel


class VisitorLocation(BaseModel):
    ip: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    location_available: bool
    owner_location_name: str | None = None
    distance_km: float | None = None
