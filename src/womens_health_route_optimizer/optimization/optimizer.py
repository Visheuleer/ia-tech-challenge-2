from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    AttendancePoint,
    DistributionCenter,
    OptimizationResult,
    Route,
    Vehicle,
)
from womens_health_route_optimizer.optimization.fitness import evaluate_route
from womens_health_route_optimizer.optimization.operators import (
    generate_initial_population,
    mutate,
    order_crossover,
    select_parents,
    sort_population_by_fitness,
)
import random


class RouteOptimizer:
    def __init__(
        self,
        distribution_center: DistributionCenter,
        attendance_points: list[AttendancePoint],
        vehicle: Vehicle,
        app_settings: Settings = settings,
    ) -> None:
        if not attendance_points:
            raise ValueError("attendance_points cannot be empty.")

        self.distribution_center = distribution_center
        self.attendance_points = attendance_points
        self.vehicle = vehicle
        self.settings = app_settings

    def optimize(self) -> OptimizationResult:
        if self.settings.random_seed is not None:
            random.seed(self.settings.random_seed)
        population = generate_initial_population(
            points=self.attendance_points,
            population_size=self.settings.population_size,
        )

        fitness_history: list[float] = []
        best_route: Route | None = None

        for _generation in range(1, self.settings.generations + 1):
            evaluated_routes = self._evaluate_population(population)
            evaluated_routes = sort_population_by_fitness(evaluated_routes)

            current_best_route = evaluated_routes[0]
            fitness_history.append(current_best_route.fitness)

            if best_route is None or current_best_route.fitness < best_route.fitness:
                best_route = current_best_route

            population = self._build_next_population(evaluated_routes)

        if best_route is None:
            raise RuntimeError("Optimization finished without a best route.")

        return OptimizationResult(
            best_route=best_route,
            best_fitness=best_route.fitness,
            generations=self.settings.generations,
            fitness_history=fitness_history,
        )

    def _evaluate_population(
        self,
        population: list[list[AttendancePoint]],
    ) -> list[Route]:
        return [
            evaluate_route(
                route_points=individual,
                distribution_center=self.distribution_center,
                vehicle=self.vehicle,
                app_settings=self.settings,
            )
            for individual in population
        ]

    def _build_next_population(
        self,
        evaluated_routes: list[Route],
    ) -> list[list[AttendancePoint]]:
        new_population: list[list[AttendancePoint]] = []

        elite_routes = evaluated_routes[: self.settings.elitism_size]

        for elite_route in elite_routes:
            new_population.append(elite_route.ordered_points)

        while len(new_population) < self.settings.population_size:
            parent1, parent2 = select_parents(evaluated_routes)

            child = order_crossover(parent1, parent2)

            child = mutate(
                route_points=child,
                mutation_probability=self.settings.mutation_probability,
            )

            new_population.append(child)

        return new_population