import csv
from dataclasses import replace
from pathlib import Path

from womens_health_route_optimizer.config import settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.optimization.optimizer import RouteOptimizer


OUTPUT_DIR = Path("experiments/outputs")
OUTPUT_FILE = OUTPUT_DIR / "experiments_results.csv"


EXPERIMENTS = [
    {
        "experiment_name": "baseline_small",
        "population_size": 50,
        "generations": 80,
        "mutation_probability": 0.20,
        "elitism_size": 1,
        "random_seed": 42,
    },
    {
        "experiment_name": "baseline_medium",
        "population_size": 100,
        "generations": 150,
        "mutation_probability": 0.20,
        "elitism_size": 1,
        "random_seed": 42,
    },
    {
        "experiment_name": "large_population",
        "population_size": 150,
        "generations": 200,
        "mutation_probability": 0.20,
        "elitism_size": 1,
        "random_seed": 42,
    },
    {
        "experiment_name": "high_mutation",
        "population_size": 100,
        "generations": 150,
        "mutation_probability": 0.35,
        "elitism_size": 1,
        "random_seed": 42,
    },
    {
        "experiment_name": "low_mutation",
        "population_size": 100,
        "generations": 150,
        "mutation_probability": 0.10,
        "elitism_size": 1,
        "random_seed": 42,
    },
    {
        "experiment_name": "higher_elitism",
        "population_size": 100,
        "generations": 150,
        "mutation_probability": 0.20,
        "elitism_size": 3,
        "random_seed": 42,
    },
    {
        "experiment_name": "no_fixed_seed",
        "population_size": 100,
        "generations": 150,
        "mutation_probability": 0.20,
        "elitism_size": 1,
        "random_seed": None,
    },
]


def summarize_vehicle_routes(solution) -> str:
    """
    Cria um resumo textual compacto das rotas por veículo.

    Exemplo:
    V001: P004>P001>P005 | V002: P003>P011>P012
    """
    route_summaries = []

    for vehicle_route in solution.vehicle_routes:
        points_sequence = ">".join(
            point.id for point in vehicle_route.ordered_points
        )

        route_summaries.append(
            f"{vehicle_route.vehicle.id}: {points_sequence}"
        )

    return " | ".join(route_summaries)


def get_longest_vehicle_route(solution):
    """
    Retorna a rota do veículo com maior duração.
    """
    return max(
        solution.vehicle_routes,
        key=lambda vehicle_route: vehicle_route.total_duration_minutes,
    )


def run_experiment(experiment_config: dict) -> dict:
    """
    Executa um experimento do algoritmo genético com frota heterogênea.
    """
    center = load_distribution_center()
    points = load_attendance_points()

    experiment_settings = replace(
        settings,
        population_size=experiment_config["population_size"],
        generations=experiment_config["generations"],
        mutation_probability=experiment_config["mutation_probability"],
        elitism_size=experiment_config["elitism_size"],
        random_seed=experiment_config["random_seed"],
    )

    optimizer = RouteOptimizer(
        distribution_center=center,
        attendance_points=points,
        app_settings=experiment_settings,
    )

    result = optimizer.optimize()
    solution = result.best_solution

    longest_vehicle_route = get_longest_vehicle_route(solution)

    return {
        "experiment_name": experiment_config["experiment_name"],
        "population_size": experiment_settings.population_size,
        "generations": experiment_settings.generations,
        "mutation_probability": experiment_settings.mutation_probability,
        "elitism_size": experiment_settings.elitism_size,
        "random_seed": experiment_settings.random_seed,
        "fitness": round(solution.fitness, 4),
        "initial_fitness": round(result.fitness_history[0], 4),
        "fitness_improvement": round(
            result.fitness_history[0] - solution.fitness,
            4,
        ),
        "total_distance_km": round(solution.total_distance_km, 4),
        "total_duration_minutes": round(
            solution.total_duration_minutes,
            4,
        ),
        "priority_penalty": round(solution.priority_penalty, 4),
        "time_window_penalty": round(solution.time_window_penalty, 4),
        "capacity_penalty": round(solution.capacity_penalty, 4),
        "hormonal_transport_penalty": round(
            solution.hormonal_transport_penalty,
            4,
        ),
        "route_duration_penalty": round(
            solution.route_duration_penalty,
            4,
        ),
        "vehicle_compatibility_penalty": round(
            solution.vehicle_compatibility_penalty,
            4,
        ),
        "total_supply_demand": solution.total_supply_demand,
        "vehicles_count": len(solution.vehicle_routes),
        "longest_vehicle_id": longest_vehicle_route.vehicle.id,
        "longest_vehicle_name": longest_vehicle_route.vehicle.name,
        "longest_vehicle_duration_minutes": round(
            longest_vehicle_route.total_duration_minutes,
            4,
        ),
        "vehicle_routes": summarize_vehicle_routes(solution),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for experiment_config in EXPERIMENTS:
        experiment_name = experiment_config["experiment_name"]

        print(f"Executando experimento: {experiment_name}")

        result = run_experiment(experiment_config)
        results.append(result)

        print(
            f"  Fitness: {result['fitness']} | "
            f"Distância: {result['total_distance_km']} km | "
            f"Duração: {result['total_duration_minutes']} min | "
            f"Janela: {result['time_window_penalty']} | "
            f"Capacidade: {result['capacity_penalty']} | "
            f"Hormonal: {result['hormonal_transport_penalty']} | "
            f"Compatibilidade: {result['vehicle_compatibility_penalty']}"
        )

    fieldnames = [
        "experiment_name",
        "population_size",
        "generations",
        "mutation_probability",
        "elitism_size",
        "random_seed",
        "fitness",
        "initial_fitness",
        "fitness_improvement",
        "total_distance_km",
        "total_duration_minutes",
        "priority_penalty",
        "time_window_penalty",
        "capacity_penalty",
        "hormonal_transport_penalty",
        "route_duration_penalty",
        "vehicle_compatibility_penalty",
        "total_supply_demand",
        "vehicles_count",
        "longest_vehicle_id",
        "longest_vehicle_name",
        "longest_vehicle_duration_minutes",
        "vehicle_routes",
    ]

    with OUTPUT_FILE.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Resultados salvos em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()