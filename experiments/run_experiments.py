import csv
import time
from pathlib import Path

from womens_health_route_optimizer.config import Settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import Vehicle
from womens_health_route_optimizer.optimization import RouteOptimizer


OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "experiments_results.csv"


EXPERIMENTS = [
    {
        "name": "baseline_small",
        "population_size": 50,
        "generations": 100,
        "mutation_probability": 0.10,
        "random_seed": 42,
    },
    {
        "name": "baseline_medium",
        "population_size": 100,
        "generations": 200,
        "mutation_probability": 0.20,
        "random_seed": 42,
    },
    {
        "name": "large_population",
        "population_size": 200,
        "generations": 300,
        "mutation_probability": 0.20,
        "random_seed": 42,
    },
    {
        "name": "high_mutation",
        "population_size": 100,
        "generations": 200,
        "mutation_probability": 0.40,
        "random_seed": 42,
    },
    {
        "name": "no_fixed_seed",
        "population_size": 100,
        "generations": 200,
        "mutation_probability": 0.20,
        "random_seed": None,
    },
]


def run_experiment(experiment_config: dict) -> dict:
    center = load_distribution_center()
    points = load_attendance_points()

    settings = Settings(
        population_size=experiment_config["population_size"],
        generations=experiment_config["generations"],
        mutation_probability=experiment_config["mutation_probability"],
        elitism_size=1,
        random_seed=experiment_config["random_seed"],
        vehicle_capacity=20,
        average_vehicle_speed_kmh=35.0,
        route_start_time="08:00",
        priority_penalty_weight=1000.0,
        time_window_penalty_weight=500.0,
        capacity_penalty_weight=2000.0,
        ollama_base_url="https://ollama.com",
        ollama_model="gpt-oss:20b",
        ollama_api_key=None,
        llm_temperature=0.2,
    )

    vehicle = Vehicle(
        id="V001",
        name="Veículo experimental",
        max_supply_capacity=settings.vehicle_capacity,
    )

    optimizer = RouteOptimizer(
        distribution_center=center,
        attendance_points=points,
        vehicle=vehicle,
        app_settings=settings,
    )

    start_time = time.perf_counter()
    result = optimizer.optimize()
    elapsed_seconds = time.perf_counter() - start_time

    best_route = result.best_route

    return {
        "experiment": experiment_config["name"],
        "population_size": settings.population_size,
        "generations": settings.generations,
        "mutation_probability": settings.mutation_probability,
        "random_seed": settings.random_seed,
        "elapsed_seconds": round(elapsed_seconds, 4),
        "best_fitness": round(best_route.fitness, 4),
        "total_distance_km": round(best_route.total_distance_km, 4),
        "priority_penalty": round(best_route.priority_penalty, 4),
        "time_window_penalty": round(best_route.time_window_penalty, 4),
        "capacity_penalty": round(best_route.capacity_penalty, 4),
        "total_supply_demand": best_route.total_supply_demand,
        "first_stop_id": best_route.ordered_points[0].id,
        "first_stop_type": best_route.ordered_points[0].attendance_type.value,
    }


def save_results(results: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "experiment",
        "population_size",
        "generations",
        "mutation_probability",
        "random_seed",
        "elapsed_seconds",
        "best_fitness",
        "total_distance_km",
        "priority_penalty",
        "time_window_penalty",
        "capacity_penalty",
        "total_supply_demand",
        "first_stop_id",
        "first_stop_type",
    ]

    with OUTPUT_FILE.open(mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    results = []

    for experiment_config in EXPERIMENTS:
        print(f"Running experiment: {experiment_config['name']}")

        result = run_experiment(experiment_config)
        results.append(result)

        print(
            f"  fitness={result['best_fitness']} | "
            f"distance={result['total_distance_km']} km | "
            f"time={result['elapsed_seconds']}s"
        )

    save_results(results)

    print()
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()