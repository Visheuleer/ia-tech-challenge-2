from datetime import datetime, timedelta

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    DistributionCenter,
    Route,
    Vehicle,
)
from womens_health_route_optimizer.utils import (
    calculate_distance_km,
    estimate_travel_time_minutes,
)


def parse_route_start_time(value: str) -> datetime:
    hour, minute = value.split(":")
    return datetime(2026, 1, 1, int(hour), int(minute))


def calculate_total_distance_km(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
) -> float:
    if not route_points:
        return 0.0

    total_distance = 0.0

    total_distance += calculate_distance_km(
        distribution_center.coordinate,
        route_points[0].coordinate,
    )

    for current_point, next_point in zip(route_points, route_points[1:]):
        total_distance += calculate_distance_km(
            current_point.coordinate,
            next_point.coordinate,
        )

    total_distance += calculate_distance_km(
        route_points[-1].coordinate,
        distribution_center.coordinate,
    )

    return total_distance


def calculate_priority_penalty(
    route_points: list[AttendancePoint],
    app_settings: Settings = settings,
) -> float:
    penalty = 0.0

    for position, point in enumerate(route_points, start=1):
        urgency_score = 5 - point.priority
        penalty += urgency_score * position

    return penalty * app_settings.priority_penalty_weight


def calculate_capacity_penalty(
    route_points: list[AttendancePoint],
    vehicle: Vehicle,
    app_settings: Settings = settings,
) -> float:
    total_demand = sum(point.supply_demand for point in route_points)
    excess = max(0, total_demand - vehicle.max_supply_capacity)

    return excess * app_settings.capacity_penalty_weight


def calculate_time_window_penalty(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> float:
    if not route_points:
        return 0.0

    penalty_minutes = 0.0
    current_time = parse_route_start_time(app_settings.route_start_time)
    previous_coordinate = distribution_center.coordinate

    for point in route_points:
        distance_km = calculate_distance_km(
            previous_coordinate,
            point.coordinate,
        )

        travel_minutes = estimate_travel_time_minutes(
            distance_km,
            app_settings.average_vehicle_speed_kmh,
        )

        current_time += timedelta(minutes=travel_minutes)

        window_start = datetime.combine(
            current_time.date(),
            point.time_window_start,
        )

        window_end = datetime.combine(
            current_time.date(),
            point.time_window_end,
        )

        if current_time < window_start:
            current_time = window_start

        if current_time > window_end:
            delay_minutes = (current_time - window_end).total_seconds() / 60
            penalty_minutes += delay_minutes

        current_time += timedelta(minutes=point.service_time_minutes)
        previous_coordinate = point.coordinate

    return penalty_minutes * app_settings.time_window_penalty_weight


def evaluate_route(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    vehicle: Vehicle,
    app_settings: Settings = settings,
) -> Route:
    total_distance = calculate_total_distance_km(
        route_points,
        distribution_center,
    )

    priority_penalty = calculate_priority_penalty(
        route_points,
        app_settings,
    )

    time_window_penalty = calculate_time_window_penalty(
        route_points,
        distribution_center,
        app_settings,
    )

    capacity_penalty = calculate_capacity_penalty(
        route_points,
        vehicle,
        app_settings,
    )

    fitness = (
        total_distance
        + priority_penalty
        + time_window_penalty
        + capacity_penalty
    )

    return Route(
        ordered_points=route_points,
        total_distance_km=total_distance,
        priority_penalty=priority_penalty,
        time_window_penalty=time_window_penalty,
        capacity_penalty=capacity_penalty,
        fitness=fitness,
    )