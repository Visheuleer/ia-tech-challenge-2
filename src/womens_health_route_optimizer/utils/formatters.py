from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    AttendanceType,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization.simulation import simulate_route


def format_duration(total_minutes: float) -> str:
    rounded_minutes = round(total_minutes)
    hours, minutes = divmod(rounded_minutes, 60)

    if hours == 0:
        return f"{minutes} min"

    return f"{hours}h {minutes:02d}min"


def format_route_summary(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:

    simulation = simulate_route(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    lines: list[str] = ["Resumo da rota otimizada", "=" * 60, f"Distância total: {route.total_distance_km:.2f} km",
                        f"Duração total: {format_duration(route.total_duration_minutes)}", f"Limite de duração: "
                                                                                           f"{format_duration(app_settings.max_route_duration_minutes)}",
                        f"Horário estimado de retorno: "
                        f"{simulation.return_time.strftime('%H:%M')}", f"Distância do retorno à central: "
                                                                       f"{simulation.return_leg_distance_km:.2f} km",
                        "", "Penalidades", "-" * 60, f"Prioridade: {route.priority_penalty:.2f}",
                        f"Janela de horário: {route.time_window_penalty:.2f}",
                        f"Capacidade: {route.capacity_penalty:.2f}", f"Prazo de medicamentos hormonais: "
                                                                     f"{route.hormonal_transport_penalty:.2f}",
                        f"Duração máxima da rota: "
                        f"{route.route_duration_penalty:.2f}", f"Fitness final: {route.fitness:.2f}", "",
                        f"Demanda total de suprimentos: {route.total_supply_demand}",
                        f"Capacidade do veículo: {app_settings.vehicle_capacity}",
                        f"Prazo máximo para medicamentos hormonais: "
                        f"{app_settings.max_hormonal_transport_minutes} min", "", "Ordem dos atendimentos", "-" * 60]

    for stop in simulation.stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[
            point.attendance_type
        ]

        status_parts: list[str] = []

        if stop.waiting_minutes > 0:
            status_parts.append(
                f"Espera {stop.waiting_minutes:.1f} min"
            )

        if stop.delay_minutes > 0:
            status_parts.append(
                f"Atraso {stop.delay_minutes:.1f} min"
            )

        if not status_parts:
            status_parts.append("Sem espera/atraso")

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
                    f"Prazo hormonal excedido em "
                    f"{hormonal_excess:.1f} min"
                )
            else:
                hormonal_status = "Medicamento dentro do prazo"
        else:
            hormonal_status = "Prazo hormonal não se aplica"

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
            f"Tempo desde saída "
            f"{stop.elapsed_minutes_from_departure:.1f} min | "
            f"{status_text} | "
            f"{hormonal_status}"
        )

    return "\n".join(lines)