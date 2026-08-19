class Constants:
    DEFAULT_MODEL = "gpt-4.1-mini"
    DEFAULT_TEMPERATURE = 0.5
    DEFAULT_MAX_ITERATION = 3
    DEFAULT_MAX_TOOL_CALLS = 3
    DEFAULT_MAX_HISTORY =5
    ERROR_GENERIC = "Something went wrong. Please try again."
    ERROR_MISSING_API_KEY = "OPENAI_API_KEY is required but was not provided."
    ERROR_NO_CHOICES = "No choices returned from OpenAI API."
    ERROR_TOOL_EXECUTION = "Error executing tool: {e}"
    ERROR_TOOL_NOT_FOUND = "Tool '{func_name}' not found."
    ERROR_API_CONNECTION = "Failed to connect to OpenAI API: {e}"
    ERROR_API_GENERATION = "OpenAI API failed to generate a response: {e}"
    ERROR_UNEXPECTED = "Unexpected error: {e}"
