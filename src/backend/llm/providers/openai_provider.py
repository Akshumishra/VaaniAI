import logging
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError, APIConnectionError

from src.backend.llm.exceptions import LLMConnectionError, LLMGenerationError
from src.backend.core.setting import Settings
from src.backend.core.constants import LLM
from src.backend.core.constants import ErrorMessages

logger = logging.getLogger(__name__)


class OpenAIProvider():
    """LLM Provider implementation using the OpenAI API."""

    def __init__(self, model: str = LLM.DEFAULT_MODEL):
        self.api_key = Settings.OPENAI_API_KEY
        self.model = model

        if not self.api_key:
            logger.error("OpenAI API Key is missing.")
            raise ValueError(ErrorMessages.MISSING_OPENAI_API_KEY)

        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"OpenAIProvider initialized with model: {self.model}")

    def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        max_tokens = kwargs.get("max_tokens", LLM.MAX_TOKENS)
        temperature = kwargs.get("temperature")

        try:
            tools = kwargs.get("tools")
            tool_map = kwargs.get("tool_map", {})

            while True:
                logger.debug(f"Sending {len(messages)} messages to OpenAI API.")
                call_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_completion_tokens": max_tokens,
                }

                if temperature is not None:
                    call_kwargs["temperature"] = temperature

                if tools:
                    call_kwargs["tools"] = tools

                response = self.client.chat.completions.create(**call_kwargs)

                if not response.choices:
                    raise LLMGenerationError(ErrorMessages.NO_LLM_CHOICES)

                message = response.choices[0].message

                if getattr(message, "tool_calls", None):
                    messages.append(message.model_dump(exclude_none=True))

                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = tool_call.function.arguments

                        logger.info(
                            f"LLM called tool: {func_name} with args: {func_args}"
                        )

                        if func_name in tool_map:
                            import json

                            try:
                                args_dict = json.loads(func_args)
                                tool_result = tool_map[func_name](**args_dict)
                            except Exception as e:
                                tool_result = ErrorMessages.TOOL_EXECUTION_FAILED.format(e=e)
                        else:
                            tool_result = ErrorMessages.TOOL_NOT_FOUND.format(func_name=func_name)

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": str(tool_result),
                            }
                        )

                    continue

                return message.content.strip() if message.content else ""

        except APIConnectionError as e:
            logger.error(f"Connection error to OpenAI API: {e}")
            raise LLMConnectionError(ErrorMessages.API_CONNECTION_FAILED.format(e=e))
        except OpenAIError as e:
            logger.error(f"OpenAI API Error: {e}")
            raise LLMGenerationError(ErrorMessages.API_GENERATION_FAILED.format(e=e))
        except Exception as e:
            logger.exception("Unexpected error during OpenAI generation.")
            raise LLMGenerationError(ErrorMessages.UNEXPECTED.format(e=e))
