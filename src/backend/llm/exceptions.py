class LLMError(Exception):
    """Base exception for LLM module errors."""
    pass

class LLMConnectionError(LLMError):
    """Raised when there is an issue connecting to the LLM API."""
    pass

class LLMGenerationError(LLMError):
    """Raised when the LLM fails to generate a response."""
    pass
