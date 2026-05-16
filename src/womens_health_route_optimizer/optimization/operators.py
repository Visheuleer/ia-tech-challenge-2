import random

from womens_health_route_optimizer.domain import AttendancePoint, Route


def generate_initial_population(
    points: list[AttendancePoint],
    population_size: int,
) -> list[list[AttendancePoint]]:
    return [
        random.sample(points, len(points))
        for _ in range(population_size)
    ]


def sort_population_by_fitness(routes: list[Route]) -> list[Route]:
    return sorted(routes, key=lambda route: route.fitness)


def select_parents(
    evaluated_routes: list[Route],
) -> tuple[list[AttendancePoint], list[AttendancePoint]]:
    if not evaluated_routes:
        raise ValueError("evaluated_routes cannot be empty.")

    weights = [
        1 / route.fitness if route.fitness > 0 else 1
        for route in evaluated_routes
    ]

    parent_routes = random.choices(
        evaluated_routes,
        weights=weights,
        k=2,
    )

    return (
        parent_routes[0].ordered_points,
        parent_routes[1].ordered_points,
    )


def order_crossover(
    parent1: list[AttendancePoint],
    parent2: list[AttendancePoint],
) -> list[AttendancePoint]:
    if len(parent1) != len(parent2):
        raise ValueError("Parents must have the same length.")

    size = len(parent1)

    if size < 2:
        return parent1.copy()

    start, end = sorted(random.sample(range(size), 2))

    child: list[AttendancePoint | None] = [None] * size

    child[start:end] = parent1[start:end]

    parent2_points = [
        point
        for point in parent2
        if point not in child
    ]

    parent2_index = 0

    for index in range(size):
        if child[index] is None:
            child[index] = parent2_points[parent2_index]
            parent2_index += 1

    return [point for point in child if point is not None]


def mutate(
    route_points: list[AttendancePoint],
    mutation_probability: float,
) -> list[AttendancePoint]:
    mutated_route = route_points.copy()

    if random.random() > mutation_probability:
        return mutated_route

    if len(mutated_route) < 2:
        return mutated_route

    index1, index2 = random.sample(range(len(mutated_route)), 2)

    mutated_route[index1], mutated_route[index2] = (
        mutated_route[index2],
        mutated_route[index1],
    )

    return mutated_route