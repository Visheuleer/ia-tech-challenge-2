from womens_health_route_optimizer.config import Settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import Vehicle
from womens_health_route_optimizer.optimization import (
    calculate_capacity_penalty,
    calculate_hormonal_transport_penalty,
    calculate_route_duration_penalty,
    calculate_total_distance_km,
)
from womens_health_route_optimizer.domain.enums import VehicleType


def test_total_distance_is_positive_for_non_empty_route():
    center = load_distribution_center()
    points = load_attendance_points()

    distance = calculate_total_distance_km(
        route_points=points,
        distribution_center=center,
    )

    assert distance > 0


def test_capacity_penalty_is_zero_when_capacity_is_enough():
    points = load_attendance_points()
    vehicle = Vehicle(
        id="V001",
        name="Veículo teste",
        vehicle_type=VehicleType.OPERATIONAL_VAN,
        max_supply_capacity=100,
        is_refrigerated=False,
    )

    penalty = calculate_capacity_penalty(
        route_points=points,
        vehicle_capacity=vehicle.max_supply_capacity,
        app_settings=Settings(),
    )

    assert penalty == 0


def test_capacity_penalty_is_positive_when_capacity_is_exceeded():
    points = load_attendance_points()
    vehicle = Vehicle(
        id="V001",
        name="Veículo teste",
        vehicle_type=VehicleType.OPERATIONAL_VAN,
        max_supply_capacity=1,
        is_refrigerated=False,
    )

    penalty = calculate_capacity_penalty(
        route_points=points,
        vehicle_capacity=vehicle.max_supply_capacity,
        app_settings=Settings(),
    )

    assert penalty > 0

def test_hormonal_transport_penalty_is_zero_with_generous_limit():
    center = load_distribution_center()
    points = load_attendance_points()

    app_settings = Settings(
        max_hormonal_transport_minutes=1440,
    )

    penalty = calculate_hormonal_transport_penalty(
        route_points=points,
        distribution_center=center,
        app_settings=app_settings,
    )

    assert penalty == 0

def test_hormonal_transport_penalty_is_positive_with_short_limit():
    center = load_distribution_center()
    points = load_attendance_points()

    app_settings = Settings(
        max_hormonal_transport_minutes=1,
        hormonal_transport_penalty_weight=500.0,
    )

    penalty = calculate_hormonal_transport_penalty(
        route_points=points,
        distribution_center=center,
        app_settings=app_settings,
    )

    assert penalty > 0

def test_route_duration_penalty_is_zero_with_generous_limit():
    center = load_distribution_center()
    points = load_attendance_points()

    app_settings = Settings(
        max_route_duration_minutes=1440,
    )

    penalty, duration = calculate_route_duration_penalty(
        route_points=points,
        distribution_center=center,
        app_settings=app_settings,
    )

    assert duration > 0
    assert penalty == 0

def test_route_duration_penalty_is_positive_with_short_limit():
    center = load_distribution_center()
    points = load_attendance_points()

    app_settings = Settings(
        max_route_duration_minutes=60,
        route_duration_penalty_weight=500.0,
    )

    penalty, duration = calculate_route_duration_penalty(
        route_points=points,
        distribution_center=center,
        app_settings=app_settings,
    )

    assert duration > 60
    assert penalty > 0