from womens_health_route_optimizer.config import Settings, settings
from womens_health_route_optimizer.domain import DistributionCenter, Route
from womens_health_route_optimizer.llm.prompts import (
    build_instruction_manual_prompt,
    build_question_prompt,
    build_visit_plan_prompt,
)
from womens_health_route_optimizer.llm.providers import get_llm_provider


class RouteReportGenerator:

    def __init__(self, app_settings: Settings = settings) -> None:
        self.app_settings = app_settings
        self.provider = get_llm_provider(app_settings)

    def generate_instruction_manual(
        self,
        route: Route,
        distribution_center: DistributionCenter,
    ) -> str:
        prompt = build_instruction_manual_prompt(
            route=route,
            distribution_center=distribution_center,
        )

        return self.provider.generate(prompt)

    def generate_visit_plan(
        self,
        route: Route,
        distribution_center: DistributionCenter,
    ) -> str:
        prompt = build_visit_plan_prompt(
            route=route,
            distribution_center=distribution_center,
        )

        return self.provider.generate(prompt)

    def answer_question(
        self,
        route: Route,
        distribution_center: DistributionCenter,
        question: str,
    ) -> str:
        prompt = build_question_prompt(
            route=route,
            distribution_center=distribution_center,
            question=question,
        )

        return self.provider.generate(prompt)