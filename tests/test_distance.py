from womens_health_route_optimizer.domain import Coordinate
from womens_health_route_optimizer.utils import (
    calculate_distance_km,
    estimate_travel_time_minutes,
)


def test_calculate_distance_between_same_point_is_zero():
    coordinate = Coordinate(latitude=-23.550520, longitude=-46.633308)

    distance = calculate_distance_km(coordinate, coordinate)

    assert distance == 0


def test_calculate_distance_between_different_points_is_positive():
    origin = Coordinate(latitude=-23.550520, longitude=-46.633308)
    destination = Coordinate(latitude=-23.520100, longitude=-46.620500)

    distance = calculate_distance_km(origin, destination)

    assert distance > 0


def test_estimate_travel_time_minutes():
    travel_time = estimate_travel_time_minutes(
        distance_km=35,
        average_speed_kmh=35,
    )

    assert travel_time == 60


def test_estimate_travel_time_rejects_invalid_speed():
    try:
        estimate_travel_time_minutes(
            distance_km=10,
            average_speed_kmh=0,
        )
    except ValueError as error:
        assert "average_speed_kmh must be greater than zero" in str(error)
    else:
        raise AssertionError("Expected ValueError")