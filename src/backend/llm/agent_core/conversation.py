from typing import List, Dict, Any
from src.backend.llm.agent_core.prompts import SystemPrompts


class ConversationManager:
    """Manages the chat history to maintain context for the LLM."""

    def __init__(self, system_prompt: str = None, max_history: int = 10):
        self.max_history = max_history
        self.system_prompt = system_prompt or SystemPrompts.get_default_prompt()
        self.messages: List[Dict[str, Any]] = []
        self._initialize_conversation()

    def _initialize_conversation(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def add_message(self, message: Dict[str, Any]):
        self.messages.append(message)
        self._trim_history()

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def clear_history(self):
        self._initialize_conversation()

    def _trim_history(self):
        if len(self.messages) > self.max_history + 1:
            self.messages = [self.messages[0]] + self.messages[-self.max_history :]
