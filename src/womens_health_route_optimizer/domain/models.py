from dataclasses import dataclass, field
from datetime import time

from womens_health_route_optimizer.domain.enums import AttendanceType


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
    max_supply_capacity: int


@dataclass
class Route:
    ordered_points: list[AttendancePoint]
    total_distance_km: float = 0.0
    priority_penalty: float = 0.0
    time_window_penalty: float = 0.0
    capacity_penalty: float = 0.0
    hormonal_transport_penalty: float = 0.0
    route_duration_penalty: float = 0.0
    total_duration_minutes: float = 0.0
    fitness: float = 0.0

    @property
    def total_supply_demand(self) -> int:
        return sum(point.supply_demand for point in self.ordered_points)


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

@dataclass(frozen=True)
class RouteSimulation:
    stops: list[RouteStop]
    total_duration_minutes: float
    return_time: time
    return_leg_distance_km: float


@dataclass
class OptimizationResult:
    best_route: Route
    best_fitness: float
    generations: int
    fitness_history: list[float] = field(default_factory=list)