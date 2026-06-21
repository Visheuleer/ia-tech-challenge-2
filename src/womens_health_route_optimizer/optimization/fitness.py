from dataclasses import replace

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    AttendanceType,
    DistributionCenter,
    FleetSolution,
    VehicleRoute,
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
    vehicle_capacity: int,
    app_settings: Settings = settings,
) -> float:

    total_demand = sum(point.supply_demand for point in route_points)
    excess_demand = max(0, total_demand - vehicle_capacity)

    return excess_demand * app_settings.capacity_penalty_weight


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


def calculate_vehicle_compatibility_penalty(
    vehicle_route: VehicleRoute,
    app_settings: Settings = settings,
) -> float:

    incompatible_points = [
        point
        for point in vehicle_route.ordered_points
        if (
            point.attendance_type == AttendanceType.HORMONAL_MEDICATION
            and not vehicle_route.vehicle.is_refrigerated
        )
    ]

    return (
        len(incompatible_points)
        * app_settings.vehicle_compatibility_penalty_weight
    )


def _extract_penalty_value(value: float | tuple[float, ...]) -> float:
    if isinstance(value, tuple):
        return float(value[0])

    return float(value)


def evaluate_vehicle_route(
    vehicle_route: VehicleRoute,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> VehicleRoute:


    route_settings = replace(
        app_settings,
        average_vehicle_speed_kmh=(
            vehicle_route.vehicle.average_speed_kmh
            if vehicle_route.vehicle.average_speed_kmh is not None
            else app_settings.average_vehicle_speed_kmh
        ),
        vehicle_capacity=vehicle_route.vehicle.max_supply_capacity,
    )

    simulation = simulate_route(
        route_points=vehicle_route.ordered_points,
        distribution_center=distribution_center,
        app_settings=route_settings,
    )

    total_distance = float(simulation.total_distance_km)
    total_duration = float(simulation.total_duration_minutes)

    priority_penalty = _extract_penalty_value(
        calculate_priority_penalty(
            route_points=vehicle_route.ordered_points,
            app_settings=route_settings,
        )
    )

    time_window_penalty = _extract_penalty_value(
        calculate_time_window_penalty(
            route_points=vehicle_route.ordered_points,
            distribution_center=distribution_center,
            app_settings=route_settings,
        )
    )

    capacity_penalty = _extract_penalty_value(
        calculate_capacity_penalty(
            route_points=vehicle_route.ordered_points,
            vehicle_capacity=vehicle_route.vehicle.max_supply_capacity,
            app_settings=route_settings,
        )
    )

    hormonal_transport_penalty = _extract_penalty_value(
        calculate_hormonal_transport_penalty(
            route_points=vehicle_route.ordered_points,
            distribution_center=distribution_center,
            app_settings=route_settings,
        )
    )

    route_duration_penalty = _extract_penalty_value(
        calculate_route_duration_penalty(
            route_points=vehicle_route.ordered_points,
            distribution_center=distribution_center,
            app_settings=route_settings,
        )
    )

    vehicle_compatibility_penalty = _extract_penalty_value(
        calculate_vehicle_compatibility_penalty(
            vehicle_route=vehicle_route,
            app_settings=route_settings,
        )
    )

    fitness = (
        total_distance
        + priority_penalty
        + time_window_penalty
        + capacity_penalty
        + hormonal_transport_penalty
        + route_duration_penalty
        + vehicle_compatibility_penalty
    )

    return VehicleRoute(
        vehicle=vehicle_route.vehicle,
        ordered_points=vehicle_route.ordered_points,
        total_distance_km=total_distance,
        total_duration_minutes=total_duration,
        priority_penalty=priority_penalty,
        time_window_penalty=time_window_penalty,
        capacity_penalty=capacity_penalty,
        hormonal_transport_penalty=hormonal_transport_penalty,
        route_duration_penalty=route_duration_penalty,
        vehicle_compatibility_penalty=vehicle_compatibility_penalty,
        fitness=fitness,
    )


def evaluate_fleet_solution(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> FleetSolution:

    evaluated_vehicle_routes = [
        evaluate_vehicle_route(
            vehicle_route=vehicle_route,
            distribution_center=distribution_center,
            app_settings=app_settings,
        )
        for vehicle_route in solution.vehicle_routes
    ]

    total_distance = sum(
        vehicle_route.total_distance_km
        for vehicle_route in evaluated_vehicle_routes
    )

    total_duration = max(
        (
            vehicle_route.total_duration_minutes
            for vehicle_route in evaluated_vehicle_routes
        ),
        default=0.0,
    )

    priority_penalty = sum(
        vehicle_route.priority_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    time_window_penalty = sum(
        vehicle_route.time_window_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    capacity_penalty = sum(
        vehicle_route.capacity_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    hormonal_transport_penalty = sum(
        vehicle_route.hormonal_transport_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    route_duration_penalty = sum(
        vehicle_route.route_duration_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    vehicle_compatibility_penalty = sum(
        vehicle_route.vehicle_compatibility_penalty
        for vehicle_route in evaluated_vehicle_routes
    )

    fitness = (
        total_distance
        + priority_penalty
        + time_window_penalty
        + capacity_penalty
        + hormonal_transport_penalty
        + route_duration_penalty
        + vehicle_compatibility_penalty
    )

    return FleetSolution(
        vehicle_routes=evaluated_vehicle_routes,
        total_distance_km=total_distance,
        total_duration_minutes=total_duration,
        priority_penalty=priority_penalty,
        time_window_penalty=time_window_penalty,
        capacity_penalty=capacity_penalty,
        hormonal_transport_penalty=hormonal_transport_penalty,
        route_duration_penalty=route_duration_penalty,
        vehicle_compatibility_penalty=vehicle_compatibility_penalty,
        fitness=fitness,
    )