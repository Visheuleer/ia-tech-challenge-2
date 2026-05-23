from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization.simulation import simulate_route_stops


def format_route_summary(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:
    """
    Gera um resumo textual simples da rota otimizada.
    """

    stops = simulate_route_stops(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    lines: list[str] = []

    lines.append("Resumo da rota otimizada")
    lines.append("=" * 40)
    lines.append(f"Distância total: {route.total_distance_km:.2f} km")
    lines.append(f"Penalidade de prioridade: {route.priority_penalty:.2f}")
    lines.append(f"Penalidade de janela de horário: {route.time_window_penalty:.2f}")
    lines.append(f"Penalidade de capacidade: {route.capacity_penalty:.2f}")
    lines.append(f"Fitness final: {route.fitness:.2f}")
    lines.append(f"Demanda total de suprimentos: {route.total_supply_demand}")
    lines.append("")
    lines.append("Ordem dos atendimentos:")
    lines.append("-" * 40)

    for stop in stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[point.attendance_type]

        status_parts: list[str] = []

        if stop.waiting_minutes > 0:
            status_parts.append(f"Espera {stop.waiting_minutes:.1f} min")

        if stop.delay_minutes > 0:
            status_parts.append(f"Atraso {stop.delay_minutes:.1f} min")

        if not status_parts:
            status_parts.append("Sem espera/atraso")

        status_text = " | ".join(status_parts)

        lines.append(
            f"{stop.sequence:02d}. {point.id} - {point.name} | "
            f"{attendance_label} | "
            f"Prioridade {point.priority} | "
            f"Demanda {point.supply_demand} | "
            f"Chegada {stop.estimated_arrival_time.strftime('%H:%M')} | "
            f"Início {stop.service_start_time.strftime('%H:%M')} | "
            f"Janela {stop.time_window_start.strftime('%H:%M')}"
            f"-{stop.time_window_end.strftime('%H:%M')} | "
            f"Trecho {stop.leg_distance_km:.2f} km | "
            f"{status_text}"
        )

    return "\n".join(lines)