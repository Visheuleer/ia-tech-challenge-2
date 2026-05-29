from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import AttendanceType


def test_load_distribution_center():
    center = load_distribution_center()

    assert center.id == "DC001"
    assert center.name == "Central de Distribuição Hospitalar"
    assert center.coordinate.latitude is not None
    assert center.coordinate.longitude is not None


def test_load_attendance_points_count():
    points = load_attendance_points()

    assert len(points) == 20


def test_load_attendance_points_types():
    points = load_attendance_points()

    attendance_types = {point.attendance_type for point in points}

    assert AttendanceType.OBSTETRIC_EMERGENCY in attendance_types
    assert AttendanceType.DOMESTIC_VIOLENCE in attendance_types
    assert AttendanceType.HORMONAL_MEDICATION in attendance_types
    assert AttendanceType.POSTPARTUM_CARE in attendance_types


def test_load_attendance_points_priorities():
    points = load_attendance_points()

    priorities_by_type = {
        point.attendance_type: point.priority
        for point in points
    }

    assert priorities_by_type[AttendanceType.OBSTETRIC_EMERGENCY] == 1
    assert priorities_by_type[AttendanceType.DOMESTIC_VIOLENCE] == 2
    assert priorities_by_type[AttendanceType.HORMONAL_MEDICATION] == 3
    assert priorities_by_type[AttendanceType.POSTPARTUM_CARE] == 4