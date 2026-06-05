import streamlit as st

from womens_health_route_optimizer.config import Settings, settings


def render_sidebar() -> tuple[Settings, bool]:
    st.sidebar.title("Parâmetros")

    run_optimization = st.sidebar.button(
        "Executar otimização",
        type="primary",
        use_container_width=True,
    )

    st.sidebar.caption(
        "Ajuste os parâmetros abaixo e execute novamente para recalcular a rota."
    )

    with st.sidebar.expander(
        "Algoritmo genético",
        expanded=False,
    ):
        population_size = st.slider(
            "Tamanho da população",
            min_value=20,
            max_value=300,
            value=settings.population_size,
            step=10,
        )

        generations = st.slider(
            "Número de gerações",
            min_value=20,
            max_value=500,
            value=settings.generations,
            step=20,
        )

        mutation_probability = st.slider(
            "Probabilidade de mutação",
            min_value=0.0,
            max_value=1.0,
            value=settings.mutation_probability,
            step=0.05,
        )

        use_random_seed = st.checkbox(
            "Usar seed fixa",
            value=settings.random_seed is not None,
            help=(
                "Permite reproduzir os mesmos resultados quando os demais "
                "parâmetros permanecem iguais."
            ),
        )

        random_seed = st.number_input(
            "Seed aleatória",
            min_value=0,
            value=settings.random_seed or 0,
            step=1,
            disabled=not use_random_seed,
        )

    with st.sidebar.expander(
        "Operação da rota",
        expanded=False,
    ):
        vehicle_capacity = st.number_input(
            "Capacidade máxima de suprimentos",
            min_value=1,
            max_value=100,
            value=settings.vehicle_capacity,
            step=5,
        )

        max_hormonal_transport_minutes = st.number_input(
            "Prazo para medicamentos hormonais",
            min_value=30,
            max_value=720,
            value=settings.max_hormonal_transport_minutes,
            step=30,
            help=(
                "Tempo máximo, em minutos, entre a saída da central "
                "e a entrega do medicamento."
            ),
        )

        max_route_duration_minutes = st.number_input(
            "Duração máxima da rota",
            min_value=60,
            max_value=1440,
            value=settings.max_route_duration_minutes,
            step=30,
            help="Inclui deslocamentos, esperas, atendimentos e retorno à central.",
        )

    with st.sidebar.expander(
        "Pesos da função fitness",
        expanded=False,
    ):
        st.caption(
            "Valores maiores tornam a respectiva restrição mais importante "
            "durante a otimização."
        )

        priority_penalty_weight = st.number_input(
            "Prioridade dos atendimentos",
            min_value=0.0,
            value=settings.priority_penalty_weight,
            step=100.0,
        )

        time_window_penalty_weight = st.number_input(
            "Janelas de horário",
            min_value=0.0,
            value=settings.time_window_penalty_weight,
            step=50.0,
        )

        capacity_penalty_weight = st.number_input(
            "Capacidade do veículo",
            min_value=0.0,
            value=settings.capacity_penalty_weight,
            step=100.0,
        )

        hormonal_transport_penalty_weight = st.number_input(
            "Prazo dos medicamentos hormonais",
            min_value=0.0,
            value=settings.hormonal_transport_penalty_weight,
            step=50.0,
        )

        route_duration_penalty_weight = st.number_input(
            "Duração máxima da rota",
            min_value=0.0,
            value=settings.route_duration_penalty_weight,
            step=50.0,
        )

    with st.sidebar.expander(
        "Integração com LLM",
        expanded=False,
    ):
        ollama_base_url = st.text_input(
            "URL do Ollama",
            value=settings.ollama_base_url,
        )

        ollama_model = st.text_input(
            "Modelo",
            value=settings.ollama_model,
        )

        ollama_api_key = st.text_input(
            "API key",
            value="",
            type="password",
            help=(
                "Pode ser deixada vazia quando OLLAMA_API_KEY "
                "já estiver configurada no ambiente."
            ),
        )

        llm_temperature = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=settings.llm_temperature,
            step=0.1,
        )

    run_settings = Settings(
        population_size=population_size,
        generations=generations,
        mutation_probability=mutation_probability,
        elitism_size=settings.elitism_size,
        random_seed=random_seed if use_random_seed else None,
        vehicle_capacity=vehicle_capacity,
        average_vehicle_speed_kmh=settings.average_vehicle_speed_kmh,
        route_start_time=settings.route_start_time,
        priority_penalty_weight=priority_penalty_weight,
        time_window_penalty_weight=time_window_penalty_weight,
        capacity_penalty_weight=capacity_penalty_weight,
        max_hormonal_transport_minutes=max_hormonal_transport_minutes,
        hormonal_transport_penalty_weight=(
            hormonal_transport_penalty_weight
        ),
        max_route_duration_minutes=max_route_duration_minutes,
        route_duration_penalty_weight=route_duration_penalty_weight,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_api_key=ollama_api_key or None,
        llm_temperature=llm_temperature,
    )

    return run_settings, run_optimization


def render_settings_changed_warning() -> None:
    st.sidebar.warning(
        "Os parâmetros foram alterados. Execute novamente para atualizar a rota."
    )