from womens_health_route_optimizer.data import load_attendance_points
from womens_health_route_optimizer.optimization import (
    generate_initial_population,
    mutate,
    order_crossover,
)


def test_generate_initial_population_size():
    points = load_attendance_points()

    population = generate_initial_population(
        points=points,
        population_size=10,
    )

    assert len(population) == 10
    assert all(len(individual) == len(points) for individual in population)


def test_order_crossover_preserves_all_points():
    points = load_attendance_points()

    parent1 = points
    parent2 = list(reversed(points))

    child = order_crossover(parent1, parent2)

    assert len(child) == len(points)
    assert {point.id for point in child} == {point.id for point in points}


def test_mutation_preserves_all_points():
    points = load_attendance_points()

    mutated = mutate(
        route_points=points,
        mutation_probability=1.0,
    )

    assert len(mutated) == len(points)
    assert {point.id for point in mutated} == {point.id for point in points}