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
    evaluate_route,
)


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
        max_supply_capacity=100,
    )

    penalty = calculate_capacity_penalty(
        route_points=points,
        vehicle=vehicle,
    )

    assert penalty == 0


def test_capacity_penalty_is_positive_when_capacity_is_exceeded():
    points = load_attendance_points()
    vehicle = Vehicle(
        id="V001",
        name="Veículo teste",
        max_supply_capacity=10,
    )

    penalty = calculate_capacity_penalty(
        route_points=points,
        vehicle=vehicle,
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

def test_evaluate_route_returns_route_with_all_metrics():
    center = load_distribution_center()
    points = load_attendance_points()

    vehicle = Vehicle(
        id="V001",
        name="Veículo teste",
        max_supply_capacity=20,
    )

    route = evaluate_route(
        route_points=points,
        distribution_center=center,
        vehicle=vehicle,
        app_settings=Settings(),
    )

    assert route.total_distance_km > 0
    assert route.total_duration_minutes > 0
    assert route.priority_penalty >= 0
    assert route.time_window_penalty >= 0
    assert route.capacity_penalty >= 0
    assert route.hormonal_transport_penalty >= 0
    assert route.route_duration_penalty >= 0
    assert route.fitness > 0
    assert route.total_supply_demand == 40