import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import (
    ATTENDANCE_TYPE_LABELS,
    Vehicle,
)
from womens_health_route_optimizer.optimization import (
    RouteOptimizer,
    simulate_route_stops,
)
from womens_health_route_optimizer.utils.formatters import format_route_summary
from womens_health_route_optimizer.visualization import create_route_map


st.set_page_config(
    page_title="Otimização de Rotas - Saúde da Mulher",
    layout="wide",
)


CUSTOM_CSS = """
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }

    .subtitle {
        font-size: 1rem;
        color: #A0A0A0;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    .metric-card {
        background: #1E1E26;
        border: 1px solid #333342;
        border-radius: 16px;
        padding: 18px 20px;
        min-height: 110px;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #B6B6C3;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #FFFFFF;
    }

    .metric-helper {
        font-size: 0.75rem;
        color: #8C8C99;
        margin-top: 0.35rem;
    }

    .legend-box {
        background: #1E1E26;
        border: 1px solid #333342;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 1rem;
    }

    .legend-item {
        display: inline-block;
        margin-right: 18px;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }

    .dot {
        height: 11px;
        width: 11px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }

    .dot-red { background-color: #E74C3C; }
    .dot-purple { background-color: #9B59B6; }
    .dot-blue { background-color: #3498DB; }
    .dot-green { background-color: #2ECC71; }
    .dot-black { background-color: #222222; border: 1px solid #FFFFFF; }

    .info-box {
        background: #1E1E26;
        border-left: 4px solid #FF4B4B;
        border-radius: 12px;
        padding: 14px 16px;
        color: #DADADA;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background: #1E1E26;
        border: 1px solid #333342;
        padding: 16px;
        border-radius: 16px;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
    }
</style>
"""


@st.cache_data
def load_data():
    center = load_distribution_center()
    points = load_attendance_points()
    return center, points


def build_run_settings(
    population_size: int,
    generations: int,
    mutation_probability: float,
    vehicle_capacity: int,
    priority_penalty_weight: float,
    time_window_penalty_weight: float,
    capacity_penalty_weight: float,
) -> Settings:
    return Settings(
        population_size=population_size,
        generations=generations,
        mutation_probability=mutation_probability,
        elitism_size=settings.elitism_size,
        vehicle_capacity=vehicle_capacity,
        average_vehicle_speed_kmh=settings.average_vehicle_speed_kmh,
        route_start_time=settings.route_start_time,
        priority_penalty_weight=priority_penalty_weight,
        time_window_penalty_weight=time_window_penalty_weight,
        capacity_penalty_weight=capacity_penalty_weight,
    )


def build_route_dataframe(route, distribution_center, app_settings: Settings) -> pd.DataFrame:
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


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

center, points = load_data()

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

st.sidebar.title("Parâmetros")

st.sidebar.markdown("### Algoritmo genético")

population_size = st.sidebar.slider(
    "Tamanho da população",
    min_value=20,
    max_value=300,
    value=settings.population_size,
    step=10,
)

generations = st.sidebar.slider(
    "Número de gerações",
    min_value=20,
    max_value=500,
    value=settings.generations,
    step=20,
)

mutation_probability = st.sidebar.slider(
    "Probabilidade de mutação",
    min_value=0.0,
    max_value=1.0,
    value=settings.mutation_probability,
    step=0.05,
)

st.sidebar.markdown("### Veículo")

vehicle_capacity = st.sidebar.slider(
    "Capacidade máxima de suprimentos",
    min_value=10,
    max_value=60,
    value=settings.vehicle_capacity,
    step=5,
)

st.sidebar.markdown("### Penalidades")

priority_penalty_weight = st.sidebar.number_input(
    "Peso da prioridade",
    min_value=0.0,
    value=settings.priority_penalty_weight,
    step=100.0,
)

time_window_penalty_weight = st.sidebar.number_input(
    "Peso da janela de horário",
    min_value=0.0,
    value=settings.time_window_penalty_weight,
    step=50.0,
)

capacity_penalty_weight = st.sidebar.number_input(
    "Peso da capacidade",
    min_value=0.0,
    value=settings.capacity_penalty_weight,
    step=100.0,
)

run_settings = build_run_settings(
    population_size=population_size,
    generations=generations,
    mutation_probability=mutation_probability,
    vehicle_capacity=vehicle_capacity,
    priority_penalty_weight=priority_penalty_weight,
    time_window_penalty_weight=time_window_penalty_weight,
    capacity_penalty_weight=capacity_penalty_weight,
)

vehicle = Vehicle(
    id="V001",
    name="Veículo 1",
    max_supply_capacity=run_settings.vehicle_capacity,
)

if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None

if "last_run_settings" not in st.session_state:
    st.session_state.last_run_settings = None

run_optimization = st.sidebar.button(
    "Executar otimização",
    type="primary",
    use_container_width=True,
)

settings_changed = (
    st.session_state.last_run_settings is not None
    and st.session_state.last_run_settings != run_settings
)

if settings_changed:
    st.sidebar.warning(
        "Parâmetros alterados. Clique em Executar otimização para atualizar a rota."
    )

if run_optimization or st.session_state.optimization_result is None:
    with st.spinner("Otimizando rota com algoritmo genético..."):
        st.session_state.optimization_result = RouteOptimizer(
            distribution_center=center,
            attendance_points=points,
            vehicle=vehicle,
            app_settings=run_settings,
        ).optimize()

        st.session_state.last_run_settings = run_settings

result = st.session_state.optimization_result
best_route = result.best_route
active_settings = st.session_state.last_run_settings or run_settings

st.markdown('<div class="section-title">Resumo da solução</div>', unsafe_allow_html=True)

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    render_metric_card(
        "Distância total",
        f"{best_route.total_distance_km:.2f} km",
        "Percurso saindo e retornando à central",
    )

with metric_col2:
    render_metric_card(
        "Fitness final",
        f"{best_route.fitness:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Distância + penalidades",
    )

with metric_col3:
    render_metric_card(
        "Demanda total",
        str(best_route.total_supply_demand),
        f"Capacidade do veículo: {vehicle.max_supply_capacity}",
    )

with metric_col4:
    render_metric_card(
        "Gerações",
        str(result.generations),
        f"População: {active_settings.population_size}",
    )

st.markdown('<div class="section-title">Penalidades aplicadas</div>', unsafe_allow_html=True)

penalty_col1, penalty_col2, penalty_col3 = st.columns(3)

with penalty_col1:
    st.metric(
        "Prioridade",
        f"{best_route.priority_penalty:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

with penalty_col2:
    st.metric(
        "Janela de horário",
        f"{best_route.time_window_penalty:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

with penalty_col3:
    st.metric(
        "Capacidade",
        f"{best_route.capacity_penalty:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

if best_route.capacity_penalty > 0:
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

st.markdown('<div class="section-title">Mapa da rota otimizada</div>', unsafe_allow_html=True)

render_legend()

route_map = create_route_map(
    route=best_route,
    distribution_center=center,
    app_settings=active_settings,
)

st_folium(
    route_map,
    width=None,
    height=620,
)

route_df = build_route_dataframe(
    route=best_route,
    distribution_center=center,
    app_settings=active_settings,
)

tab_table, tab_summary, tab_fitness = st.tabs(
    [
        "Tabela da rota",
        "Resumo textual",
        "Evolução do fitness",
    ]
)

with tab_table:
    st.markdown("### Sequência operacional de visitas")

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

    delayed_stops = route_df[route_df["Atraso (min)"] > 0]

    if delayed_stops.empty:
        st.success("Nenhuma parada apresentou atraso em relação à janela de horário.")
    else:
        st.warning(
            f"{len(delayed_stops)} parada(s) apresentaram atraso em relação à janela de horário."
        )

with tab_summary:
    st.markdown("### Resumo textual da rota")

    st.code(
        format_route_summary(
            route=best_route,
            distribution_center=center,
            app_settings=active_settings,
        ),
        language="text",
    )

with tab_fitness:
    st.markdown("### Evolução do melhor fitness por geração")

    fitness_df = pd.DataFrame(
        {
            "Geração": list(range(1, len(result.fitness_history) + 1)),
            "Fitness": result.fitness_history,
        }
    )

    st.line_chart(
        fitness_df,
        x="Geração",
        y="Fitness",
        use_container_width=True,
    )