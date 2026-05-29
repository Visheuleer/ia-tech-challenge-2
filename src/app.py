import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from womens_health_route_optimizer.data import (
    load_attendance_points,
    load_distribution_center,
)
from womens_health_route_optimizer.domain import Vehicle
from womens_health_route_optimizer.llm import RouteReportGenerator
from womens_health_route_optimizer.optimization import RouteOptimizer
from womens_health_route_optimizer.ui import (
    build_route_dataframe,
    format_number_br,
    load_css,
    load_experiments_results,
    render_capacity_warning,
    render_delay_feedback,
    render_experiments_charts,
    render_experiments_summary,
    render_experiments_table,
    render_legend,
    render_llm_output,
    render_metric_card,
    render_page_header,
    render_route_dataframe,
    render_run_button,
    render_section_title,
    render_settings_changed_warning,
    render_sidebar,
)
from womens_health_route_optimizer.utils.formatters import format_route_summary
from womens_health_route_optimizer.visualization import create_route_map


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

run_settings = render_sidebar()
run_optimization = render_run_button()

settings_changed = (
    st.session_state.last_run_settings is not None
    and st.session_state.last_run_settings != run_settings
)

if settings_changed:
    render_settings_changed_warning()

vehicle = Vehicle(
    id="V001",
    name="Veículo 1",
    max_supply_capacity=run_settings.vehicle_capacity,
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
        reset_llm_outputs()

result = st.session_state.optimization_result
best_route = result.best_route
active_settings = st.session_state.last_run_settings or run_settings

render_section_title("Resumo da solução")

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
        format_number_br(best_route.fitness),
        "Distância + penalidades",
    )

with metric_col3:
    render_metric_card(
        "Demanda total",
        str(best_route.total_supply_demand),
        f"Capacidade do veículo: {vehicle.max_supply_capacity}",
    )

with metric_col4:
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

with penalty_col1:
    st.metric(
        "Prioridade",
        format_number_br(best_route.priority_penalty),
    )

with penalty_col2:
    st.metric(
        "Janela de horário",
        format_number_br(best_route.time_window_penalty),
    )

with penalty_col3:
    st.metric(
        "Capacidade",
        format_number_br(best_route.capacity_penalty),
    )

if best_route.capacity_penalty > 0:
    render_capacity_warning()

render_section_title("Mapa da rota otimizada")

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

tab_table, tab_summary, tab_fitness, tab_experiments, tab_llm = st.tabs(
    [
        "Tabela da rota",
        "Resumo textual",
        "Evolução do fitness",
        "Experimentos",
        "Relatórios com LLM",
    ]
)

with tab_table:
    st.markdown("### Sequência operacional de visitas")

    render_route_dataframe(route_df)
    render_delay_feedback(route_df)

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
                            route=best_route,
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
                    st.session_state.visit_plan = report_generator.generate_visit_plan(
                        route=best_route,
                        distribution_center=center,
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
        placeholder="Ex.: Qual é o próximo atendimento prioritário?",
    )

    if st.button("Responder pergunta", use_container_width=True):
        if not question.strip():
            st.warning("Digite uma pergunta antes de consultar a LLM.")
        else:
            with st.spinner("Consultando LLM..."):
                try:
                    st.session_state.llm_answer = report_generator.answer_question(
                        route=best_route,
                        distribution_center=center,
                        question=question,
                    )
                    st.session_state.instruction_manual = None
                    st.session_state.visit_plan = None
                except RuntimeError as error:
                    st.error(str(error))

    render_llm_output(
        title="Resposta",
        content=st.session_state.llm_answer,
    )