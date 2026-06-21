from womens_health_route_optimizer.config import settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import (
    FleetSolution,
    VehicleRoute,
    create_default_fleet,
)
from womens_health_route_optimizer.domain.enums import (
    AttendanceType,
    VehicleType,
)
from womens_health_route_optimizer.optimization.fitness import (
    calculate_vehicle_compatibility_penalty,
    evaluate_fleet_solution,
)
from womens_health_route_optimizer.optimization.operators import (
    fleet_crossover,
    generate_initial_fleet_population,
    generate_initial_fleet_solution,
    mutate_fleet_solution,
    validate_fleet_solution,
)


def test_default_fleet_has_expected_vehicles():
    fleet = create_default_fleet()

    assert len(fleet) == 3

    vehicle_types = {vehicle.vehicle_type for vehicle in fleet}

    assert VehicleType.MOTORCYCLE in vehicle_types
    assert VehicleType.REFRIGERATED_VEHICLE in vehicle_types
    assert VehicleType.OPERATIONAL_VAN in vehicle_types

    refrigerated_vehicles = [
        vehicle
        for vehicle in fleet
        if vehicle.is_refrigerated
    ]

    assert len(refrigerated_vehicles) == 1
    assert refrigerated_vehicles[0].vehicle_type == VehicleType.REFRIGERATED_VEHICLE


def test_initial_fleet_population_keeps_all_points_once():
    points = load_attendance_points()
    fleet = create_default_fleet()

    population = generate_initial_fleet_population(
        points=points,
        vehicles=fleet,
        population_size=10,
    )

    assert len(population) == 10

    for solution in population:
        validate_fleet_solution(
            solution=solution,
            expected_points=points,
        )


def test_fleet_crossover_keeps_all_points_once():
    points = load_attendance_points()
    fleet = create_default_fleet()

    population = generate_initial_fleet_population(
        points=points,
        vehicles=fleet,
        population_size=2,
    )

    child = fleet_crossover(
        parent_a=population[0],
        parent_b=population[1],
    )

    validate_fleet_solution(
        solution=child,
        expected_points=points,
    )


def test_fleet_mutation_keeps_all_points_once():
    points = load_attendance_points()
    fleet = create_default_fleet()

    solution = generate_initial_fleet_solution(
        points=points,
        vehicles=fleet,
    )

    mutated = mutate_fleet_solution(
        solution=solution,
        mutation_probability=1.0,
    )

    validate_fleet_solution(
        solution=mutated,
        expected_points=points,
    )


def test_evaluate_fleet_solution_returns_valid_metrics():
    points = load_attendance_points()
    center = load_distribution_center()
    fleet = create_default_fleet()

    solution = generate_initial_fleet_solution(
        points=points,
        vehicles=fleet,
    )

    evaluated = evaluate_fleet_solution(
        solution=solution,
        distribution_center=center,
        app_settings=settings,
    )

    validate_fleet_solution(
        solution=evaluated,
        expected_points=points,
    )

    assert evaluated.fitness > 0
    assert evaluated.total_distance_km > 0
    assert evaluated.total_duration_minutes > 0
    assert len(evaluated.vehicle_routes) == len(fleet)

    for vehicle_route in evaluated.vehicle_routes:
        assert vehicle_route.fitness >= 0
        assert vehicle_route.total_distance_km >= 0
        assert vehicle_route.total_duration_minutes >= 0


def test_hormonal_medication_in_non_refrigerated_vehicle_has_penalty():
    points = load_attendance_points()
    fleet = create_default_fleet()

    non_refrigerated_vehicle = next(
        vehicle
        for vehicle in fleet
        if not vehicle.is_refrigerated
    )

    hormonal_point = next(
        point
        for point in points
        if point.attendance_type == AttendanceType.HORMONAL_MEDICATION
    )

    vehicle_route = VehicleRoute(
        vehicle=non_refrigerated_vehicle,
        ordered_points=[hormonal_point],
    )

    penalty = calculate_vehicle_compatibility_penalty(
        vehicle_route=vehicle_route,
        app_settings=settings,
    )

    assert penalty == settings.vehicle_compatibility_penalty_weight


def test_hormonal_medication_in_refrigerated_vehicle_has_no_penalty():
    points = load_attendance_points()
    fleet = create_default_fleet()

    refrigerated_vehicle = next(
        vehicle
        for vehicle in fleet
        if vehicle.is_refrigerated
    )

    hormonal_point = next(
        point
        for point in points
        if point.attendance_type == AttendanceType.HORMONAL_MEDICATION
    )

    vehicle_route = VehicleRoute(
        vehicle=refrigerated_vehicle,
        ordered_points=[hormonal_point],
    )

    penalty = calculate_vehicle_compatibility_penalty(
        vehicle_route=vehicle_route,
        app_settings=settings,
    )

    assert penalty == 0