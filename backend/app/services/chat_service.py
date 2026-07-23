from typing import Optional
from app.services.llm.manager import llm_manager
from app.exceptions.llm import ProviderException, LLMException


class ChatService:
    """
    Service layer for handling chat interactions.
    
    Orchestrates the flow between the API layer and the LLM provider system.
    """

    async def send_message(
        self,
        provider_name: str,
        model: str,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Processes a chat message using the specified LLM provider.
        
        Args:
            provider_name: The unique identifier of the LLM provider to use.
            model: The specific model identifier for the provider.
            message: The user's input message.
            system_prompt: Optional system instructions to guide the model.
            temperature: Sampling temperature for the generation.
            
        Returns:
            The generated response text from the LLM.
            
        Raises:
            ProviderException: If the provider is not registered or the API call fails.
            LLMException: If an unexpected failure occurs.
        """
        # Retrieve the provider instance from the manager
        provider = llm_manager.get_provider(provider_name)
        
        try:
            # Delegate generation directly to the provider instance
            return await provider.generate(
                message=message,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature
            )
        except ProviderException:
            # Let ProviderException propagate naturally to the API layer
            raise
        except Exception as e:
            # Wrap unexpected errors in the base LLMException
            raise LLMException(f"Unexpected error in ChatService: {str(e)}") from e
