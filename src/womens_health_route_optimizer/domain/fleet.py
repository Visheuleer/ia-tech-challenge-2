from womens_health_route_optimizer.domain.models import Vehicle
from womens_health_route_optimizer.domain.enums import VehicleType


def create_default_fleet() -> list[Vehicle]:
    return [
        Vehicle(
            id="V001",
            name="Moto de atendimento",
            vehicle_type=VehicleType.MOTORCYCLE,
            max_supply_capacity=8,
            is_refrigerated=False,
            average_speed_kmh=40.0,
        ),
        Vehicle(
            id="V002",
            name="Veículo refrigerado",
            vehicle_type=VehicleType.REFRIGERATED_VEHICLE,
            max_supply_capacity=20,
            is_refrigerated=True,
            average_speed_kmh=35.0,
        ),
        Vehicle(
            id="V003",
            name="Van operacional",
            vehicle_type=VehicleType.OPERATIONAL_VAN,
            max_supply_capacity=30,
            is_refrigerated=False,
            average_speed_kmh=32.0,
        ),
    ]