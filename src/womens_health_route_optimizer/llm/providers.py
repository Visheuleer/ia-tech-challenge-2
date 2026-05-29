import json
import os
from abc import ABC, abstractmethod
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from womens_health_route_optimizer.config import Settings, settings


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaLLMProvider(LLMProvider):

    def __init__(self, app_settings: Settings = settings) -> None:
        self.base_url = app_settings.ollama_base_url.rstrip("/")
        self.model = app_settings.ollama_model
        self.temperature = app_settings.llm_temperature
        self.api_key = app_settings.ollama_api_key or os.getenv("OLLAMA_API_KEY")

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

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=180) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            error_body = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Erro HTTP ao chamar Ollama API: {error.code}. "
                f"Detalhes: {error_body}"
            ) from error
        except URLError as error:
            raise RuntimeError(
                "Não foi possível conectar à API do Ollama. "
                "Verifique a URL, a conexão de rede e a API key."
            ) from error

        generated_text = response_data.get("response")

        if not generated_text:
            raise RuntimeError("Ollama API não retornou uma resposta válida.")

        return generated_text


def get_llm_provider(app_settings: Settings = settings) -> LLMProvider:
    return OllamaLLMProvider(app_settings)