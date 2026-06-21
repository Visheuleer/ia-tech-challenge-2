from dataclasses import dataclass, field
from datetime import time, datetime

from womens_health_route_optimizer.domain.enums import AttendanceType, VehicleType


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DistributionCenter:
    id: str
    name: str
    coordinate: Coordinate
    notes: str = ""


@dataclass(frozen=True)
class AttendancePoint:
    id: str
    name: str
    attendance_type: AttendanceType
    priority: int
    coordinate: Coordinate
    supply_demand: int
    time_window_start: time
    time_window_end: time
    service_time_minutes: int
    notes: str = ""


@dataclass(frozen=True)
class Vehicle:
    id: str
    name: str
    vehicle_type: VehicleType
    max_supply_capacity: int
    is_refrigerated: bool = False
    average_speed_kmh: float | None = None


@dataclass(frozen=True)
class RouteStop:
    sequence: int
    point: AttendancePoint
    leg_distance_km: float
    estimated_arrival_time: time
    service_start_time: time
    time_window_start: time
    time_window_end: time
    waiting_minutes: float
    delay_minutes: float
    elapsed_minutes_from_departure: float

@dataclass
class RouteSimulation:
    stops: list[RouteStop]
    total_duration_minutes: float
    return_time: datetime
    return_leg_distance_km: float

    @property
    def total_distance_km(self) -> float:
        stops_distance = sum(
            stop.leg_distance_km
            for stop in self.stops
        )

        return stops_distance + self.return_leg_distance_km


@dataclass
class VehicleRoute:
    vehicle: Vehicle
    ordered_points: list[AttendancePoint]
    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    priority_penalty: float = 0.0
    time_window_penalty: float = 0.0
    capacity_penalty: float = 0.0
    hormonal_transport_penalty: float = 0.0
    route_duration_penalty: float = 0.0
    vehicle_compatibility_penalty: float = 0.0
    fitness: float = 0.0

    @property
    def total_supply_demand(self) -> int:
        return sum(point.supply_demand for point in self.ordered_points)


@dataclass
class FleetSolution:
    vehicle_routes: list[VehicleRoute]
    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    priority_penalty: float = 0.0
    time_window_penalty: float = 0.0
    capacity_penalty: float = 0.0
    hormonal_transport_penalty: float = 0.0
    route_duration_penalty: float = 0.0
    vehicle_compatibility_penalty: float = 0.0
    fitness: float = 0.0

    @property
    def total_supply_demand(self) -> int:
        return sum(
            vehicle_route.total_supply_demand
            for vehicle_route in self.vehicle_routes
        )

    @property
    def all_ordered_points(self) -> list[AttendancePoint]:
        return [
            point
            for vehicle_route in self.vehicle_routes
            for point in vehicle_route.ordered_points
        ]


@dataclass
class OptimizationResult:
    best_solution: FleetSolution
    best_fitness: float
    generations: int
    fitness_history: list[float] = field(default_factory=list)

    @property
    def best_route(self) -> FleetSolution:
        return self.best_solution