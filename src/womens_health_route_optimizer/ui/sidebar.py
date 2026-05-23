import streamlit as st

from womens_health_route_optimizer.config import Settings, settings


def render_sidebar() -> Settings:

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

    st.sidebar.markdown("### LLM")

    llm_provider = st.sidebar.selectbox(
        "Provedor",
        options=["mock", "ollama"],
        index=0,
    )

    ollama_model = st.sidebar.text_input(
        "Modelo Ollama",
        value=settings.ollama_model,
    )

    llm_temperature = st.sidebar.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=settings.llm_temperature,
        step=0.1,
    )

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
        llm_provider=llm_provider,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=ollama_model,
        llm_temperature=llm_temperature,
    )


def render_run_button() -> bool:
    return st.sidebar.button(
        "Executar otimização",
        type="primary",
        use_container_width=True,
    )


def render_settings_changed_warning() -> None:
    st.sidebar.warning(
        "Parâmetros alterados. Clique em Executar otimização para atualizar a rota."
    )