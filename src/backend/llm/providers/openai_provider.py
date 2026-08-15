import logging
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError, APIConnectionError

from src.backend.llm.interfaces import LLMProvider
from src.backend.llm.exceptions import LLMConnectionError, LLMGenerationError
from src.backend.core.setting import Settings
from src.backend.core.constants import LLM

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """LLM Provider implementation using the OpenAI API."""

    def __init__(self, api_key: str = None, model: str = LLM.DEFAULT_MODEL):
        """
        Initializes the OpenAI provider.

        Args:
            api_key: The OpenAI API key. If None, it will be fetched from Settings.
            model: The name of the model to use (e.g., 'gpt-4o-mini').
        """
        self.api_key = api_key or Settings.OPENAI_API_KEY
        self.model = model
        
        if not self.api_key:
            logger.error("OpenAI API Key is missing.")
            raise ValueError("OPENAI_API_KEY is required but was not provided.")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"OpenAIProvider initialized with model: {self.model}")

    def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generates a response from the OpenAI LLM based on a list of messages.

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
        max_tokens = kwargs.get('max_tokens', LLM.MAX_TOKENS)

        try:
            logger.debug(f"Sending {len(messages)} messages to OpenAI API.")
            
            call_kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
            }
                
            response = self.client.chat.completions.create(**call_kwargs)
            
            if not response.choices:
                raise LLMGenerationError("No choices returned from OpenAI API.")
                
            return response.choices[0].message.content.strip()

        except APIConnectionError as e:
            logger.error(f"Connection error to OpenAI API: {e}")
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {e}")
        except OpenAIError as e:
            logger.error(f"OpenAI API Error: {e}")
            raise LLMGenerationError(f"OpenAI API failed to generate a response: {e}")
        except Exception as e:
            logger.exception("Unexpected error during OpenAI generation.")
            raise LLMGenerationError(f"Unexpected error: {e}")
