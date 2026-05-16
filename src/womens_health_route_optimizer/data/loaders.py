import csv
from datetime import time
from pathlib import Path

from womens_health_route_optimizer.config import settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_PRIORITIES,
    AttendancePoint,
    AttendanceType,
    Coordinate,
    DistributionCenter,
)


def parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def load_distribution_center(
    file_path: Path | None = None,
) -> DistributionCenter:
    path = file_path or settings.distribution_center_file

    with path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        row = next(reader)

    return DistributionCenter(
        id=row["id"],
        name=row["name"],
        coordinate=Coordinate(
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        ),
        notes=row.get("notes", ""),
    )


def load_attendance_points(
    file_path: Path | None = None,
) -> list[AttendancePoint]:
    path = file_path or settings.attendance_points_file
    points: list[AttendancePoint] = []

    with path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            attendance_type = AttendanceType(row["type"])

            points.append(
                AttendancePoint(
                    id=row["id"],
                    name=row["name"],
                    attendance_type=attendance_type,
                    priority=ATTENDANCE_TYPE_PRIORITIES[attendance_type],
                    coordinate=Coordinate(
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                    ),
                    supply_demand=int(row["supply_demand"]),
                    time_window_start=parse_time(row["time_window_start"]),
                    time_window_end=parse_time(row["time_window_end"]),
                    service_time_minutes=int(row["service_time_minutes"]),
                    notes=row.get("notes", ""),
                )
            )

    return points