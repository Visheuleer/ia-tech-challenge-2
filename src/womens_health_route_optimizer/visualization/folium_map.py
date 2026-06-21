from dataclasses import replace

import folium
from folium import DivIcon

from womens_health_route_optimizer.domain import ATTENDANCE_TYPE_LABELS
from womens_health_route_optimizer.domain.enums import AttendanceType
from womens_health_route_optimizer.optimization.simulation import simulate_route


def get_priority_color(priority: int) -> str:
    priority_colors = {
        1: "#E53935",
        2: "#FB8C00",
        3: "#1E88E5",
        4: "#43A047",
    }
    return priority_colors.get(priority, "#757575")


def build_stop_icon(
    order: int,
    vehicle_color: str,
    priority: int,
) -> DivIcon:

    priority_color = get_priority_color(priority)

    html = f"""
    <div style="position: relative; width: 34px; height: 34px;">
        <div style="
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: {vehicle_color};
            color: white;
            font-weight: bold;
            text-align: center;
            line-height: 34px;
            font-size: 14px;
            border: 2px solid white;
            box-shadow: 0 0 6px rgba(0,0,0,0.35);
        ">
            {order}
        </div>

        <div style="
            position: absolute;
            top: -8px;
            right: -8px;
            min-width: 22px;
            height: 22px;
            padding: 0 4px;
            border-radius: 11px;
            background: {priority_color};
            color: white;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
            line-height: 22px;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.25);
        ">
            P{priority}
        </div>
    </div>
    """

    return DivIcon(
        html=html,
        icon_size=(34, 34),
        icon_anchor=(17, 17),
    )


def build_map_legend(vehicle_color_map: dict[str, tuple[str, str]]) -> str:
    vehicle_items = ""

    for vehicle_id, (vehicle_name, vehicle_color) in vehicle_color_map.items():
        vehicle_items += f"""
        <div class="fleet-legend-row">
            <span class="fleet-legend-dot" style="background-color: {vehicle_color} !important;"></span>
            <span class="fleet-legend-text">
                <strong>{vehicle_id}</strong> - {vehicle_name}
            </span>
        </div>
        """

    legend_html = f"""
    <style>
        #fleet-map-legend {{
            position: fixed !important;
            top: 24px !important;
            right: 24px !important;
            z-index: 999999 !important;
            background-color: #ffffff !important;
            border: 1px solid #d1d5db !important;
            border-radius: 12px !important;
            padding: 14px 16px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28) !important;
            min-width: 280px !important;
            max-width: 320px !important;
            font-family: Arial, sans-serif !important;
            opacity: 1 !important;
            color: #111827 !important;
        }}

        #fleet-map-legend,
        #fleet-map-legend div,
        #fleet-map-legend span,
        #fleet-map-legend strong {{
            color: #111827 !important;
            opacity: 1 !important;
            text-shadow: none !important;
            filter: none !important;
        }}

        #fleet-map-legend .fleet-legend-title {{
            font-size: 15px !important;
            font-weight: 800 !important;
            margin-bottom: 10px !important;
            color: #111827 !important;
        }}

        #fleet-map-legend .fleet-legend-section-title {{
            font-size: 13px !important;
            font-weight: 800 !important;
            margin-bottom: 8px !important;
            color: #374151 !important;
        }}

        #fleet-map-legend .fleet-legend-row {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 8px !important;
            font-size: 13px !important;
            line-height: 1.25 !important;
        }}

        #fleet-map-legend .fleet-legend-dot {{
            display: inline-block !important;
            width: 14px !important;
            height: 14px !important;
            min-width: 14px !important;
            border-radius: 50% !important;
            border: 1px solid rgba(0, 0, 0, 0.25) !important;
        }}

        #fleet-map-legend .fleet-legend-divider {{
            border-top: 1px solid #e5e7eb !important;
            margin: 12px 0 !important;
        }}

        #fleet-map-legend .priority-row {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 7px !important;
            font-size: 13px !important;
            line-height: 1.25 !important;
        }}

        #fleet-map-legend .priority-badge {{
            color: #ffffff !important;
            padding: 3px 8px !important;
            border-radius: 999px !important;
            font-weight: 800 !important;
            min-width: 28px !important;
            text-align: center !important;
            display: inline-block !important;
        }}

        #fleet-map-legend .priority-label {{
            color: #111827 !important;
            font-weight: 500 !important;
        }}
    </style>

    <div id="fleet-map-legend">
        <div class="fleet-legend-title">
            Legenda do mapa
        </div>

        <div class="fleet-legend-section-title">
            Veículos
        </div>

        {vehicle_items}

        <div class="fleet-legend-divider"></div>

        <div class="fleet-legend-section-title">
            Prioridade
        </div>

        <div class="priority-row">
            <span class="priority-badge" style="background-color: #E53935 !important;">P1</span>
            <span class="priority-label">Emergência obstétrica</span>
        </div>

        <div class="priority-row">
            <span class="priority-badge" style="background-color: #FB8C00 !important;">P2</span>
            <span class="priority-label">Violência doméstica</span>
        </div>

        <div class="priority-row">
            <span class="priority-badge" style="background-color: #1E88E5 !important;">P3</span>
            <span class="priority-label">Medicamento hormonal</span>
        </div>

        <div class="priority-row">
            <span class="priority-badge" style="background-color: #43A047 !important;">P4</span>
            <span class="priority-label">Atendimento pós-parto</span>
        </div>
    </div>
    """

    return legend_html

def create_fleet_map(
    solution,
    distribution_center,
    app_settings,
):
    center_location = [
        distribution_center.coordinate.latitude,
        distribution_center.coordinate.longitude,
    ]

    route_map = folium.Map(
        location=center_location,
        zoom_start=11,
        control_scale=True,
    )

    vehicle_colors = [
        "#1E88E5",
        "#8E24AA",
        "#43A047",
        "#FB8C00",
        "#E53935",
        "#00ACC1",
        "#6D4C41",
        "#3949AB",
    ]

    vehicle_color_map = {}

    # Central
    folium.Marker(
        location=center_location,
        popup=folium.Popup(
            f"<strong>{distribution_center.name}</strong><br>Central de distribuição",
            max_width=300,
        ),
        tooltip="Central de distribuição",
        icon=folium.Icon(color="black", icon="home"),
    ).add_to(route_map)

    for vehicle_index, vehicle_route in enumerate(solution.vehicle_routes):
        vehicle_color = vehicle_colors[vehicle_index % len(vehicle_colors)]

        vehicle_color_map[vehicle_route.vehicle.id] = (
            vehicle_route.vehicle.name,
            vehicle_color,
        )

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

        coordinates = [center_location]

        for stop in simulation.stops:
            point = stop.point

            point_location = [
                point.coordinate.latitude,
                point.coordinate.longitude,
            ]
            coordinates.append(point_location)

            if stop.delay_minutes > 0:
                operational_status = f"Atraso de {stop.delay_minutes:.1f} min"
            elif stop.waiting_minutes > 0:
                operational_status = f"Espera de {stop.waiting_minutes:.1f} min"
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

            popup_html = f"""
            <strong>{vehicle_route.vehicle.id} - {vehicle_route.vehicle.name}</strong><br>
            <strong>Parada {stop.sequence}: {point.id}</strong><br>
            <strong>{point.name}</strong><br><br>
            Tipo: {ATTENDANCE_TYPE_LABELS[point.attendance_type]}<br>
            Prioridade: {point.priority}<br>
            Demanda: {point.supply_demand}<br>
            Chegada estimada: {stop.estimated_arrival_time.strftime("%H:%M")}<br>
            Início do atendimento: {stop.service_start_time.strftime("%H:%M")}<br>
            Janela: {stop.time_window_start.strftime("%H:%M")} - {stop.time_window_end.strftime("%H:%M")}<br>
            Status: {operational_status}<br>
            Tempo desde saída: {stop.elapsed_minutes_from_departure:.1f} min<br>
            Prazo hormonal: {hormonal_status}
            """

            folium.Marker(
                location=point_location,
                popup=folium.Popup(popup_html, max_width=360),
                tooltip=(
                    f"{vehicle_route.vehicle.id} | "
                    f"Parada {stop.sequence} | "
                    f"{point.id} | "
                    f"P{point.priority}"
                ),
                icon=build_stop_icon(
                    order=stop.sequence,
                    vehicle_color=vehicle_color,
                    priority=point.priority,
                ),
            ).add_to(route_map)

        coordinates.append(center_location)

        folium.PolyLine(
            locations=coordinates,
            color=vehicle_color,
            weight=5,
            opacity=0.85,
            tooltip=f"{vehicle_route.vehicle.id} - {vehicle_route.vehicle.name}",
        ).add_to(route_map)

    route_map.get_root().html.add_child(
        folium.Element(build_map_legend(vehicle_color_map))
    )

    return route_map