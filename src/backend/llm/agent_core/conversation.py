from typing import List, Dict, Any
from src.backend.llm.agent_core.prompts import SystemPrompts

class ConversationManager:
    """Manages the chat history to maintain context for the LLM."""

    def __init__(self, system_prompt: str = None, max_history: int = 10):
        """
        Initializes the conversation manager.

        Args:
            system_prompt: The initial system prompt. If None, uses default.
            max_history: The maximum number of messages to keep in history to avoid token limits.
        """
        self.max_history = max_history
        self.system_prompt = system_prompt or SystemPrompts.get_default_prompt()
        self.messages: List[Dict[str, Any]] = []
        self._initialize_conversation()

    def _initialize_conversation(self):
        """Sets up the initial system message."""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]

    def add_user_message(self, content: str):
        """Adds a message from the user."""
        self.messages.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, content: str):
        """Adds a message from the assistant."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns the current list of messages."""
        return self.messages

    def clear_history(self):
        """Clears the conversation history, retaining only the system prompt."""
        self._initialize_conversation()

    def _trim_history(self):
        """Trims the history to maintain the max_history limit, ensuring system prompt is kept."""
        if len(self.messages) > self.max_history + 1: # +1 for the system prompt
            # Keep the system prompt (index 0) and the most recent max_history messages
            self.messages = [self.messages[0]] + self.messages[-self.max_history:]
