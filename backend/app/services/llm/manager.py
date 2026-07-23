from typing import Dict, Optional
from app.services.llm.base import BaseLLMProvider
from app.services.llm.registry import provider_registry, ProviderRegistryException


class LLMManager:
    """
    Manager for LLM providers.
    
    Handles the dynamic retrieval and instantiation of LLM providers
    using the ProviderRegistry.
    """

    def __init__(self) -> None:
        # Cache for instantiated provider instances
        self._provider_instances: Dict[str, BaseLLMProvider] = {}

    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Retrieves an instance of the specified LLM provider.
        
        Args:
            provider_name: The unique identifier of the provider.
            
        Returns:
            An instance of a BaseLLMProvider subclass.
            
        Raises:
            ProviderRegistryException: If the provider is not registered.
        """
        normalized_name = provider_name.strip().lower()
        
        if normalized_name in self._provider_instances:
            return self._provider_instances[normalized_name]
        
        try:
            provider_cls = provider_registry.get_provider_class(normalized_name)
            instance = provider_cls()
            self._provider_instances[normalized_name] = instance
            return instance
        except ProviderRegistryException:
            raise

    async def generate(
        self,
        provider_name: str,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generates a response using the specified LLM provider.
        
        Args:
            provider_name: The unique identifier of the provider to use.
            message: The user prompt.
            model: The specific model identifier for the provider.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature.
            
        Returns:
            The generated text response.
            
        Raises:
            ProviderRegistryException: If the provider is not registered.
        """
        provider = self.get_provider(provider_name)
        return await provider.generate(
            message=message,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature
        )

    def clear_cache(self) -> None:
        """Clears the cached provider instances."""
        self._provider_instances.clear()


# Global singleton manager instance
llm_manager = LLMManager()
