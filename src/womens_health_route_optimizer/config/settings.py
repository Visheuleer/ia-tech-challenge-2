from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[3]
    data_dir: Path = project_root / "data"

    attendance_points_file: Path = data_dir / "attendance_points.csv"
    distribution_center_file: Path = data_dir / "distribution_center.csv"

    population_size: int = 100
    generations: int = 200
    mutation_probability: float = 0.20
    elitism_size: int = 1

    vehicle_capacity: int = 20

    average_vehicle_speed_kmh: float = 35.0
    route_start_time: str = "08:00"

    priority_penalty_weight: float = 1000.0
    time_window_penalty_weight: float = 500.0
    capacity_penalty_weight: float = 2000.0


settings = Settings()