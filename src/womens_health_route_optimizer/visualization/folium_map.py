import folium

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization import simulate_route_stops


MARKER_COLORS = {
    "obstetric_emergency": "red",
    "domestic_violence": "purple",
    "hormonal_medication": "blue",
    "postpartum_care": "green",
}


def create_route_map(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings = settings,
) -> folium.Map:

    center_location = [
        distribution_center.coordinate.latitude,
        distribution_center.coordinate.longitude,
    ]

    route_map = folium.Map(
        location=center_location,
        zoom_start=12,
    )

    folium.Marker(
        location=center_location,
        popup=f"<b>{distribution_center.name}</b><br>{distribution_center.notes}",
        tooltip="Central de distribuição",
        icon=folium.Icon(color="black", icon="home", prefix="fa"),
    ).add_to(route_map)

    stops = simulate_route_stops(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    route_coordinates = [center_location]

    for stop in stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[point.attendance_type]

        point_location = [
            point.coordinate.latitude,
            point.coordinate.longitude,
        ]

        route_coordinates.append(point_location)

        marker_color = MARKER_COLORS.get(
            point.attendance_type.value,
            "gray",
        )

        status_parts: list[str] = []

        if stop.waiting_minutes > 0:
            status_parts.append(f"Espera: {stop.waiting_minutes:.1f} min")

        if stop.delay_minutes > 0:
            status_parts.append(f"Atraso: {stop.delay_minutes:.1f} min")

        if not status_parts:
            status_parts.append("Sem espera/atraso")

        status = " | ".join(status_parts)

        hormonal_status = "Não se aplica"

        if point.attendance_type.value == "hormonal_medication":
            excess = max(
                0.0,
                stop.elapsed_minutes_from_departure
                - app_settings.max_hormonal_transport_minutes,
            )

            hormonal_status = (
                f"Prazo excedido em {excess:.1f} min"
                if excess > 0
                else "Dentro do prazo"
            )

        popup_html = f"""
        <b>{stop.sequence:02d}. {point.name}</b><br>
        <b>Tipo:</b> {attendance_label}<br>
        <b>Prioridade:</b> {point.priority}<br>
        <b>Demanda:</b> {point.supply_demand}<br>
        <b>Chegada:</b> {stop.estimated_arrival_time.strftime("%H:%M")}<br>
        <b>Início:</b> {stop.service_start_time.strftime("%H:%M")}<br>
        <b>Tempo desde a saída:</b>{stop.elapsed_minutes_from_departure:.1f} min<br>
        <b>Janela:</b> {stop.time_window_start.strftime("%H:%M")} - {stop.time_window_end.strftime("%H:%M")}<br>
        <b>Trecho:</b> {stop.leg_distance_km:.2f} km<br>
        <b>Status:</b> {status}<br>
        <b>Status hormonal:</b> {hormonal_status}<br>
        <b>Observação:</b> {point.notes}
        """

        folium.Marker(
            location=point_location,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{stop.sequence:02d}. {attendance_label}",
            icon=folium.Icon(color=marker_color, icon="plus-sign"),
        ).add_to(route_map)

    route_coordinates.append(center_location)

    folium.PolyLine(
        locations=route_coordinates,
        weight=4,
        opacity=0.8,
        tooltip="Rota otimizada",
    ).add_to(route_map)

    return route_map