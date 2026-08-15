from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generates a response from the LLM based on a list of messages.

        Args:
            messages: A list of message dictionaries. 
                      Format: [{'role': 'system'/'user'/'assistant', 'content': '...'}, ...]
            **kwargs: Additional parameters (e.g., temperature, max_tokens).

        Returns:
            The text response from the LLM.
            
        Raises:
            LLMConnectionError: If connection to the provider fails.
            LLMGenerationError: If the provider fails to generate a valid response.
        """
        pass
