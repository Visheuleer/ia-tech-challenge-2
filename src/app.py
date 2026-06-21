import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from womens_health_route_optimizer.visualization import create_fleet_map

from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.llm import RouteReportGenerator
from womens_health_route_optimizer.optimization import RouteOptimizer
from womens_health_route_optimizer.ui import (
    format_number_br,
    load_css,
    load_experiments_results,
    render_capacity_warning,
    render_experiments_charts,
    render_experiments_summary,
    render_experiments_table,
    render_llm_output,
    render_metric_card,
    render_page_header,
    render_section_title,
    render_settings_changed_warning,
    render_sidebar,
)

from womens_health_route_optimizer.ui.components import (
    build_fleet_dataframe,
    build_vehicle_summary_dataframe,
    render_fleet_metrics,
)

from womens_health_route_optimizer.utils.formatters import format_fleet_summary


st.set_page_config(
    page_title="Otimização de Rotas - Saúde da Mulher",
    layout="wide",
)


@st.cache_data
def load_data():
    center = load_distribution_center()
    points = load_attendance_points()
    return center, points


def reset_llm_outputs() -> None:
    st.session_state.instruction_manual = None
    st.session_state.visit_plan = None
    st.session_state.llm_answer = None


def ensure_session_state() -> None:
    if "last_run_fleet" not in st.session_state:
        st.session_state.last_run_fleet = None

    if "optimization_result" not in st.session_state:
        st.session_state.optimization_result = None

    if "last_run_settings" not in st.session_state:
        st.session_state.last_run_settings = None

    if "instruction_manual" not in st.session_state:
        st.session_state.instruction_manual = None

    if "visit_plan" not in st.session_state:
        st.session_state.visit_plan = None

    if "llm_answer" not in st.session_state:
        st.session_state.llm_answer = None


load_css()
ensure_session_state()

center, points = load_data()

render_page_header()

run_settings, run_optimization, run_fleet = render_sidebar()

settings_changed = (
    st.session_state.last_run_settings is not None
    and (
        st.session_state.last_run_settings != run_settings
        or st.session_state.last_run_fleet != run_fleet
    )
)

if settings_changed:
    render_settings_changed_warning()

if run_optimization or st.session_state.optimization_result is None:
    with st.spinner("Otimizando rotas com frota heterogênea..."):
        st.session_state.optimization_result = RouteOptimizer(
            distribution_center=center,
            attendance_points=points,
            app_settings=run_settings,
            fleet=run_fleet,
        ).optimize()

        st.session_state.last_run_settings = run_settings
        st.session_state.last_run_fleet = run_fleet
        reset_llm_outputs()

result = st.session_state.optimization_result
best_solution = result.best_solution
active_settings = st.session_state.last_run_settings or run_settings


render_section_title("Resumo da solução com frota heterogênea")

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col4, metric_col5, metric_col6 = st.columns(3)

with metric_col1:
    render_metric_card(
        "Distância total",
        f"{best_solution.total_distance_km:.2f} km",
        "Soma das distâncias percorridas por todos os veículos",
    )

with metric_col2:
    render_metric_card(
        "Fitness final",
        format_number_br(best_solution.fitness),
        "Distância e penalidades da frota",
    )

with metric_col3:
    render_metric_card(
        "Demanda total",
        str(best_solution.total_supply_demand),
        "Demanda somada de todos os atendimentos",
    )

with metric_col4:
    render_metric_card(
        "Duração operacional",
        f"{best_solution.total_duration_minutes:.1f} min",
        (
            "Maior duração entre as rotas, considerando "
            "execução paralela da frota"
        ),
    )

with metric_col5:
    render_metric_card(
        "Veículos utilizados",
        str(len(best_solution.vehicle_routes)),
        "Frota heterogênea disponível",
    )

with metric_col6:
    seed_text = (
        f"Seed: {active_settings.random_seed}"
        if active_settings.random_seed is not None
        else "Seed aleatória"
    )

    render_metric_card(
        "Gerações",
        str(result.generations),
        f"População: {active_settings.population_size} | {seed_text}",
    )


render_section_title("Penalidades aplicadas")

penalty_col1, penalty_col2, penalty_col3 = st.columns(3)
penalty_col4, penalty_col5, penalty_col6 = st.columns(3)

with penalty_col1:
    st.metric(
        "Prioridade",
        format_number_br(best_solution.priority_penalty),
    )

with penalty_col2:
    st.metric(
        "Janela de horário",
        format_number_br(best_solution.time_window_penalty),
    )

with penalty_col3:
    st.metric(
        "Capacidade",
        format_number_br(best_solution.capacity_penalty),
    )

with penalty_col4:
    st.metric(
        "Prazo hormonal",
        format_number_br(best_solution.hormonal_transport_penalty),
    )

with penalty_col5:
    st.metric(
        "Duração máxima",
        format_number_br(best_solution.route_duration_penalty),
    )

with penalty_col6:
    st.metric(
        "Compatibilidade veículo/carga",
        format_number_br(best_solution.vehicle_compatibility_penalty),
    )


if best_solution.route_duration_penalty > 0:
    st.warning(
        "A duração operacional da frota ultrapassou o limite máximo definido."
    )
else:
    st.success(
        "A duração operacional da frota está dentro do limite máximo definido."
    )

if best_solution.capacity_penalty > 0:
    render_capacity_warning()
else:
    st.success("Todas as rotas respeitam a capacidade dos veículos.")

if best_solution.hormonal_transport_penalty > 0:
    st.warning(
        "Há entregas de medicamentos hormonais fora do prazo máximo de transporte."
    )
else:
    st.success(
        "Todas as entregas de medicamentos hormonais respeitam o prazo máximo."
    )

if best_solution.vehicle_compatibility_penalty > 0:
    st.warning(
        "Há medicamentos hormonais atribuídos a veículos sem refrigeração."
    )
else:
    st.success(
        "As entregas hormonais foram atribuídas a veículos compatíveis."
    )

st.markdown("## Visão operacional da frota")

st.caption(
    "Mapa principal da solução otimizada. "
    "Cada cor representa um veículo, e cada marcador exibe a prioridade da parada."
)

fleet_map = create_fleet_map(
    solution=best_solution,
    distribution_center=center,
    app_settings=active_settings,
)

st_folium(
    fleet_map,
    width=None,
    height=720,
)

tab_table, tab_vehicle_summary, tab_summary, tab_fitness, tab_experiments, tab_llm = st.tabs(
    [
        "Roteiro da frota",
        "Resumo por veículo",
        "Resumo textual",
        "Evolução do fitness",
        "Experimentos",
        "Relatórios com LLM",
    ]
)


with tab_table:
    st.markdown("### Roteiro consolidado da frota")

    fleet_df = build_fleet_dataframe(
        best_solution=best_solution,
        distribution_center=center,
        app_settings=active_settings,
    )

    st.dataframe(
        fleet_df,
        use_container_width=True,
        hide_index=True,
    )


with tab_vehicle_summary:
    st.markdown("### Resumo operacional por veículo")

    vehicle_summary_df = build_vehicle_summary_dataframe(best_solution)

    st.dataframe(
        vehicle_summary_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Métricas gerais da frota")
    render_fleet_metrics(best_solution)


with tab_summary:
    st.markdown("### Resumo textual da frota")

    st.code(
        format_fleet_summary(
            solution=best_solution,
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


with tab_experiments:
    st.markdown("### Comparação de experimentos do algoritmo genético")

    experiments_df = load_experiments_results()

    if experiments_df is None:
        st.warning(
            "Nenhum resultado de experimento foi encontrado. "
            "Execute primeiro o script abaixo na raiz do projeto:"
        )

        st.code(
            "python experiments/run_experiments.py",
            language="bash",
        )
    else:
        render_experiments_summary(experiments_df)

        st.markdown("### Tabela comparativa")
        render_experiments_table(experiments_df)

        st.markdown("### Gráficos comparativos")
        render_experiments_charts(experiments_df)


with tab_llm:
    st.markdown("### Geração de relatórios com LLM")

    st.info(
        "A geração dos relatórios utiliza a API do Ollama. "
        "Configure a URL, o modelo e a API key na sidebar antes de gerar as respostas. "
        "A API key também pode ser definida pela variável de ambiente OLLAMA_API_KEY."
    )

    report_generator = RouteReportGenerator(app_settings=active_settings)

    llm_col1, llm_col2 = st.columns(2)

    with llm_col1:
        if st.button("Gerar manual de instruções", use_container_width=True):
            with st.spinner("Gerando manual..."):
                try:
                    st.session_state.instruction_manual = (
                        report_generator.generate_instruction_manual(
                            solution=best_solution,
                            distribution_center=center,
                        )
                    )
                    st.session_state.visit_plan = None
                    st.session_state.llm_answer = None
                except RuntimeError as error:
                    st.error(str(error))

    with llm_col2:
        if st.button("Gerar roteiro detalhado", use_container_width=True):
            with st.spinner("Gerando roteiro..."):
                try:
                    st.session_state.visit_plan = (
                        report_generator.generate_visit_plan(
                            solution=best_solution,
                            distribution_center=center,
                        )
                    )
                    st.session_state.instruction_manual = None
                    st.session_state.llm_answer = None
                except RuntimeError as error:
                    st.error(str(error))

    render_llm_output(
        title="Manual de instruções",
        content=st.session_state.instruction_manual,
    )

    render_llm_output(
        title="Roteiro detalhado",
        content=st.session_state.visit_plan,
    )

    st.markdown("### Perguntas sobre a rota")

    question = st.text_input(
        "Digite uma pergunta",
        placeholder="Ex.: Qual veículo atende os medicamentos hormonais?",
    )

    if st.button("Responder pergunta", use_container_width=True):
        if not question.strip():
            st.warning("Digite uma pergunta antes de consultar a LLM.")
        else:
            with st.spinner("Consultando LLM..."):
                try:
                    st.session_state.llm_answer = (
                        report_generator.answer_question(
                            solution=best_solution,
                            distribution_center=center,
                            question=question,
                        )
                    )
                    st.session_state.instruction_manual = None
                    st.session_state.visit_plan = None
                except RuntimeError as error:
                    st.error(str(error))

    render_llm_output(
        title="Resposta",
        content=st.session_state.llm_answer,
    )


