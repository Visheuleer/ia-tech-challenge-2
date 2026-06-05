from datetime import datetime, timedelta

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    DistributionCenter,
    RouteSimulation,
    RouteStop,
)
from womens_health_route_optimizer.utils import (
    calculate_distance_km,
    estimate_travel_time_minutes,
)


def parse_route_start_time(value: str) -> datetime:
    hour, minute = value.split(":")
    return datetime(2026, 1, 1, int(hour), int(minute))


def simulate_route(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> RouteSimulation:

    stops: list[RouteStop] = []

    route_start = parse_route_start_time(app_settings.route_start_time)
    current_time = route_start
    previous_coordinate = distribution_center.coordinate

    for sequence, point in enumerate(route_points, start=1):
        leg_distance_km = calculate_distance_km(
            previous_coordinate,
            point.coordinate,
        )

        travel_minutes = estimate_travel_time_minutes(
            distance_km=leg_distance_km,
            average_speed_kmh=app_settings.average_vehicle_speed_kmh,
        )

        current_time += timedelta(minutes=travel_minutes)
        estimated_arrival = current_time

        window_start = datetime.combine(
            current_time.date(),
            point.time_window_start,
        )

        window_end = datetime.combine(
            current_time.date(),
            point.time_window_end,
        )

        waiting_minutes = 0.0
        delay_minutes = 0.0

        if current_time < window_start:
            waiting_minutes = (
                window_start - current_time
            ).total_seconds() / 60

            current_time = window_start

        if current_time > window_end:
            delay_minutes = (
                current_time - window_end
            ).total_seconds() / 60

        service_start = current_time

        elapsed_minutes = (
            service_start - route_start
        ).total_seconds() / 60

        stops.append(
            RouteStop(
                sequence=sequence,
                point=point,
                leg_distance_km=leg_distance_km,
                estimated_arrival_time=estimated_arrival.time().replace(
                    microsecond=0
                ),
                service_start_time=service_start.time().replace(
                    microsecond=0
                ),
                time_window_start=point.time_window_start,
                time_window_end=point.time_window_end,
                waiting_minutes=waiting_minutes,
                delay_minutes=delay_minutes,
                elapsed_minutes_from_departure=elapsed_minutes,
            )
        )

        current_time += timedelta(
            minutes=point.service_time_minutes
        )

        previous_coordinate = point.coordinate

    return_leg_distance_km = 0.0

    if route_points:
        return_leg_distance_km = calculate_distance_km(
            previous_coordinate,
            distribution_center.coordinate,
        )

        return_travel_minutes = estimate_travel_time_minutes(
            distance_km=return_leg_distance_km,
            average_speed_kmh=app_settings.average_vehicle_speed_kmh,
        )

        current_time += timedelta(minutes=return_travel_minutes)

    total_duration_minutes = (
        current_time - route_start
    ).total_seconds() / 60

    return RouteSimulation(
        stops=stops,
        total_duration_minutes=total_duration_minutes,
        return_time=current_time.time().replace(microsecond=0),
        return_leg_distance_km=return_leg_distance_km,
    )


def simulate_route_stops(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> list[RouteStop]:

    return simulate_route(
        route_points=route_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    ).stops