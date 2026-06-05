from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.optimization import (
    simulate_route,
    simulate_route_stops,
)


def test_simulate_route_stops_returns_one_stop_per_point():
    center = load_distribution_center()
    points = load_attendance_points()

    stops = simulate_route_stops(
        route_points=points,
        distribution_center=center,
    )

    assert len(stops) == len(points)


def test_simulate_route_stops_sequence_is_ordered():
    center = load_distribution_center()
    points = load_attendance_points()

    stops = simulate_route_stops(
        route_points=points,
        distribution_center=center,
    )

    sequences = [stop.sequence for stop in stops]

    assert sequences == list(range(1, len(points) + 1))


def test_simulate_route_stops_has_arrival_and_service_start():
    center = load_distribution_center()
    points = load_attendance_points()

    stops = simulate_route_stops(
        route_points=points,
        distribution_center=center,
    )

    first_stop = stops[0]

    assert first_stop.estimated_arrival_time is not None
    assert first_stop.service_start_time is not None
    assert first_stop.leg_distance_km > 0

def test_simulate_route_includes_return_to_distribution_center():
    center = load_distribution_center()
    points = load_attendance_points()

    simulation = simulate_route(
        route_points=points,
        distribution_center=center,
    )

    assert simulation.return_leg_distance_km > 0
    assert simulation.total_duration_minutes > 0
    assert simulation.return_time is not None

def test_simulation_tracks_elapsed_minutes_from_departure():
    center = load_distribution_center()
    points = load_attendance_points()

    simulation = simulate_route(
        route_points=points,
        distribution_center=center,
    )

    elapsed_values = [
        stop.elapsed_minutes_from_departure
        for stop in simulation.stops
    ]

    assert all(value >= 0 for value in elapsed_values)
    assert elapsed_values == sorted(elapsed_values)