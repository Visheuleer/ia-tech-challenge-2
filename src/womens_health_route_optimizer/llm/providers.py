import json
from abc import ABC, abstractmethod
from urllib.error import URLError
from urllib.request import Request, urlopen

from womens_health_route_optimizer.config import Settings, settings


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):

    def generate(self, prompt: str) -> str:
        return (
            "## Resposta gerada em modo mock\n\n"
            "Esta resposta simula a integração com uma LLM local. "
            "Para executar com um modelo open-source real, altere o provedor para Ollama.\n\n"
            "### Orientações operacionais gerais\n\n"
            "1. Priorize atendimentos de emergência obstétrica conforme a ordem definida pela rota.\n"
            "2. Em casos relacionados à violência doméstica, mantenha discrição, postura acolhedora "
            "e atenção a protocolos de segurança.\n"
            "3. Em entregas de medicamentos hormonais, preserve as condições adequadas de transporte "
            "e registre o recebimento.\n"
            "4. Em atendimentos pós-parto, respeite a janela de horário e adote comunicação cuidadosa.\n\n"
            "### Observação\n\n"
            "O conteúdo acima é uma saída determinística para fins de demonstração e fallback técnico."
        )


class OllamaLLMProvider(LLMProvider):

    def __init__(self, app_settings: Settings = settings) -> None:
        self.base_url = app_settings.ollama_base_url.rstrip("/")
        self.model = app_settings.ollama_model
        self.temperature = app_settings.llm_temperature

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=120) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except URLError as error:
            raise RuntimeError(
                "Não foi possível conectar ao Ollama. "
                "Verifique se o Ollama está em execução e se o modelo foi baixado."
            ) from error

        generated_text = response_data.get("response")

        if not generated_text:
            raise RuntimeError("Ollama não retornou uma resposta válida.")

        return generated_text


def get_llm_provider(app_settings: Settings = settings) -> LLMProvider:

    provider = app_settings.llm_provider.lower().strip()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "ollama":
        return OllamaLLMProvider(app_settings)

    raise ValueError(f"Unsupported LLM provider: {app_settings.llm_provider}")