from pathlib import Path

import pandas as pd
import streamlit as st

from womens_health_route_optimizer.config import Settings
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    DistributionCenter,
    Route,
)
from womens_health_route_optimizer.optimization import simulate_route_stops


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
            Sistema experimental de roteirização com algoritmo genético, considerando prioridade de atendimento,
            janelas de horário e capacidade máxima de suprimentos do veículo.
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


def render_legend() -> None:
    st.markdown(
        """
        <div class="legend-box">
            <span class="legend-item"><span class="dot dot-black"></span>Central de distribuição</span>
            <span class="legend-item"><span class="dot dot-red"></span>Emergência obstétrica</span>
            <span class="legend-item"><span class="dot dot-purple"></span>Violência doméstica</span>
            <span class="legend-item"><span class="dot dot-blue"></span>Medicamento hormonal</span>
            <span class="legend-item"><span class="dot dot-green"></span>Atendimento pós-parto</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capacity_warning() -> None:
    st.markdown(
        """
        <div class="info-box">
            A rota excede a capacidade configurada do veículo. Nesta versão inicial, a violação é tratada
            como penalidade no fitness. Em evoluções futuras, essa restrição pode ser tratada com múltiplos
            veículos ou divisão automática de rotas.
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_route_dataframe(
    route: Route,
    distribution_center: DistributionCenter,
    app_settings: Settings,
) -> pd.DataFrame:
    stops = simulate_route_stops(
        route_points=route.ordered_points,
        distribution_center=distribution_center,
        app_settings=app_settings,
    )

    rows = []

    for stop in stops:
        point = stop.point
        attendance_label = ATTENDANCE_TYPE_LABELS[point.attendance_type]

        rows.append(
            {
                "Ordem": stop.sequence,
                "ID": point.id,
                "Local": point.name,
                "Tipo": attendance_label,
                "Prioridade": point.priority,
                "Demanda": point.supply_demand,
                "Chegada": stop.estimated_arrival_time.strftime("%H:%M"),
                "Início": stop.service_start_time.strftime("%H:%M"),
                "Janela": (
                    f"{stop.time_window_start.strftime('%H:%M')} - "
                    f"{stop.time_window_end.strftime('%H:%M')}"
                ),
                "Trecho (km)": round(stop.leg_distance_km, 2),
                "Espera (min)": round(stop.waiting_minutes, 1),
                "Atraso (min)": round(stop.delay_minutes, 1),
            }
        )

    return pd.DataFrame(rows)


def render_route_dataframe(route_df: pd.DataFrame) -> None:
    st.dataframe(
        route_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ordem": st.column_config.NumberColumn("Ordem", width="small"),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Local": st.column_config.TextColumn("Local", width="large"),
            "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
            "Prioridade": st.column_config.NumberColumn("Prioridade", width="small"),
            "Demanda": st.column_config.NumberColumn("Demanda", width="small"),
            "Chegada": st.column_config.TextColumn("Chegada", width="small"),
            "Início": st.column_config.TextColumn("Início", width="small"),
            "Janela": st.column_config.TextColumn("Janela", width="medium"),
            "Trecho (km)": st.column_config.NumberColumn(
                "Trecho (km)",
                format="%.2f",
                width="small",
            ),
            "Espera (min)": st.column_config.NumberColumn(
                "Espera (min)",
                format="%.1f",
                width="small",
            ),
            "Atraso (min)": st.column_config.NumberColumn(
                "Atraso (min)",
                format="%.1f",
                width="small",
            ),
        },
    )


def render_delay_feedback(route_df: pd.DataFrame) -> None:
    delayed_stops = route_df[route_df["Atraso (min)"] > 0]

    if delayed_stops.empty:
        st.success("Nenhuma parada apresentou atraso em relação à janela de horário.")
    else:
        st.warning(
            f"{len(delayed_stops)} parada(s) apresentaram atraso em relação à janela de horário."
        )


def render_llm_output(title: str, content: str | None) -> None:
    if not content:
        return

    st.markdown(f"#### {title}")
    st.markdown(
        '<div class="llm-output-box">',
        unsafe_allow_html=True,
    )
    st.markdown(content)
    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def load_experiments_results(file_path: Path = Path("experiments/outputs/experiments_results.csv")) -> pd.DataFrame | None:
    if not file_path.exists():
        return None

    return pd.read_csv(file_path)


def render_experiments_table(experiments_df: pd.DataFrame) -> None:

    st.dataframe(
        experiments_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "experiment": st.column_config.TextColumn("Experimento", width="medium"),
            "population_size": st.column_config.NumberColumn("População", width="small"),
            "generations": st.column_config.NumberColumn("Gerações", width="small"),
            "mutation_probability": st.column_config.NumberColumn(
                "Mutação",
                format="%.2f",
                width="small",
            ),
            "random_seed": st.column_config.TextColumn("Seed", width="small"),
            "elapsed_seconds": st.column_config.NumberColumn(
                "Tempo (s)",
                format="%.4f",
                width="small",
            ),
            "best_fitness": st.column_config.NumberColumn(
                "Fitness",
                format="%.2f",
                width="medium",
            ),
            "total_distance_km": st.column_config.NumberColumn(
                "Distância (km)",
                format="%.2f",
                width="small",
            ),
            "priority_penalty": st.column_config.NumberColumn(
                "Penalidade prioridade",
                format="%.2f",
                width="medium",
            ),
            "time_window_penalty": st.column_config.NumberColumn(
                "Penalidade janela",
                format="%.2f",
                width="medium",
            ),
            "capacity_penalty": st.column_config.NumberColumn(
                "Penalidade capacidade",
                format="%.2f",
                width="medium",
            ),
            "total_supply_demand": st.column_config.NumberColumn(
                "Demanda",
                width="small",
            ),
            "first_stop_id": st.column_config.TextColumn("Primeira parada", width="small"),
            "first_stop_type": st.column_config.TextColumn("Tipo inicial", width="medium"),
        },
    )


def render_experiments_summary(experiments_df: pd.DataFrame) -> None:

    best_fitness_row = experiments_df.loc[experiments_df["best_fitness"].idxmin()]
    best_distance_row = experiments_df.loc[experiments_df["total_distance_km"].idxmin()]
    fastest_row = experiments_df.loc[experiments_df["elapsed_seconds"].idxmin()]

    col1, col2, col3 = st.columns(3)

    with col1:
        render_metric_card(
            "Melhor fitness",
            format_number_br(float(best_fitness_row["best_fitness"])),
            f"Experimento: {best_fitness_row['experiment']}",
        )

    with col2:
        render_metric_card(
            "Menor distância",
            f"{best_distance_row['total_distance_km']:.2f} km",
            f"Experimento: {best_distance_row['experiment']}",
        )

    with col3:
        render_metric_card(
            "Menor tempo",
            f"{fastest_row['elapsed_seconds']:.4f}s",
            f"Experimento: {fastest_row['experiment']}",
        )


def render_experiments_charts(experiments_df: pd.DataFrame) -> None:

    chart_df = experiments_df.set_index("experiment")

    st.markdown("#### Fitness por experimento")
    st.bar_chart(
        chart_df[["best_fitness"]],
        use_container_width=True,
    )

    st.markdown("#### Distância total por experimento")
    st.bar_chart(
        chart_df[["total_distance_km"]],
        use_container_width=True,
    )

    st.markdown("#### Tempo de execução por experimento")
    st.bar_chart(
        chart_df[["elapsed_seconds"]],
        use_container_width=True,
    )