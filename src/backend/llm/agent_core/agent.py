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
        self.client = OpenAI(api_key=Settings.OPEN_API_KEY)
        self.client_async = AsyncOpenAI(api_key=Settings.OPEN_API_KEY)
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

    def _call_llm(self, chat_history: List[dict], stream: bool = False):
        return self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=chat_history,
            tools=[tool.schema() for tool in self.tools.values()],
            tool_choice="auto",
            stream=stream,
        )

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
        chat_history = self._format_chat_history(chat_history)
        tool_calls = []

        for _ in range(self.max_iteration):
            response = self._call_llm(chat_history)
            assistant_text = ""

            for item in response.output:

                if item.type == "function_call":
                    tool_name = item.name
                    args = json.loads(item.arguments) if item.arguments else {}

                    tool_input = {
                        "type": "function_call",
                        "name": tool_name,
                        "arguments": json.dumps(args),
                        "call_id": item.call_id,
                    }
                    chat_history.append(tool_input)

                    result = self._execute_tool(tool_name, args)

                    self.on_tool_result(tool_name, args, result)

                    tool_output = {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                    chat_history.append(tool_output)
                    tool_calls.append({"input": tool_input, "output": tool_output})

                elif item.type == "message":
                    for part in item.content:
                        if part.type == "output_text":
                            assistant_text += part.text

            if assistant_text:
                return assistant_text, tool_calls

        return Constants.ERROR_GENERIC, tool_calls
