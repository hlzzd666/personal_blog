import ipaddress
import json
import math
from urllib.error import URLError
from urllib.request import urlopen

from backend.app.schemas.visitor_location import VisitorLocation


def calculate_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    earth_radius_km = 6371.0088
    latitude_delta = math.radians(destination_latitude - origin_latitude)
    longitude_delta = math.radians(destination_longitude - origin_longitude)
    origin_latitude_radians = math.radians(origin_latitude)
    destination_latitude_radians = math.radians(destination_latitude)
    distance_formula = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(origin_latitude_radians)
        * math.cos(destination_latitude_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(distance_formula), math.sqrt(1 - distance_formula))


def resolve_visitor_location(
    ip: str,
    owner_location_name: str,
    owner_latitude: float | None,
    owner_longitude: float | None,
) -> VisitorLocation:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return VisitorLocation(ip=ip, location_available=False, owner_location_name=owner_location_name)

    if not address.is_global:
        return VisitorLocation(
            ip=ip,
            city="本地网络",
            region="开发环境",
            country="本地",
            location_available=False,
            owner_location_name=owner_location_name,
        )

    try:
        with urlopen(f"https://ipwho.is/{ip}", timeout=3) as response:
            payload = json.load(response)
    except (TimeoutError, URLError, json.JSONDecodeError):
        return VisitorLocation(ip=ip, location_available=False, owner_location_name=owner_location_name)

    if not payload.get("success"):
        return VisitorLocation(ip=ip, location_available=False, owner_location_name=owner_location_name)

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    distance_km = None
    if owner_latitude is not None and owner_longitude is not None and latitude is not None and longitude is not None:
        distance_km = round(calculate_distance_km(latitude, longitude, owner_latitude, owner_longitude), 1)

    return VisitorLocation(
        ip=ip,
        city=payload.get("city"),
        region=payload.get("region"),
        country=payload.get("country"),
        location_available=True,
        owner_location_name=owner_location_name,
        distance_km=distance_km,
    )
