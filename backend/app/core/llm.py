from functools import lru_cache
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings

Provider = Literal["openai", "anthropic", "google", "xai", "ollama"]

OLLAMA_MODEL_IDS = frozenset({"qwen3.6-27b-fable5"})


def resolve_ollama_model(model: str) -> str:
    normalized = model.lower()
    if normalized.startswith("ollama:"):
        return model.split(":", 1)[1]
    return model


def resolve_provider(model: str) -> Provider:
    normalized = model.lower()
    if normalized.startswith("ollama:") or normalized in OLLAMA_MODEL_IDS or normalized.startswith("qwen3.6"):
        return "ollama"
    if normalized.startswith("claude"):
        return "anthropic"
    if normalized.startswith("gemini"):
        return "google"
    if normalized.startswith("grok"):
        return "xai"
    return "openai"


class LLMFactory:
    """Create and cache chat models based on registry llm_model values."""

    def __init__(self) -> None:
        self._cache: dict[str, BaseChatModel] = {}

    def get(self, model: str | None = None) -> BaseChatModel:
        resolved_model = model or settings.default_model
        if resolved_model not in self._cache:
            self._cache[resolved_model] = self._create(resolved_model)
        return self._cache[resolved_model]

    def get_default(self) -> BaseChatModel:
        return self.get(settings.default_model)

    def get_supervisor(self) -> BaseChatModel:
        return self.get(settings.supervisor_model or settings.default_model)

    def _create(self, model: str) -> BaseChatModel:
        provider = resolve_provider(model)
        if provider == "ollama":
            if not settings.ollama_enabled:
                raise RuntimeError(
                    f"OLLAMA_ENABLED=true is required for local model '{model}'. "
                    "Set it in backend .env and ensure Ollama is running."
                )
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=resolve_ollama_model(model),
                base_url=settings.ollama_base_url,
                temperature=0.2,
            )

        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    f"ANTHROPIC_API_KEY is required for model '{model}'. "
                    "Set it in .env before running this agent."
                )
            return ChatAnthropic(
                model=model,
                api_key=settings.anthropic_api_key,
                temperature=0.2,
            )

        if provider == "google":
            google_key = settings.google_api_key or settings.gemini_api_key
            if not google_key:
                raise RuntimeError(
                    f"GOOGLE_API_KEY or GEMINI_API_KEY is required for model '{model}'. "
                    "Set it in .env before running this agent."
                )
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_key,
                temperature=0.2,
            )

        if provider == "xai":
            if not settings.xai_api_key:
                raise RuntimeError(
                    f"XAI_API_KEY is required for model '{model}'. "
                    "Set it in .env before running this agent."
                )
            from langchain_xai import ChatXAI

            return ChatXAI(
                model=model,
                xai_api_key=settings.xai_api_key,
                temperature=0.2,
            )

        if not settings.openai_api_key:
            raise RuntimeError(
                f"OPENAI_API_KEY is required for model '{model}'. "
                "Set it in .env before running this agent."
            )
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )


def has_llm_provider_configured() -> bool:
    return bool(
        settings.openai_api_key
        or settings.anthropic_api_key
        or settings.google_api_key
        or settings.gemini_api_key
        or settings.xai_api_key
        or settings.ollama_enabled
    )


@lru_cache
def get_llm_factory() -> LLMFactory:
    if not has_llm_provider_configured():
        raise RuntimeError(
            "At least one LLM provider is required. "
            "Set API keys and/or OLLAMA_ENABLED=true in .env."
        )
    return LLMFactory()


def get_llm() -> BaseChatModel:
    """Backward-compatible default LLM accessor."""
    return get_llm_factory().get_default()