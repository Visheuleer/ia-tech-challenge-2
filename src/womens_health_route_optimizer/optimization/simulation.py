from datetime import datetime, timedelta

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    DistributionCenter,
    RouteStop,
)
from womens_health_route_optimizer.optimization.fitness import parse_route_start_time
from womens_health_route_optimizer.utils import (
    calculate_distance_km,
    estimate_travel_time_minutes,
)


def simulate_route_stops(
    route_points: list[AttendancePoint],
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> list[RouteStop]:
    stops: list[RouteStop] = []

    current_time = parse_route_start_time(app_settings.route_start_time)
    previous_coordinate = distribution_center.coordinate

    for sequence, point in enumerate(route_points, start=1):
        leg_distance_km = calculate_distance_km(
            previous_coordinate,
            point.coordinate,
        )

        travel_minutes = estimate_travel_time_minutes(
            leg_distance_km,
            app_settings.average_vehicle_speed_kmh,
        )

        current_time += timedelta(minutes=travel_minutes)

        estimated_arrival_time = current_time

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
            waiting_minutes = (window_start - current_time).total_seconds() / 60
            current_time = window_start

        if current_time > window_end:
            delay_minutes = (current_time - window_end).total_seconds() / 60

        service_start_time = current_time

        stops.append(
            RouteStop(
                sequence=sequence,
                point=point,
                leg_distance_km=leg_distance_km,
                estimated_arrival_time=estimated_arrival_time.time().replace(microsecond=0),
                service_start_time=service_start_time.time().replace(microsecond=0),
                time_window_start=point.time_window_start,
                time_window_end=point.time_window_end,
                waiting_minutes=waiting_minutes,
                delay_minutes=delay_minutes,
            )
        )

        current_time += timedelta(minutes=point.service_time_minutes)
        previous_coordinate = point.coordinate

    return stops