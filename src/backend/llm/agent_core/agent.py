import json
from openai import OpenAI
from typing import List, Optional
from openai import AsyncOpenAI
from src.backend.core.setting import Settings
from src.backend.llm.agent_core.constants import Constants
from src.backend.llm.agent_core.tools import Tool


class Agent:

    def __init__(
        self,
        system_prompt: str,
        model: str = Constants.DEFAULT_MODEL,
        temperature: float = Constants.DEFAULT_TEMPERATURE,
        max_iteration: int = Constants.DEFAULT_MAX_ITERATION,
        max_tool_call: int = Constants.DEFAULT_MAX_TOOL_CALLS,
    ):
        self.client = OpenAI(api_key=Settings.OPENAI_API_KEY)
        self.client_async = AsyncOpenAI(api_key=Settings.OPENAI_API_KEY)
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_iteration = max_iteration
        self.max_tool_call = max_tool_call
        self.tools = {}

    def add_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def on_tool_result(self, tool_name: str, args: dict, result: dict):
        pass

    def _execute_tool(self, name: str, args: Optional[dict]):
        if args:
            return self.tools[name].execute(**args)
        return self.tools[name].execute()

    def _call_llm(self, chat_history: List[dict]):
        tools_list = (
            [tool.schema() for tool in self.tools.values()] if self.tools else None
        )

        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": chat_history,
        }
        if tools_list:
            kwargs["tools"] = tools_list
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(**kwargs)

    def _format_chat_history(self, chat_history: list[dict]) -> List[dict]:
        history = [
            {"role": "system", "content": self.system_prompt},
        ]
        if isinstance(chat_history, list):
            history.extend(chat_history)
        else:
            history.append(chat_history)

        return history

    def invoke(self, chat_history=None):
        if chat_history is None:
            chat_history = []
        formatted_history = self._format_chat_history(chat_history)
        tool_calls = []

        for _ in range(self.max_iteration):
            response = self._call_llm(formatted_history)
            message = response.choices[0].message

            if message.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
                formatted_history.append(assistant_msg)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    args = (
                        json.loads(tool_call.function.arguments)
                        if tool_call.function.arguments
                        else {}
                    )

                    result = self._execute_tool(tool_name, args)
                    self.on_tool_result(tool_name, args, result)

                    tool_output_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result),
                    }
                    formatted_history.append(tool_output_message)

                    tool_input = {
                        "type": "function_call",
                        "name": tool_name,
                        "arguments": json.dumps(args),
                        "call_id": tool_call.id,
                    }
                    tool_output = {
                        "type": "function_call_output",
                        "call_id": tool_call.id,
                        "output": json.dumps(result),
                    }
                    tool_calls.append({"input": tool_input, "output": tool_output})
            else:
                assistant_text = message.content or ""
                return assistant_text, tool_calls

        return Constants.ERROR_GENERIC, tool_calls
