class LLMException(Exception):
    """
    Base exception for all LLM-related errors.
    
    All exceptions originating from the LLM service layer should inherit from this class.
    """
    pass


class ProviderException(LLMException):
    """
    Base exception for LLM provider-specific errors.
    
    Use this class to catch errors that are specific to the underlying LLM API 
    (e.g., API timeouts, authentication failures, or rate limits).
    """
    pass


class GeminiProviderException(ProviderException):
    """Exception raised for errors related to the Google Gemini provider."""
    pass


class OpenAIProviderException(ProviderException):
    """Exception raised for errors related to the OpenAI provider."""
    pass


class AnthropicProviderException(ProviderException):
    """Exception raised for errors related to the Anthropic provider."""
    pass


class OpenRouterProviderException(ProviderException):
    """Exception raised for errors related to the OpenRouter provider."""
    pass


class LocalProviderException(ProviderException):
    """Exception raised for errors related to local LLM providers (e.g., Ollama)."""
    pass


class AstrologyProviderException(ProviderException):
    """Exception raised for errors related to the Astrology-specific provider."""
    pass
