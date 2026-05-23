from pathlib import Path

from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization import simulate_route_stops


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_prompt_template(template_name: str) -> str:
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def build_route_context(
    route: Route,
    distribution_center: DistributionCenter,
) -> str:

    stops = simulate_route_stops(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
    )

    lines: list[str] = ["DADOS DA ROTA OTIMIZADA", "", f"Central de distribuição: {distribution_center.name}",
                        f"Distância total: {route.total_distance_km:.2f} km", f"Fitness final: {route.fitness:.2f}",
                        f"Penalidade de prioridade: {route.priority_penalty:.2f}",
                        f"Penalidade de janela de horário: {route.time_window_penalty:.2f}",
                        f"Penalidade de capacidade: {route.capacity_penalty:.2f}",
                        f"Demanda total de suprimentos: {route.total_supply_demand}", "", "SEQUÊNCIA DE ATENDIMENTOS",
                        ""]

    for stop in stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[point.attendance_type]

        status_parts: list[str] = []

        if stop.waiting_minutes > 0:
            status_parts.append(f"espera de {stop.waiting_minutes:.1f} minutos")

        if stop.delay_minutes > 0:
            status_parts.append(f"atraso de {stop.delay_minutes:.1f} minutos")

        if not status_parts:
            status_parts.append("sem espera ou atraso")

        status = "; ".join(status_parts)

        lines.append(
            f"{stop.sequence:02d}. {point.id} - {point.name}\n"
            f"    Tipo: {attendance_label}\n"
            f"    Prioridade: {point.priority}\n"
            f"    Demanda de suprimentos: {point.supply_demand}\n"
            f"    Chegada estimada: {stop.estimated_arrival_time.strftime('%H:%M')}\n"
            f"    Início do atendimento: {stop.service_start_time.strftime('%H:%M')}\n"
            f"    Janela de horário: "
            f"{stop.time_window_start.strftime('%H:%M')} - "
            f"{stop.time_window_end.strftime('%H:%M')}\n"
            f"    Distância do trecho anterior: {stop.leg_distance_km:.2f} km\n"
            f"    Status: {status}\n"
            f"    Observação: {point.notes}\n"
        )

    return "\n".join(lines)


def build_instruction_manual_prompt(
    route: Route,
    distribution_center: DistributionCenter,
) -> str:
    template = load_prompt_template("instruction_manual.md")
    route_context = build_route_context(route, distribution_center)

    return template.format(route_context=route_context)


def build_visit_plan_prompt(
    route: Route,
    distribution_center: DistributionCenter,
) -> str:
    template = load_prompt_template("visit_plan.md")
    route_context = build_route_context(route, distribution_center)

    return template.format(route_context=route_context)


def build_question_prompt(
    route: Route,
    distribution_center: DistributionCenter,
    question: str,
) -> str:
    template = load_prompt_template("route_question.md")
    route_context = build_route_context(route, distribution_center)

    return template.format(
        question=question,
        route_context=route_context,
    )