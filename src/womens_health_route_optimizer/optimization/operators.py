import random

from womens_health_route_optimizer.domain.enums import AttendanceType
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    FleetSolution,
    Vehicle,
    VehicleRoute,
)


def create_empty_fleet_solution(vehicles: list[Vehicle]) -> FleetSolution:
    return FleetSolution(
        vehicle_routes=[
            VehicleRoute(
                vehicle=vehicle,
                ordered_points=[],
            )
            for vehicle in vehicles
        ]
    )


def validate_fleet_solution(
    solution: FleetSolution,
    expected_points: list[AttendancePoint],
) -> None:

    expected_ids = {point.id for point in expected_points}
    actual_ids = [
        point.id
        for vehicle_route in solution.vehicle_routes
        for point in vehicle_route.ordered_points
    ]

    actual_ids_set = set(actual_ids)

    duplicated_ids = {
        point_id
        for point_id in actual_ids
        if actual_ids.count(point_id) > 1
    }

    missing_ids = expected_ids - actual_ids_set
    unexpected_ids = actual_ids_set - expected_ids

    if duplicated_ids:
        raise ValueError(
            f"Solução de frota possui pontos duplicados: "
            f"{sorted(duplicated_ids)}"
        )

    if missing_ids:
        raise ValueError(
            f"Solução de frota não possui todos os pontos esperados. "
            f"Ausentes: {sorted(missing_ids)}"
        )

    if unexpected_ids:
        raise ValueError(
            f"Solução de frota possui pontos inesperados: "
            f"{sorted(unexpected_ids)}"
        )


def generate_initial_fleet_solution(
    points: list[AttendancePoint],
    vehicles: list[Vehicle],
) -> FleetSolution:

    solution = create_empty_fleet_solution(vehicles)

    shuffled_points = points[:]
    random.shuffle(shuffled_points)

    refrigerated_routes = [
        vehicle_route
        for vehicle_route in solution.vehicle_routes
        if vehicle_route.vehicle.is_refrigerated
    ]

    all_routes = solution.vehicle_routes

    for point in shuffled_points:
        preferred_routes = all_routes

        if point.attendance_type == AttendanceType.HORMONAL_MEDICATION and refrigerated_routes:
            preferred_routes = refrigerated_routes

        selected_route = random.choice(preferred_routes)
        selected_route.ordered_points.append(point)

    for vehicle_route in solution.vehicle_routes:
        random.shuffle(vehicle_route.ordered_points)

    return solution


def generate_initial_fleet_population(
    points: list[AttendancePoint],
    vehicles: list[Vehicle],
    population_size: int,
) -> list[FleetSolution]:

    population = [
        generate_initial_fleet_solution(
            points=points,
            vehicles=vehicles,
        )
        for _ in range(population_size)
    ]

    for solution in population:
        validate_fleet_solution(solution, points)

    return population


def flatten_fleet_solution(solution: FleetSolution) -> list[AttendancePoint]:
    return [
        point
        for vehicle_route in solution.vehicle_routes
        for point in vehicle_route.ordered_points
    ]


def clone_fleet_structure(solution: FleetSolution) -> FleetSolution:
    return FleetSolution(
        vehicle_routes=[
            VehicleRoute(
                vehicle=vehicle_route.vehicle,
                ordered_points=[],
            )
            for vehicle_route in solution.vehicle_routes
        ]
    )


def fleet_crossover(
    parent_a: FleetSolution,
    parent_b: FleetSolution,
) -> FleetSolution:

    child = clone_fleet_structure(parent_a)

    number_of_routes = len(parent_a.vehicle_routes)

    if number_of_routes != len(parent_b.vehicle_routes):
        raise ValueError(
            "Os pais possuem quantidades diferentes de rotas/veículos."
        )

    selected_route_indexes = set(
        random.sample(
            range(number_of_routes),
            k=max(1, number_of_routes // 2),
        )
    )

    used_point_ids: set[str] = set()

    for index in selected_route_indexes:
        copied_points = parent_a.vehicle_routes[index].ordered_points[:]

        child.vehicle_routes[index].ordered_points.extend(copied_points)

        used_point_ids.update(point.id for point in copied_points)

    remaining_points = [
        point
        for point in flatten_fleet_solution(parent_b)
        if point.id not in used_point_ids
    ]

    route_index = 0

    for point in remaining_points:
        attempts = 0

        while attempts < number_of_routes:
            target_route = child.vehicle_routes[route_index]

            if (
                    point.attendance_type == AttendanceType.HORMONAL_MEDICATION
                    and not target_route.vehicle.is_refrigerated
            ):
                route_index = (route_index + 1) % number_of_routes
                attempts += 1
                continue

            target_route.ordered_points.append(point)
            route_index = (route_index + 1) % number_of_routes
            break

        else:
            child.vehicle_routes[route_index].ordered_points.append(point)
            route_index = (route_index + 1) % number_of_routes

    return child


def mutate_fleet_solution(
    solution: FleetSolution,
    mutation_probability: float,
) -> FleetSolution:

    mutated = clone_fleet_structure(solution)

    for index, vehicle_route in enumerate(solution.vehicle_routes):
        mutated.vehicle_routes[index].ordered_points = (
            vehicle_route.ordered_points[:]
        )

    if random.random() > mutation_probability:
        return mutated

    mutation_type = random.choice(
        [
            "swap_inside_route",
            "move_between_routes",
            "swap_between_routes",
        ]
    )

    non_empty_routes = [
        vehicle_route
        for vehicle_route in mutated.vehicle_routes
        if vehicle_route.ordered_points
    ]

    if not non_empty_routes:
        return mutated

    if mutation_type == "swap_inside_route":
        candidate_routes = [
            vehicle_route
            for vehicle_route in non_empty_routes
            if len(vehicle_route.ordered_points) >= 2
        ]

        if candidate_routes:
            selected_route = random.choice(candidate_routes)
            first_index, second_index = random.sample(
                range(len(selected_route.ordered_points)),
                2,
            )

            selected_route.ordered_points[first_index], selected_route.ordered_points[second_index] = (
                selected_route.ordered_points[second_index],
                selected_route.ordered_points[first_index],
            )

    elif mutation_type == "move_between_routes":
        source_route = random.choice(non_empty_routes)
        target_route = random.choice(mutated.vehicle_routes)

        if source_route is not target_route:
            point_index = random.randrange(len(source_route.ordered_points))
            point = source_route.ordered_points.pop(point_index)
            insert_index = random.randrange(
                len(target_route.ordered_points) + 1
            )
            target_route.ordered_points.insert(insert_index, point)

    elif mutation_type == "swap_between_routes":
        if len(non_empty_routes) >= 2:
            first_route, second_route = random.sample(non_empty_routes, 2)

            first_index = random.randrange(len(first_route.ordered_points))
            second_index = random.randrange(len(second_route.ordered_points))

            first_route.ordered_points[first_index], second_route.ordered_points[second_index] = (
                second_route.ordered_points[second_index],
                first_route.ordered_points[first_index],
            )

    return mutated


def sort_fleet_population_by_fitness(
    solutions: list[FleetSolution],
) -> list[FleetSolution]:

    return sorted(solutions, key=lambda solution: solution.fitness)


def select_fleet_parents(
    evaluated_solutions: list[FleetSolution],
) -> tuple[FleetSolution, FleetSolution]:

    weights = [
        1 / (solution.fitness + 1e-9)
        for solution in evaluated_solutions
    ]

    parents = random.choices(
        evaluated_solutions,
        weights=weights,
        k=2,
    )

    return parents[0], parents[1]