import json
from pathlib import Path
from typing import List, Dict, Any
from src.backend.llm.agent_core.constants import Constants
from src.backend.core.constants import Paths


class ConversationManager:
    """Manages the chat history to maintain context for the LLM."""

    def __init__(self, max_history: int = Constants.DEFAULT_MAX_HISTORY, file_path: Path = None):
        self.max_history = max_history
        self.file_path = file_path or Paths.GENERATED_DIR / "chat_history.json"
        self._initialize_conversation()

    def _initialize_conversation(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save_messages([])

    def add_user_message(self, content: str):
        self.add_message({"role": "user", "content": content})

    def add_assistant_message(self, text: str):
        self.add_message({"role": "assistant", "content": text})

    def add_message(self, message: Dict[str, Any]):
        messages = self._load_messages()
        messages.append(message)
        self._save_messages(messages)

    def get_messages(self) -> List[Dict[str, Any]]:
        messages = self._load_messages()
        return messages[-self.max_history:] if self.max_history > 0 else messages

    def clear_history(self):
        self._save_messages([])

    def _load_messages(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_messages(self, messages: List[Dict[str, Any]]):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
