from typing import Dict, Type, Callable
from app.services.llm.base import BaseLLMProvider


class ProviderRegistryException(Exception):
    """Custom exception for registry errors."""
    pass


class ProviderRegistry:
    """
    Registry for managing available LLM providers.
    
    Provides dictionary-backed dynamic registration and retrieval of
    BaseLLMProvider subclasses.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, Type[BaseLLMProvider]] = {}

    def register(self, name: str) -> Callable[[Type[BaseLLMProvider]], Type[BaseLLMProvider]]:
        """
        Decorator to register a provider class.
        
        Args:
            name: The unique string identifier for the provider (e.g. 'openai').
            
        Returns:
            A decorator function that registers the provider class.
        """
        def decorator(cls: Type[BaseLLMProvider]) -> Type[BaseLLMProvider]:
            self.register_provider_class(name, cls)
            return cls
        return decorator

    def register_provider_class(self, name: str, cls: Type[BaseLLMProvider]) -> None:
        """
        Manually register a provider class.
        
        Args:
            name: The unique string identifier for the provider.
            cls: The provider class inheriting from BaseLLMProvider.
            
        Raises:
            ProviderRegistryException: If the class is not a subclass of BaseLLMProvider
                                       or if the name is empty.
        """
        if not name or not name.strip():
            raise ProviderRegistryException("Provider name cannot be empty.")
        
        if not issubclass(cls, BaseLLMProvider):
            raise ProviderRegistryException(
                f"Cannot register '{cls.__name__}'. It must be a subclass of BaseLLMProvider."
            )
            
        normalized_name = name.strip().lower()
        self._providers[normalized_name] = cls

    def get_provider_class(self, name: str) -> Type[BaseLLMProvider]:
        """
        Retrieve a registered provider class by name.
        
        Args:
            name: The unique identifier of the provider.
            
        Returns:
            The registered provider class.
            
        Raises:
            ProviderRegistryException: If the provider is not registered.
        """
        if not name or not name.strip():
            raise ProviderRegistryException("Provider name cannot be empty.")
            
        normalized_name = name.strip().lower()
        cls = self._providers.get(normalized_name)
        if not cls:
            raise ProviderRegistryException(
                f"LLM Provider '{name}' is not registered in the registry. "
                f"Available providers: {self.list_providers()}"
            )
        return cls

    def list_providers(self) -> list[str]:
        """
        Return a list of all registered provider names.
        """
        return list(self._providers.keys())


# Global singleton registry instance
provider_registry = ProviderRegistry()
