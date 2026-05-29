from womens_health_route_optimizer.config import Settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import Vehicle
from womens_health_route_optimizer.optimization import (
    calculate_capacity_penalty,
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


def test_evaluate_route_returns_route_with_fitness():
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
    assert route.fitness > 0
    assert route.total_supply_demand == 40