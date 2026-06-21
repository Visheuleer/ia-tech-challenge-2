from dataclasses import replace
from pathlib import Path

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import ATTENDANCE_TYPE_LABELS
from womens_health_route_optimizer.domain.enums import AttendanceType
from womens_health_route_optimizer.domain.models import (
    DistributionCenter,
    FleetSolution,
)
from womens_health_route_optimizer.optimization.simulation import simulate_route


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_prompt_template(template_name: str) -> str:
    template_path = TEMPLATES_DIR / template_name
    return template_path.read_text(encoding="utf-8")


def build_fleet_route_context(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:

    lines: list[str] = ["## Resumo geral da frota", f"Central de distribuição: {distribution_center.name}",
                        f"Horário de saída: {app_settings.route_start_time}",
                        f"Fitness final da solução: {solution.fitness:.2f}",
                        f"Distância total da frota: {solution.total_distance_km:.2f} km",
                        "Duração operacional da frota: "
                        f"{solution.total_duration_minutes:.1f} min", "Limite máximo de duração por rota: "
                                                                      f"{app_settings.max_route_duration_minutes} min",
                        "Duração máxima respeitada: "
                        f"{'Sim' if solution.route_duration_penalty == 0 else 'Não'}",
                        f"Demanda total: {solution.total_supply_demand}",
                        f"Quantidade de veículos: {len(solution.vehicle_routes)}",
                        f"Penalidade de prioridade: {solution.priority_penalty:.2f}",
                        f"Penalidade de janela de horário: {solution.time_window_penalty:.2f}",
                        f"Penalidade de capacidade: {solution.capacity_penalty:.2f}", "Penalidade de prazo hormonal: "
                                                                                      f"{solution.hormonal_transport_penalty:.2f}",
                        "Penalidade de duração máxima: "
                        f"{solution.route_duration_penalty:.2f}", "Penalidade de compatibilidade veículo/carga: "
                                                                  f"{solution.vehicle_compatibility_penalty:.2f}"]

    delayed_stops_count = 0
    hormonal_out_of_deadline_count = 0

    for vehicle_route in solution.vehicle_routes:
        route_settings = replace(
            app_settings,
            average_vehicle_speed_kmh=(
                vehicle_route.vehicle.average_speed_kmh
                if vehicle_route.vehicle.average_speed_kmh is not None
                else app_settings.average_vehicle_speed_kmh
            ),
            vehicle_capacity=vehicle_route.vehicle.max_supply_capacity,
        )

        simulation = simulate_route(
            route_points=vehicle_route.ordered_points,
            distribution_center=distribution_center,
            app_settings=route_settings,
        )

        delayed_stops_count += sum(
            1
            for stop in simulation.stops
            if stop.delay_minutes > 0
        )

        hormonal_out_of_deadline_count += sum(
            1
            for stop in simulation.stops
            if (
                stop.point.attendance_type
                == AttendanceType.HORMONAL_MEDICATION
                and stop.elapsed_minutes_from_departure
                > app_settings.max_hormonal_transport_minutes
            )
        )

    lines.append(
        f"Quantidade de paradas com atraso: {delayed_stops_count}"
    )
    lines.append(
        "Quantidade de entregas hormonais fora do prazo: "
        f"{hormonal_out_of_deadline_count}"
    )

    lines.append("")
    lines.append("## Rotas por veículo")

    for vehicle_route in solution.vehicle_routes:
        route_settings = replace(
            app_settings,
            average_vehicle_speed_kmh=(
                vehicle_route.vehicle.average_speed_kmh
                if vehicle_route.vehicle.average_speed_kmh is not None
                else app_settings.average_vehicle_speed_kmh
            ),
            vehicle_capacity=vehicle_route.vehicle.max_supply_capacity,
        )

        simulation = simulate_route(
            route_points=vehicle_route.ordered_points,
            distribution_center=distribution_center,
            app_settings=route_settings,
        )

        lines.append("")
        lines.append(
            f"### {vehicle_route.vehicle.id} - {vehicle_route.vehicle.name}"
        )
        lines.append(
            f"Veículo refrigerado: "
            f"{'Sim' if vehicle_route.vehicle.is_refrigerated else 'Não'}"
        )
        lines.append(
            f"Capacidade: {vehicle_route.vehicle.max_supply_capacity}"
        )
        lines.append(
            f"Demanda atribuída: {vehicle_route.total_supply_demand}"
        )
        lines.append(
            f"Distância da rota: {vehicle_route.total_distance_km:.2f} km"
        )
        lines.append(
            f"Duração da rota: {vehicle_route.total_duration_minutes:.1f} min"
        )
        lines.append(
            f"Horário estimado de retorno: "
            f"{simulation.return_time.strftime('%H:%M')}"
        )
        lines.append(
            f"Penalidade de janela: {vehicle_route.time_window_penalty:.2f}"
        )
        lines.append(
            f"Penalidade de capacidade: {vehicle_route.capacity_penalty:.2f}"
        )
        lines.append(
            "Penalidade de prazo hormonal: "
            f"{vehicle_route.hormonal_transport_penalty:.2f}"
        )
        lines.append(
            "Penalidade de compatibilidade: "
            f"{vehicle_route.vehicle_compatibility_penalty:.2f}"
        )

        lines.append("")
        lines.append("Paradas:")

        for stop in simulation.stops:
            point = stop.point

            if stop.delay_minutes > 0:
                operational_status = (
                    f"Atraso de {stop.delay_minutes:.1f} min"
                )
            elif stop.waiting_minutes > 0:
                operational_status = (
                    f"Espera de {stop.waiting_minutes:.1f} min"
                )
            else:
                operational_status = "No prazo"

            if point.attendance_type == AttendanceType.HORMONAL_MEDICATION:
                if (
                    stop.elapsed_minutes_from_departure
                    <= app_settings.max_hormonal_transport_minutes
                ):
                    hormonal_status = "Dentro do prazo"
                else:
                    excess = (
                        stop.elapsed_minutes_from_departure
                        - app_settings.max_hormonal_transport_minutes
                    )
                    hormonal_status = f"Fora do prazo ({excess:.1f} min)"
            else:
                hormonal_status = "Não se aplica"

            lines.append(
                "- "
                f"Ordem: {stop.sequence} | "
                f"Código: {point.id} | "
                f"Local: {point.name} | "
                f"Tipo: {ATTENDANCE_TYPE_LABELS[point.attendance_type]} | "
                f"Prioridade: {point.priority} | "
                f"Chegada: {stop.estimated_arrival_time.strftime('%H:%M')} | "
                f"Início: {stop.service_start_time.strftime('%H:%M')} | "
                f"Janela: {stop.time_window_start.strftime('%H:%M')} - "
                f"{stop.time_window_end.strftime('%H:%M')} | "
                f"Status: {operational_status} | "
                f"Tempo desde saída: "
                f"{stop.elapsed_minutes_from_departure:.1f} min | "
                f"Demanda: {point.supply_demand} | "
                f"Status do prazo hormonal: {hormonal_status}"
            )

    return "\n".join(lines)


def build_instruction_manual_prompt(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("instruction_manual.md")

    route_context = build_fleet_route_context(
        solution=solution,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(route_context=route_context)


def build_visit_plan_prompt(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("visit_plan.md")

    route_context = build_fleet_route_context(
        solution=solution,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(route_context=route_context)


def build_route_question_prompt(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    question: str,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("route_question.md")

    route_context = build_fleet_route_context(
        solution=solution,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(
        question=question,
        route_context=route_context,
    )