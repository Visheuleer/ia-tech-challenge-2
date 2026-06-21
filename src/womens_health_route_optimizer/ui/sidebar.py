from dataclasses import replace

import streamlit as st

from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain.enums import VehicleType
from womens_health_route_optimizer.domain.models import Vehicle


def build_configured_fleet(
    motorcycle_capacity: int,
    motorcycle_speed: float,
    refrigerated_capacity: int,
    refrigerated_speed: float,
    van_capacity: int,
    van_speed: float,
) -> list[Vehicle]:
    return [
        Vehicle(
            id="V001",
            name="Moto de atendimento",
            vehicle_type=VehicleType.MOTORCYCLE,
            max_supply_capacity=motorcycle_capacity,
            is_refrigerated=False,
            average_speed_kmh=motorcycle_speed,
        ),
        Vehicle(
            id="V002",
            name="Veículo refrigerado",
            vehicle_type=VehicleType.REFRIGERATED_VEHICLE,
            max_supply_capacity=refrigerated_capacity,
            is_refrigerated=True,
            average_speed_kmh=refrigerated_speed,
        ),
        Vehicle(
            id="V003",
            name="Van operacional",
            vehicle_type=VehicleType.OPERATIONAL_VAN,
            max_supply_capacity=van_capacity,
            is_refrigerated=False,
            average_speed_kmh=van_speed,
        ),
    ]


def render_sidebar() -> tuple[Settings, bool, list[Vehicle]]:
    st.sidebar.title("Parâmetros")

    run_optimization = st.sidebar.button(
        "Executar otimização",
        type="primary",
        use_container_width=True,
    )

    st.sidebar.caption(
        "Ajuste os parâmetros abaixo e execute novamente para recalcular a frota."
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

        elitism_size = st.slider(
            "Elitismo",
            min_value=1,
            max_value=10,
            value=settings.elitism_size,
            step=1,
            help=(
                "Quantidade de melhores soluções preservadas diretamente "
                "para a próxima geração."
            ),
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
            "Frota disponível",
            expanded=False,
    ):
        st.caption(
            "Configure a capacidade e a velocidade média de cada veículo. "
            "A refrigeração é uma característica fixa do tipo de veículo."
        )

        with st.expander(
                "Moto de atendimento",
                expanded=False,
        ):
            motorcycle_capacity = st.number_input(
                "Capacidade da moto",
                min_value=1,
                max_value=100,
                value=8,
                step=1,
            )

            motorcycle_speed = st.number_input(
                "Velocidade média da moto (km/h)",
                min_value=1.0,
                max_value=120.0,
                value=40.0,
                step=1.0,
            )

        with st.expander(
                "Veículo refrigerado",
                expanded=False,
        ):
            refrigerated_capacity = st.number_input(
                "Capacidade do veículo refrigerado",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
            )

            refrigerated_speed = st.number_input(
                "Velocidade média do veículo refrigerado (km/h)",
                min_value=1.0,
                max_value=120.0,
                value=35.0,
                step=1.0,
            )

        with st.expander(
                "Van operacional",
                expanded=False,
        ):
            van_capacity = st.number_input(
                "Capacidade da van",
                min_value=1,
                max_value=100,
                value=30,
                step=1,
            )

            van_speed = st.number_input(
                "Velocidade média da van (km/h)",
                min_value=1.0,
                max_value=120.0,
                value=32.0,
                step=1.0,
            )

        configured_fleet = build_configured_fleet(
            motorcycle_capacity=motorcycle_capacity,
            motorcycle_speed=motorcycle_speed,
            refrigerated_capacity=refrigerated_capacity,
            refrigerated_speed=refrigerated_speed,
            van_capacity=van_capacity,
            van_speed=van_speed,
        )

        with st.expander(
                "Resumo da frota",
                expanded=False,
        ):
            fleet_rows = [
                {
                    "Veículo": vehicle.name,
                    "Capacidade": vehicle.max_supply_capacity,
                    "Velocidade": vehicle.average_speed_kmh,
                    "Refrigerado": "Sim" if vehicle.is_refrigerated else "Não",
                }
                for vehicle in configured_fleet
            ]

            st.dataframe(
                fleet_rows,
                use_container_width=True,
                hide_index=True,
            )

    with st.sidebar.expander(
        "Operação da frota",
        expanded=False,
    ):
        route_start_time = st.text_input(
            "Horário de saída",
            value=settings.route_start_time,
            help="Horário inicial usado para simular as rotas dos veículos.",
        )

        average_vehicle_speed_kmh = st.number_input(
            "Velocidade média base (km/h)",
            min_value=1.0,
            max_value=120.0,
            value=float(settings.average_vehicle_speed_kmh),
            step=1.0,
            help=(
                "Velocidade média padrão usada apenas quando um veículo "
                "não possuir velocidade própria configurada."
            ),
        )

        max_hormonal_transport_minutes = st.number_input(
            "Prazo para medicamentos hormonais (min)",
            min_value=30,
            max_value=720,
            value=settings.max_hormonal_transport_minutes,
            step=30,
            help=(
                "Tempo máximo, em minutos, entre a saída da central "
                "e a entrega do medicamento hormonal."
            ),
        )

        max_route_duration_minutes = st.number_input(
            "Duração máxima por rota (min)",
            min_value=60,
            max_value=1440,
            value=settings.max_route_duration_minutes,
            step=30,
            help=(
                "Limite máximo individual para cada veículo. "
                "A duração operacional da frota considera a maior duração "
                "entre as rotas."
            ),
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
            value=float(settings.priority_penalty_weight),
            step=100.0,
        )

        time_window_penalty_weight = st.number_input(
            "Janelas de horário",
            min_value=0.0,
            value=float(settings.time_window_penalty_weight),
            step=50.0,
        )

        capacity_penalty_weight = st.number_input(
            "Capacidade dos veículos",
            min_value=0.0,
            value=float(settings.capacity_penalty_weight),
            step=100.0,
            help=(
                "Penaliza rotas em que a demanda atribuída ultrapassa "
                "a capacidade individual do veículo."
            ),
        )

        hormonal_transport_penalty_weight = st.number_input(
            "Prazo dos medicamentos hormonais",
            min_value=0.0,
            value=float(settings.hormonal_transport_penalty_weight),
            step=50.0,
        )

        route_duration_penalty_weight = st.number_input(
            "Duração máxima por rota",
            min_value=0.0,
            value=float(settings.route_duration_penalty_weight),
            step=50.0,
        )

        vehicle_compatibility_penalty_weight = st.number_input(
            "Compatibilidade veículo/carga",
            min_value=0.0,
            value=float(settings.vehicle_compatibility_penalty_weight),
            step=500.0,
            help=(
                "Penaliza medicamentos hormonais atribuídos a veículos "
                "sem refrigeração."
            ),
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

    run_settings = replace(
        settings,
        population_size=population_size,
        generations=generations,
        mutation_probability=mutation_probability,
        elitism_size=elitism_size,
        random_seed=int(random_seed) if use_random_seed else None,
        average_vehicle_speed_kmh=average_vehicle_speed_kmh,
        route_start_time=route_start_time,
        priority_penalty_weight=priority_penalty_weight,
        time_window_penalty_weight=time_window_penalty_weight,
        capacity_penalty_weight=capacity_penalty_weight,
        max_hormonal_transport_minutes=max_hormonal_transport_minutes,
        hormonal_transport_penalty_weight=hormonal_transport_penalty_weight,
        max_route_duration_minutes=max_route_duration_minutes,
        route_duration_penalty_weight=route_duration_penalty_weight,
        vehicle_compatibility_penalty_weight=vehicle_compatibility_penalty_weight,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_api_key=ollama_api_key or None,
        llm_temperature=llm_temperature,
    )

    return run_settings, run_optimization, configured_fleet


def render_settings_changed_warning() -> None:
    st.sidebar.warning(
        "Os parâmetros foram alterados. Execute novamente para atualizar a frota."
    )