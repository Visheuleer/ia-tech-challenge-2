# Otimização de Rotas para Atendimento Especializado à Mulher

Projeto desenvolvido para o Tech Challenge da Fase 2 da pós-graduação em Inteligência Artificial da FIAP.

A aplicação implementa um sistema de otimização de rotas para distribuição de medicamentos e atendimento especializado à mulher. A solução utiliza algoritmo genético, dados sintéticos, visualização em mapa com Streamlit/Folium e integração com LLM via API do Ollama para geração de relatórios operacionais.

## Projeto escolhido

Este repositório implementa o **Projeto 2: otimização de rotas para distribuição de medicamentos e atendimento especializado à mulher**.

O sistema parte de um problema inspirado no TSP e o adapta para um cenário de roteirização com restrições, considerando:

* prioridade dos atendimentos;
* janelas de horário;
* capacidade individual de cada veículo;
* prazo máximo de transporte para medicamentos hormonais;
* compatibilidade entre tipo de carga e veículo;
* duração máxima das rotas;
* distância total percorrida pela frota.

## Funcionalidades

A aplicação permite:

* carregar dados sintéticos de pontos de atendimento;
* otimizar rotas com algoritmo genético;
* configurar população, gerações, mutação, elitismo e seed aleatória;
* distribuir os atendimentos entre veículos com capacidades diferentes;
* considerar veículo refrigerado para transporte de medicamentos hormonais;
* ajustar pesos das penalidades da função fitness;
* visualizar as rotas otimizadas em mapa;
* identificar veículos por cor no mapa;
* visualizar prioridade das paradas diretamente nos marcadores;
* consultar legenda de veículos e prioridades;
* acompanhar métricas, penalidades e evolução do fitness;
* visualizar o roteiro consolidado da frota em tabela;
* visualizar resumo operacional por veículo;
* consultar resumo textual da solução;
* executar e comparar experimentos do algoritmo genético;
* gerar manual de instruções com LLM;
* gerar roteiro detalhado de visitas com LLM;
* responder perguntas em linguagem natural sobre a frota otimizada.

## Tipos de atendimento

O projeto considera quatro tipos de atendimento:

| Tipo                  | Prioridade |
| --------------------- | ---------: |
| Emergência obstétrica |          1 |
| Violência doméstica   |          2 |
| Medicamento hormonal  |          3 |
| Atendimento pós-parto |          4 |

Quanto menor o número, maior a prioridade.

## Frota utilizada

A aplicação considera uma frota heterogênea com três tipos de veículos:

| Veículo             | Capacidade | Refrigerado |
| ------------------- | ---------: | ----------- |
| Moto de atendimento |          8 | Não         |
| Veículo refrigerado |         20 | Sim         |
| Van operacional     |         30 | Não         |

Cada veículo recebe uma rota própria, com sequência de paradas, demanda atribuída, distância, duração e penalidades específicas.

## Tecnologias utilizadas

* Python
* Streamlit
* Folium
* Pandas
* NumPy
* Pytest
* Ollama API

## Estrutura do projeto

```text
ia-tech-challenge-2/
├── data/
│   ├── attendance_points.csv
│   └── distribution_center.csv
├── docs/
│   └── architecture/
├── experiments/
│   └── run_experiments.py
├── outputs/
│   └── experiments_results.csv
├── src/
│   ├── app.py
│   └── womens_health_route_optimizer/
│       ├── config/
│       ├── data/
│       ├── domain/
│       ├── llm/
│       ├── optimization/
│       ├── ui/
│       ├── utils/
│       └── visualization/
└── tests/
    ├── test_distance.py
    ├── test_fitness.py
    ├── test_fleet_optimization.py
    ├── test_loaders.py
    └── test_simulation.py
```

## Diagramas de arquitetura

Os diagramas do projeto estão disponíveis em:

```text
docs/architecture/
```

Diagramas incluídos:

* arquitetura geral do sistema;
* fluxo do algoritmo genético;
* modelo de domínio e dados;
* fluxo de integração com LLM.

### Arquitetura geral

![Arquitetura geral do sistema](docs/architecture/arquitetura_geral.svg)

### Fluxo do algoritmo genético

![Fluxo do algoritmo genético](docs/architecture/fluxo_algoritmo_genetico.svg)

### Modelo de domínio e dados

![Modelo de domínio e dados](docs/architecture/modelo_dados.svg)

### Fluxo da LLM

![Fluxo de integração com LLM](docs/architecture/fluxo_llm.svg)

A explicação detalhada desses diagramas será apresentada no relatório técnico do projeto.

## Instalação

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual.

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

Instale o projeto em modo editável:

```bash
pip install -e ".[dev]"
```

## Configuração da API do Ollama

A aplicação utiliza a API do Ollama para geração dos relatórios com LLM.

Crie um arquivo `.env` na raiz do projeto ou configure a variável de ambiente:

```env
OLLAMA_API_KEY=your_ollama_api_key_here
```

Também é possível informar a API key diretamente pela sidebar da aplicação.

O arquivo `.env.example` serve apenas como referência e não deve conter chaves reais.

## Executar a aplicação

Para iniciar a interface:

```bash
streamlit run src/app.py
```

A aplicação será aberta no navegador.

Na sidebar, é possível configurar:

* tamanho da população;
* número de gerações;
* probabilidade de mutação;
* elitismo;
* seed aleatória;
* velocidade média;
* horário de saída;
* pesos das penalidades;
* limites operacionais;
* URL, modelo e API key do Ollama.

## Executar os experimentos

Para gerar os resultados comparativos dos experimentos:

```bash
python experiments/run_experiments.py
```

Os resultados serão salvos em:

```text
outputs/experiments_results.csv
```

Depois disso, a aba **Experimentos** da aplicação exibirá a tabela e os gráficos comparativos.

## Executar os testes

Para rodar os testes automatizados:

```bash
pytest
```

Os testes cobrem:

* carregamento dos dados;
* cálculo de distância;
* função fitness;
* simulação de rotas;
* operadores da frota;
* geração da população inicial;
* crossover e mutação;
* avaliação da solução otimizada;
* compatibilidade entre veículo e tipo de carga.

## Relatório Técnico

A explicação completa da solução está no [relatório técnico](docs/relatorio_tecnico.pdf), que detalha:

* problema escolhido;
* modelagem dos dados sintéticos;
* adaptação do problema de roteirização;
* representação genética;
* função fitness;
* restrições implementadas;
* visualização da solução;
* integração com LLM;
* experimentos;
* resultados;
* limitações;
* considerações éticas.

## Licença

Projeto desenvolvido para fins acadêmicos.
