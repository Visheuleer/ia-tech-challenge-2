from pathlib import Path

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    AttendanceType,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization import simulate_route


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_prompt_template(template_name: str) -> str:
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {template_path}"
        )

    return template_path.read_text(encoding="utf-8")


def build_route_context(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:

    simulation = simulate_route(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    route_duration_excess = max(
        0.0,
        route.total_duration_minutes
        - app_settings.max_route_duration_minutes,
    )

    lines: list[str] = ["DADOS DA ROTA OTIMIZADA", "", f"Central de distribuição: {distribution_center.name}",
                        f"Horário de saída: {app_settings.route_start_time}", f"Horário estimado de retorno: "
                                                                              f"{simulation.return_time.strftime('%H:%M')}",
                        f"Duração total da rota: "
                        f"{route.total_duration_minutes:.1f} minutos", f"Duração máxima permitida: "
                                                                       f"{app_settings.max_route_duration_minutes} minutos",
                        f"Excesso de duração: {route_duration_excess:.1f} minutos",
                        f"Distância total: {route.total_distance_km:.2f} km", f"Distância do retorno à central: "
                                                                              f"{simulation.return_leg_distance_km:.2f} km",
                        f"Fitness final: {route.fitness:.2f}", "", "PENALIDADES", "",
                        f"Prioridade: {route.priority_penalty:.2f}",
                        f"Janela de horário: {route.time_window_penalty:.2f}",
                        f"Capacidade: {route.capacity_penalty:.2f}", f"Prazo de medicamentos hormonais: "
                                                                     f"{route.hormonal_transport_penalty:.2f}",
                        f"Duração máxima da rota: "
                        f"{route.route_duration_penalty:.2f}", "", f"Demanda total de suprimentos: "
                                                                   f"{route.total_supply_demand}",
                        f"Capacidade máxima do veículo: "
                        f"{app_settings.vehicle_capacity}", f"Prazo máximo para medicamentos hormonais: "
                                                            f"{app_settings.max_hormonal_transport_minutes} minutos",
                        "", "SEQUÊNCIA DE ATENDIMENTOS", ""]

    for stop in simulation.stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[
            point.attendance_type
        ]

        status_parts: list[str] = []

        if stop.waiting_minutes > 0:
            status_parts.append(
                f"espera de {stop.waiting_minutes:.1f} minutos"
            )

        if stop.delay_minutes > 0:
            status_parts.append(
                f"atraso de {stop.delay_minutes:.1f} minutos"
            )

        if not status_parts:
            status_parts.append("sem espera ou atraso")

        if (
            point.attendance_type
            is AttendanceType.HORMONAL_MEDICATION
        ):
            hormonal_excess = max(
                0.0,
                stop.elapsed_minutes_from_departure
                - app_settings.max_hormonal_transport_minutes,
            )

            if hormonal_excess > 0:
                hormonal_status = (
                    f"prazo de transporte excedido em "
                    f"{hormonal_excess:.1f} minutos"
                )
            else:
                hormonal_status = (
                    "entrega dentro do prazo máximo de transporte"
                )
        else:
            hormonal_status = "restrição hormonal não aplicável"

        status = "; ".join(status_parts)

        lines.append(
            f"{stop.sequence:02d}. {point.id} - {point.name}\n"
            f"    Tipo: {attendance_label}\n"
            f"    Prioridade: {point.priority}\n"
            f"    Demanda de suprimentos: {point.supply_demand}\n"
            f"    Chegada estimada: "
            f"{stop.estimated_arrival_time.strftime('%H:%M')}\n"
            f"    Início do atendimento: "
            f"{stop.service_start_time.strftime('%H:%M')}\n"
            f"    Janela de horário: "
            f"{stop.time_window_start.strftime('%H:%M')} - "
            f"{stop.time_window_end.strftime('%H:%M')}\n"
            f"    Distância do trecho anterior: "
            f"{stop.leg_distance_km:.2f} km\n"
            f"    Tempo desde a saída da central: "
            f"{stop.elapsed_minutes_from_departure:.1f} minutos\n"
            f"    Status operacional: {status}\n"
            f"    Status do prazo hormonal: {hormonal_status}\n"
            f"    Observação: {point.notes}\n"
        )

    return "\n".join(lines)


def build_instruction_manual_prompt(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("instruction_manual.md")

    route_context = build_route_context(
        route=route,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(route_context=route_context)


def build_visit_plan_prompt(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("visit_plan.md")

    route_context = build_route_context(
        route=route,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(route_context=route_context)


def build_question_prompt(
    route: Route,
    distribution_center: DistributionCenter,
    question: str,
    app_settings: Settings = settings,
) -> str:
    template = load_prompt_template("route_question.md")

    route_context = build_route_context(
        route=route,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    return template.format(
        question=question,
        route_context=route_context,
    )