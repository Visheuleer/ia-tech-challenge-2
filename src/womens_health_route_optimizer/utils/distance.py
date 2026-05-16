from math import asin, cos, radians, sin, sqrt

from womens_health_route_optimizer.domain import Coordinate


EARTH_RADIUS_KM = 6371.0


def calculate_distance_km(origin: Coordinate, destination: Coordinate) -> float:
    lat1 = radians(origin.latitude)
    lon1 = radians(origin.longitude)
    lat2 = radians(destination.latitude)
    lon2 = radians(destination.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    haversine_value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    central_angle = 2 * asin(sqrt(haversine_value))

    return EARTH_RADIUS_KM * central_angle


def estimate_travel_time_minutes(
    distance_km: float,
    average_speed_kmh: float,
) -> float:
    if average_speed_kmh <= 0:
        raise ValueError("average_speed_kmh must be greater than zero.")

    return (distance_km / average_speed_kmh) * 60