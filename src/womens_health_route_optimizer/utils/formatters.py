from dataclasses import replace

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    AttendanceType,
    DistributionCenter,
    FleetSolution,
)
from womens_health_route_optimizer.optimization.simulation import simulate_route


def format_duration(total_minutes: float) -> str:
    rounded_minutes = round(total_minutes)
    hours, minutes = divmod(rounded_minutes, 60)

    if hours == 0:
        return f"{minutes} min"

    return f"{hours}h {minutes:02d}min"


def format_fleet_summary(
    solution: FleetSolution,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> str:

    lines: list[str] = ["RESUMO DA SOLUÇÃO COM FROTA HETEROGÊNEA", "",
                        f"Central de distribuição: {distribution_center.name}",
                        f"Horário de saída: {app_settings.route_start_time}",
                        f"Quantidade de veículos: {len(solution.vehicle_routes)}",
                        f"Fitness final: {solution.fitness:.2f}",
                        f"Distância total da frota: {solution.total_distance_km:.2f} km",
                        f"Duração operacional da frota: "
                        f"{solution.total_duration_minutes:.1f} min", f"Limite máximo de duração por rota: "
                                                                      f"{app_settings.max_route_duration_minutes} min",
                        f"Demanda total: {solution.total_supply_demand}", "", "PENALIDADES",
                        f"- Prioridade: {solution.priority_penalty:.2f}",
                        f"- Janela de horário: {solution.time_window_penalty:.2f}",
                        f"- Capacidade: {solution.capacity_penalty:.2f}",
                        f"- Prazo hormonal: {solution.hormonal_transport_penalty:.2f}",
                        f"- Duração máxima: {solution.route_duration_penalty:.2f}", "- Compatibilidade veículo/carga: "
                                                                                    f"{solution.vehicle_compatibility_penalty:.2f}",
                        ""]

    if solution.time_window_penalty == 0:
        lines.append("Status das janelas: todas as paradas ficaram dentro das janelas.")
    else:
        lines.append("Status das janelas: há atrasos em uma ou mais paradas.")

    if solution.capacity_penalty == 0:
        lines.append("Status da capacidade: todos os veículos respeitaram sua capacidade.")
    else:
        lines.append("Status da capacidade: há veículo com capacidade excedida.")

    if solution.hormonal_transport_penalty == 0:
        lines.append(
            "Status hormonal: todas as entregas hormonais ficaram dentro do prazo."
        )
    else:
        lines.append(
            "Status hormonal: há entregas hormonais fora do prazo máximo."
        )

    if solution.route_duration_penalty == 0:
        lines.append(
            "Status da duração: todas as rotas respeitaram o limite operacional."
        )
    else:
        lines.append(
            "Status da duração: há rota acima do limite operacional."
        )

    if solution.vehicle_compatibility_penalty == 0:
        lines.append(
            "Status de compatibilidade: medicamentos hormonais foram atribuídos "
            "a veículos compatíveis."
        )
    else:
        lines.append(
            "Status de compatibilidade: há medicamento hormonal em veículo não refrigerado."
        )

    lines.append("")
    lines.append("ROTAS POR VEÍCULO")

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
        lines.append(f"{vehicle_route.vehicle.id} - {vehicle_route.vehicle.name}")
        lines.append(
            f"- Refrigerado: "
            f"{'Sim' if vehicle_route.vehicle.is_refrigerated else 'Não'}"
        )
        lines.append(
            f"- Capacidade: "
            f"{vehicle_route.total_supply_demand}/"
            f"{vehicle_route.vehicle.max_supply_capacity}"
        )
        lines.append(f"- Distância: {vehicle_route.total_distance_km:.2f} km")
        lines.append(f"- Duração: {vehicle_route.total_duration_minutes:.1f} min")
        lines.append(f"- Retorno estimado: {simulation.return_time.strftime('%H:%M')}")
        lines.append(f"- Fitness da rota: {vehicle_route.fitness:.2f}")
        lines.append("- Sequência:")

        for stop in simulation.stops:
            point = stop.point

            if stop.delay_minutes > 0:
                status = f"Atraso de {stop.delay_minutes:.1f} min"
            elif stop.waiting_minutes > 0:
                status = f"Espera de {stop.waiting_minutes:.1f} min"
            else:
                status = "No prazo"

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
                "  "
                f"{stop.sequence}. {point.id} - {point.name} | "
                f"{ATTENDANCE_TYPE_LABELS[point.attendance_type]} | "
                f"Prioridade {point.priority} | "
                f"Chegada {stop.estimated_arrival_time.strftime('%H:%M')} | "
                f"Início {stop.service_start_time.strftime('%H:%M')} | "
                f"Janela {stop.time_window_start.strftime('%H:%M')}-"
                f"{stop.time_window_end.strftime('%H:%M')} | "
                f"{status} | "
                f"Demanda {point.supply_demand} | "
                f"Hormonal: {hormonal_status}"
            )

    return "\n".join(lines)