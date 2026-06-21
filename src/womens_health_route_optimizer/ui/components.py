from pathlib import Path

import pandas as pd
import streamlit as st


STYLE_PATH = Path(__file__).resolve().parent / "styles.css"


def load_css() -> None:
    css = STYLE_PATH.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


def format_number_br(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_page_header() -> None:
    st.markdown(
        '<div class="main-title">Otimização de Rotas para Atendimento Especializado à Mulher</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitle">
            Sistema experimental de roteirização com algoritmo genético, considerando frota heterogênea, prioridades, janelas de horário, capacidade por veículo, prazo hormonal e compatibilidade veículo/carga.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str) -> None:
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, helper: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capacity_warning() -> None:
    st.markdown(
        """
        <div class="info-box">
            Uma ou mais rotas excederam a capacidade do veículo correspondente.
            A violação foi incorporada como penalidade no fitness da solução.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_llm_output(title: str, content: str | None) -> None:
    if not content:
        return

    st.markdown(f"#### {title}")

    with st.container(border=True):
        st.markdown(content)


def load_experiments_results(file_path: Path = Path("experiments/outputs/experiments_results.csv")) -> pd.DataFrame | None:
    if not file_path.exists():
        return None

    return pd.read_csv(file_path)


def render_experiments_table(experiments_df: pd.DataFrame) -> None:
    if experiments_df.empty:
        st.warning("O arquivo de experimentos está vazio.")
        return

    columns_to_show = [
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
        "longest_vehicle_duration_minutes",
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in experiments_df.columns
    ]

    table_df = experiments_df[available_columns].copy()

    rename_map = {
        "experiment_name": "Experimento",
        "population_size": "População",
        "generations": "Gerações",
        "mutation_probability": "Mutação",
        "elitism_size": "Elitismo",
        "random_seed": "Seed",
        "fitness": "Fitness",
        "initial_fitness": "Fitness inicial",
        "fitness_improvement": "Melhoria",
        "total_distance_km": "Distância total (km)",
        "total_duration_minutes": "Duração operacional (min)",
        "priority_penalty": "Prioridade",
        "time_window_penalty": "Janela",
        "capacity_penalty": "Capacidade",
        "hormonal_transport_penalty": "Prazo hormonal",
        "route_duration_penalty": "Duração máxima",
        "vehicle_compatibility_penalty": "Compatibilidade",
        "total_supply_demand": "Demanda total",
        "vehicles_count": "Veículos",
        "longest_vehicle_id": "Veículo mais longo",
        "longest_vehicle_duration_minutes": "Maior duração individual (min)",
    }

    table_df = table_df.rename(columns=rename_map)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    if "vehicle_routes" in experiments_df.columns:
        with st.expander("Sequências de rotas por experimento"):
            routes_df = experiments_df[
                ["experiment_name", "vehicle_routes"]
            ].rename(
                columns={
                    "experiment_name": "Experimento",
                    "vehicle_routes": "Rotas por veículo",
                }
            )

            st.dataframe(
                routes_df,
                use_container_width=True,
                hide_index=True,
            )


def render_experiments_summary(experiments_df: pd.DataFrame) -> None:
    if experiments_df.empty:
        st.warning("O arquivo de experimentos está vazio.")
        return

    best_row = experiments_df.loc[experiments_df["fitness"].idxmin()]
    best_experiment_name = best_row["experiment_name"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Melhor experimento",
            best_experiment_name,
            f"Fitness: {best_row['fitness']:,.2f}",
        )

    with col2:
        st.metric(
            "Menor distância",
            f"{experiments_df['total_distance_km'].min():.2f} km",
        )

    with col3:
        st.metric(
            "Menor duração operacional",
            f"{experiments_df['total_duration_minutes'].min():.1f} min",
        )

    with col4:
        st.metric(
            "Maior melhoria",
            f"{experiments_df['fitness_improvement'].max():,.2f}",
        )


def render_experiments_charts(experiments_df: pd.DataFrame) -> None:
    if experiments_df.empty:
        st.warning("O arquivo de experimentos está vazio.")
        return

    required_columns = {
        "experiment_name",
        "fitness",
        "total_distance_km",
        "total_duration_minutes",
    }

    missing_columns = required_columns - set(experiments_df.columns)

    if missing_columns:
        st.warning(
            "Não foi possível renderizar todos os gráficos. "
            f"Colunas ausentes: {', '.join(sorted(missing_columns))}"
        )
        return

    chart_df = experiments_df.copy()

    st.markdown("#### Fitness final por experimento")
    st.bar_chart(
        chart_df,
        x="experiment_name",
        y="fitness",
        use_container_width=True,
    )

    st.markdown("#### Melhoria do fitness por experimento")
    if "fitness_improvement" in chart_df.columns:
        st.bar_chart(
            chart_df,
            x="experiment_name",
            y="fitness_improvement",
            use_container_width=True,
        )
    else:
        st.info("Coluna `fitness_improvement` não encontrada.")

    st.markdown("#### Distância total da frota por experimento")
    st.bar_chart(
        chart_df,
        x="experiment_name",
        y="total_distance_km",
        use_container_width=True,
    )

    st.markdown("#### Duração operacional da frota por experimento")
    st.bar_chart(
        chart_df,
        x="experiment_name",
        y="total_duration_minutes",
        use_container_width=True,
    )

    penalty_columns = [
        column
        for column in [
            "priority_penalty",
            "time_window_penalty",
            "capacity_penalty",
            "hormonal_transport_penalty",
            "route_duration_penalty",
            "vehicle_compatibility_penalty",
        ]
        if column in chart_df.columns
    ]

    if penalty_columns:
        st.markdown("#### Penalidades por experimento")

        penalty_df = chart_df[
            ["experiment_name", *penalty_columns]
        ].set_index("experiment_name")

        st.bar_chart(
            penalty_df,
            use_container_width=True,
        )


def build_fleet_dataframe(
    best_solution,
    distribution_center,
    app_settings,
) -> pd.DataFrame:

    from dataclasses import replace

    from womens_health_route_optimizer.domain import (
        ATTENDANCE_TYPE_LABELS,
    )
    from womens_health_route_optimizer.domain.enums import AttendanceType
    from womens_health_route_optimizer.optimization.simulation import (
        simulate_route,
    )

    rows = []

    for vehicle_route in best_solution.vehicle_routes:
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

        for stop in simulation.stops:
            point = stop.point

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

            if stop.delay_minutes > 0:
                status = f"Atraso de {stop.delay_minutes:.1f} min"
            elif stop.waiting_minutes > 0:
                status = f"Espera de {stop.waiting_minutes:.1f} min"
            else:
                status = "No prazo"

            rows.append(
                {
                    "Veículo": vehicle_route.vehicle.id,
                    "Tipo de veículo": vehicle_route.vehicle.name,
                    "Refrigerado": (
                        "Sim"
                        if vehicle_route.vehicle.is_refrigerated
                        else "Não"
                    ),
                    "Ordem no veículo": stop.sequence,
                    "Código": point.id,
                    "Local": point.name,
                    "Tipo de atendimento": ATTENDANCE_TYPE_LABELS[
                        point.attendance_type
                    ],
                    "Prioridade": point.priority,
                    "Chegada estimada": stop.estimated_arrival_time.strftime(
                        "%H:%M"
                    ),
                    "Início do atendimento": stop.service_start_time.strftime(
                        "%H:%M"
                    ),
                    "Janela": (
                        f"{stop.time_window_start.strftime('%H:%M')} - "
                        f"{stop.time_window_end.strftime('%H:%M')}"
                    ),
                    "Status operacional": status,
                    "Tempo desde saída (min)": round(
                        stop.elapsed_minutes_from_departure,
                        1,
                    ),
                    "Demanda": point.supply_demand,
                    "Demanda do veículo": vehicle_route.total_supply_demand,
                    "Capacidade do veículo": (
                        vehicle_route.vehicle.max_supply_capacity
                    ),
                    "Status hormonal": hormonal_status,
                }
            )

        rows.append(
            {
                "Veículo": vehicle_route.vehicle.id,
                "Tipo de veículo": vehicle_route.vehicle.name,
                "Refrigerado": (
                    "Sim"
                    if vehicle_route.vehicle.is_refrigerated
                    else "Não"
                ),
                "Ordem no veículo": "Retorno",
                "Código": "CD",
                "Local": distribution_center.name,
                "Tipo de atendimento": "Retorno à central",
                "Prioridade": "-",
                "Chegada estimada": simulation.return_time.strftime("%H:%M"),
                "Início do atendimento": "-",
                "Janela": "-",
                "Status operacional": "Retorno concluído",
                "Tempo desde saída (min)": round(
                    simulation.total_duration_minutes,
                    1,
                ),
                "Demanda": 0,
                "Demanda do veículo": vehicle_route.total_supply_demand,
                "Capacidade do veículo": (
                    vehicle_route.vehicle.max_supply_capacity
                ),
                "Status hormonal": "Não se aplica",
            }
        )

    return pd.DataFrame(rows)


def render_fleet_metrics(best_solution) -> None:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Fitness",
        f"{best_solution.fitness:,.2f}",
    )

    col2.metric(
        "Distância total",
        f"{best_solution.total_distance_km:.2f} km",
    )

    col3.metric(
        "Duração operacional",
        f"{best_solution.total_duration_minutes:.1f} min",
    )

    col4.metric(
        "Demanda total",
        best_solution.total_supply_demand,
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Penalidade janela",
        f"{best_solution.time_window_penalty:,.2f}",
    )

    col6.metric(
        "Penalidade capacidade",
        f"{best_solution.capacity_penalty:,.2f}",
    )

    col7.metric(
        "Penalidade hormonal",
        f"{best_solution.hormonal_transport_penalty:,.2f}",
    )

    col8.metric(
        "Compatibilidade",
        f"{best_solution.vehicle_compatibility_penalty:,.2f}",
    )


def build_vehicle_summary_dataframe(best_solution) -> pd.DataFrame:
    rows = []

    for vehicle_route in best_solution.vehicle_routes:
        rows.append(
            {
                "Veículo": vehicle_route.vehicle.id,
                "Tipo": vehicle_route.vehicle.name,
                "Refrigerado": (
                    "Sim" if vehicle_route.vehicle.is_refrigerated else "Não"
                ),
                "Paradas": len(vehicle_route.ordered_points),
                "Demanda": vehicle_route.total_supply_demand,
                "Capacidade": vehicle_route.vehicle.max_supply_capacity,
                "Distância (km)": round(vehicle_route.total_distance_km, 2),
                "Duração (min)": round(vehicle_route.total_duration_minutes, 1),
                "Fitness": round(vehicle_route.fitness, 2),
                "Janela": round(vehicle_route.time_window_penalty, 2),
                "Capacidade penalidade": round(vehicle_route.capacity_penalty, 2),
                "Hormonal": round(vehicle_route.hormonal_transport_penalty, 2),
                "Compatibilidade": round(
                    vehicle_route.vehicle_compatibility_penalty,
                    2,
                ),
            }
        )

    return pd.DataFrame(rows)

