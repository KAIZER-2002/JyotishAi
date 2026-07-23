from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Base interface for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier."""
        ...

    @abstractmethod
    async def generate(
        self,
        *,
        message: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            message: User message.
            model: Model identifier.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature.
            **kwargs: Provider-specific options.

        Returns:
            Generated response text.
        """
        ...