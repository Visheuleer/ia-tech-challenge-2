import os
from abc import ABC, abstractmethod

from ollama import Client, ResponseError

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
        self.api_key = (
            app_settings.ollama_api_key
            or os.getenv("OLLAMA_API_KEY")
        )

        if not self.api_key:
            raise RuntimeError(
                "A API key do Ollama não foi configurada. "
                "Informe a chave na sidebar ou na variável OLLAMA_API_KEY."
            )

        self.client = Client(
            host=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    def generate(self, prompt: str) -> str:
        try:
            stream = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Forneça somente a resposta final solicitada. "
                            "Não apresente raciocínio interno."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=True,
                think="low",
                options={
                    "temperature": self.temperature,
                    "num_predict": 4096,
                },
            )

            content_parts: list[str] = []
            thinking_parts: list[str] = []
            final_done_reason: str | None = None

            for part in stream:
                message = part.get("message", {})

                content = message.get("content", "")
                thinking = message.get("thinking", "")

                if content:
                    content_parts.append(content)

                if thinking:
                    thinking_parts.append(thinking)

                if part.get("done"):
                    final_done_reason = part.get("done_reason")

            generated_text = "".join(content_parts).strip()

            if not generated_text:
                raise RuntimeError(
                    "Ollama encerrou a geração sem conteúdo final. "
                    f"Motivo: {final_done_reason or 'desconhecido'} | "
                    f"Fragmentos de conteúdo: {len(content_parts)} | "
                    f"Fragmentos de raciocínio: {len(thinking_parts)}"
                )

            return generated_text

        except ResponseError as error:
            raise RuntimeError(
                f"Erro retornado pelo Ollama: {error.error}"
            ) from error

        except RuntimeError:
            raise

        except Exception as error:
            raise RuntimeError(
                "Falha inesperada ao consultar a API do Ollama: "
                f"{type(error).__name__}: {error}"
            ) from error


def get_llm_provider(
    app_settings: Settings = settings,
) -> LLMProvider:
    return OllamaLLMProvider(app_settings)