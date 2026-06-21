from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain.models import (
    DistributionCenter,
    FleetSolution,
)
from womens_health_route_optimizer.llm.prompts import (
    build_instruction_manual_prompt,
    build_route_question_prompt,
    build_visit_plan_prompt,
)
from womens_health_route_optimizer.llm.providers import (
    LLMProvider,
    get_llm_provider,
)


class RouteReportGenerator:
    """
    Serviço responsável por gerar relatórios e respostas sobre
    uma solução de frota otimizada.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        provider: LLMProvider | None = None,
    ) -> None:
        self.app_settings = app_settings
        self.provider = provider or get_llm_provider(app_settings)

    def generate_instruction_manual(
        self,
        solution: FleetSolution,
        distribution_center: DistributionCenter,
    ) -> str:
        prompt = build_instruction_manual_prompt(
            solution=solution,
            distribution_center=distribution_center,
            app_settings=self.app_settings,
        )

        return self.provider.generate(prompt)

    def generate_visit_plan(
        self,
        solution: FleetSolution,
        distribution_center: DistributionCenter,
    ) -> str:
        prompt = build_visit_plan_prompt(
            solution=solution,
            distribution_center=distribution_center,
            app_settings=self.app_settings,
        )

        return self.provider.generate(prompt)

    def answer_question(
        self,
        solution: FleetSolution,
        distribution_center: DistributionCenter,
        question: str,
    ) -> str:
        prompt = build_route_question_prompt(
            solution=solution,
            distribution_center=distribution_center,
            question=question,
            app_settings=self.app_settings,
        )

        return self.provider.generate(prompt)