"""
SBI Vishwas — AI Provider Abstraction

Provider factory that supports Gemini, OpenAI, Anthropic, and Ollama.
Providers are selected through configuration only — never tightly coupled.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from src.config.settings import AIProvider, get_settings

logger = structlog.get_logger(__name__)


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: str
    structured_output: dict[str, Any] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    finish_reason: str | None = None


class BaseProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def get_chat_model(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
    ) -> BaseChatModel:
        """Get a LangChain chat model instance."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        ...


class GeminiProvider(BaseProvider):
    """Google Gemini provider implementation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")

    def get_chat_model(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
    ) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = model or self.settings.gemini_model
        temp = temperature if temperature is not None else self.settings.ai_temperature
        tokens = max_tokens or self.settings.ai_max_tokens

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.settings.gemini_api_key,
            temperature=temp,
            max_output_tokens=tokens,
            convert_system_message_to_human=False,
        )

        if structured_output:
            llm = llm.with_structured_output(structured_output)

        return llm

    def get_provider_name(self) -> str:
        return "gemini"


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

    def get_chat_model(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
    ) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        model_name = model or self.settings.openai_model
        temp = temperature if temperature is not None else self.settings.ai_temperature
        tokens = max_tokens or self.settings.ai_max_tokens

        llm = ChatOpenAI(
            model=model_name,
            api_key=self.settings.openai_api_key,
            organization=self.settings.openai_org_id,
            temperature=temp,
            max_tokens=tokens,
        )

        if structured_output:
            llm = llm.with_structured_output(structured_output)

        return llm

    def get_provider_name(self) -> str:
        return "openai"


class AnthropicProvider(BaseProvider):
    """Anthropic (Claude) provider implementation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

    def get_chat_model(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
    ) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        model_name = model or self.settings.anthropic_model
        temp = temperature if temperature is not None else self.settings.ai_temperature
        tokens = max_tokens or self.settings.ai_max_tokens

        llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=self.settings.anthropic_api_key,
            temperature=temp,
            max_tokens=tokens,
        )

        if structured_output:
            llm = llm.with_structured_output(structured_output)

        return llm

    def get_provider_name(self) -> str:
        return "anthropic"


class OllamaProvider(BaseProvider):
    """Ollama (local) provider implementation."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_chat_model(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
    ) -> BaseChatModel:
        from langchain_community.chat_models import ChatOllama

        model_name = model or self.settings.ollama_model
        temp = temperature if temperature is not None else self.settings.ai_temperature

        llm = ChatOllama(
            model=model_name,
            base_url=self.settings.ollama_base_url,
            temperature=temp,
            num_predict=max_tokens or self.settings.ai_max_tokens,
        )

        if structured_output:
            llm = llm.with_structured_output(structured_output)

        return llm

    def get_provider_name(self) -> str:
        return "ollama"


class ProviderFactory:
    """
    Factory that creates LLM providers based on configuration.

    Usage:
        factory = ProviderFactory()
        provider = factory.get_provider()  # Uses default from settings
        provider = factory.get_provider("openai")  # Explicit provider
        llm = provider.get_chat_model(temperature=0.0)
    """

    _providers: dict[str, type[BaseProvider]] = {
        AIProvider.GEMINI.value: GeminiProvider,
        AIProvider.OPENAI.value: OpenAIProvider,
        AIProvider.ANTHROPIC.value: AnthropicProvider,
        AIProvider.OLLAMA.value: OllamaProvider,
    }

    _instances: dict[str, BaseProvider] = {}

    @classmethod
    def get_provider(cls, provider_name: str | None = None) -> BaseProvider:
        """
        Get a provider instance by name. Defaults to settings.ai_default_provider.
        Instances are cached for reuse.
        """
        settings = get_settings()
        name = provider_name or settings.ai_default_provider.value

        if name not in cls._instances:
            provider_class = cls._providers.get(name)
            if not provider_class:
                raise ValueError(
                    f"Unknown AI provider: {name}. "
                    f"Available: {list(cls._providers.keys())}"
                )
            try:
                cls._instances[name] = provider_class()
                logger.info("AI provider initialized", provider=name)
            except ValueError as e:
                logger.warning(f"Failed to initialize {name} provider: {e}")
                raise

        return cls._instances[name]

    @classmethod
    def get_chat_model(
        cls,
        provider_name: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        structured_output: type[BaseModel] | None = None,
        available_tools: list[str] | None = None,
    ) -> BaseChatModel:
        """Convenience method: get a chat model directly, with optional tool binding."""
        provider = cls.get_provider(provider_name)
        chat_model = provider.get_chat_model(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            structured_output=structured_output,
        )

        # Bind tools if requested and if structured_output is not used
        # (Usually models struggle with both structured output and tools simultaneously)
        if available_tools and not structured_output:
            try:
                from src.agents.tools.core import tool_registry
                lc_tools = tool_registry.get_all_langchain_tools(available_tools)
                if lc_tools:
                    chat_model = chat_model.bind_tools(lc_tools)
            except Exception as e:
                logger.error("Failed to bind tools to model", error=str(e))

        return chat_model

    @classmethod
    def get_embedding_model(
        cls,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> Embeddings:
        """
        Get an embedding model from the specified provider.
        """
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_openai import OpenAIEmbeddings

        settings = get_settings()
        provider = provider_name or settings.ai_default_provider.value
        model_name = model or settings.embedding_model

        if provider == "gemini":
            return GoogleGenerativeAIEmbeddings(
                model=f"models/{model_name}",
                google_api_key=settings.gemini_api_key,
            )
        elif provider == "openai":
            return OpenAIEmbeddings(
                model=model_name,
                openai_api_key=settings.openai_api_key,
            )
        else:
            # Fallback to Gemini for embeddings if provider doesn't support it directly
            logger.warning(f"Embeddings not configured for {provider}, falling back to Gemini")
            return GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.gemini_api_key,
            )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a custom provider (for extensibility)."""
        cls._providers[name] = provider_class
        logger.info("Custom AI provider registered", name=name)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached provider instances (for testing)."""
        cls._instances.clear()
