import random

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    DistributionCenter,
    FleetSolution,
    OptimizationResult,
    Vehicle,
    create_default_fleet,
)
from womens_health_route_optimizer.optimization.fitness import (
    evaluate_fleet_solution,
)
from womens_health_route_optimizer.optimization.operators import (
    fleet_crossover,
    generate_initial_fleet_population,
    mutate_fleet_solution,
    select_fleet_parents,
    sort_fleet_population_by_fitness,
    validate_fleet_solution,
)


class RouteOptimizer:
    def __init__(
        self,
        distribution_center: DistributionCenter,
        attendance_points: list[AttendancePoint],
        app_settings: Settings = settings,
        fleet: list[Vehicle] | None = None,
    ) -> None:
        self.distribution_center = distribution_center
        self.attendance_points = attendance_points
        self.app_settings = app_settings
        self.fleet = fleet or create_default_fleet()

    def optimize(self) -> OptimizationResult:
        if self.app_settings.random_seed is not None:
            random.seed(self.app_settings.random_seed)

        population = generate_initial_fleet_population(
            points=self.attendance_points,
            vehicles=self.fleet,
            population_size=self.app_settings.population_size,
        )

        evaluated_population = [
            evaluate_fleet_solution(
                solution=solution,
                distribution_center=self.distribution_center,
                app_settings=self.app_settings,
            )
            for solution in population
        ]

        evaluated_population = sort_fleet_population_by_fitness(
            evaluated_population
        )

        best_solution = evaluated_population[0]
        fitness_history = [best_solution.fitness]

        for _ in range(self.app_settings.generations):
            next_population: list[FleetSolution] = []

            elite = evaluated_population[: self.app_settings.elitism_size]

            next_population.extend(elite)

            while len(next_population) < self.app_settings.population_size:
                parent_a, parent_b = select_fleet_parents(
                    evaluated_population
                )

                child = fleet_crossover(parent_a, parent_b)

                child = mutate_fleet_solution(
                    solution=child,
                    mutation_probability=self.app_settings.mutation_probability,
                )

                validate_fleet_solution(
                    solution=child,
                    expected_points=self.attendance_points,
                )

                evaluated_child = evaluate_fleet_solution(
                    solution=child,
                    distribution_center=self.distribution_center,
                    app_settings=self.app_settings,
                )

                next_population.append(evaluated_child)

            evaluated_population = sort_fleet_population_by_fitness(
                next_population
            )

            current_best = evaluated_population[0]

            if current_best.fitness < best_solution.fitness:
                best_solution = current_best

            fitness_history.append(best_solution.fitness)

        return OptimizationResult(
            best_solution=best_solution,
            best_fitness=best_solution.fitness,
            generations=self.app_settings.generations,
            fitness_history=fitness_history,
        )