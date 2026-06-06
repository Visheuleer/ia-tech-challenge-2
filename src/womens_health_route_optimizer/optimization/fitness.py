from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    AttendanceType,
    DistributionCenter,
    Route,
    Vehicle,
)
from womens_health_route_optimizer.utils import (
    calculate_distance_km,
)
from womens_health_route_optimizer.optimization.simulation import simulate_route


PRIORITY_DELAY_MULTIPLIERS = {
    1: 10.0,
    2: 5.0,
    3: 2.0,
    4: 1.0,
}

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

    simulation = simulate_route(
        route_points=route_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    weighted_delay_minutes = sum(
        stop.delay_minutes
        * PRIORITY_DELAY_MULTIPLIERS[stop.point.priority]
        for stop in simulation.stops
    )

    return (
        weighted_delay_minutes
        * app_settings.time_window_penalty_weight
    )

def calculate_hormonal_transport_penalty(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> float:

    simulation = simulate_route(
        route_points=route_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    excess_minutes = 0.0

    for stop in simulation.stops:
        if (
            stop.point.attendance_type
            is AttendanceType.HORMONAL_MEDICATION
        ):
            excess_minutes += max(
                0.0,
                stop.elapsed_minutes_from_departure
                - app_settings.max_hormonal_transport_minutes,
            )

    return (
        excess_minutes
        * app_settings.hormonal_transport_penalty_weight
    )


def calculate_route_duration_penalty(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> tuple[float, float]:

    simulation = simulate_route(
        route_points=route_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    excess_minutes = max(
        0.0,
        simulation.total_duration_minutes
        - app_settings.max_route_duration_minutes,
    )

    penalty = (
        excess_minutes
        * app_settings.route_duration_penalty_weight
    )

    return penalty, simulation.total_duration_minutes


def evaluate_route(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    vehicle: Vehicle,
    app_settings: Settings = settings,
) -> Route:

    total_distance = calculate_total_distance_km(
        route_points=route_points,
        distribution_center=distribution_center,
    )

    priority_penalty = calculate_priority_penalty(
        route_points=route_points,
        app_settings=app_settings,
    )

    time_window_penalty = calculate_time_window_penalty(
        route_points=route_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    capacity_penalty = calculate_capacity_penalty(
        route_points=route_points,
        vehicle=vehicle,
        app_settings=app_settings,
    )

    hormonal_transport_penalty = (
        calculate_hormonal_transport_penalty(
            route_points=route_points,
            distribution_center=distribution_center,
            app_settings=app_settings,
        )
    )

    route_duration_penalty, total_duration_minutes = (
        calculate_route_duration_penalty(
            route_points=route_points,
            distribution_center=distribution_center,
            app_settings=app_settings,
        )
    )

    fitness = (
        total_distance
        + priority_penalty
        + time_window_penalty
        + capacity_penalty
        + hormonal_transport_penalty
        + route_duration_penalty
    )

    return Route(
        ordered_points=route_points,
        total_distance_km=total_distance,
        priority_penalty=priority_penalty,
        time_window_penalty=time_window_penalty,
        capacity_penalty=capacity_penalty,
        hormonal_transport_penalty=hormonal_transport_penalty,
        route_duration_penalty=route_duration_penalty,
        total_duration_minutes=total_duration_minutes,
        fitness=fitness,
    )