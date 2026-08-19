import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.backend.llm.providers.openai_provider import OpenAIProvider
from src.backend.llm.agent_core.conversation import ConversationManager


def test_llm():
    try:
        provider = OpenAIProvider()
        conversation = ConversationManager()

        user_input = "Hello! Say a short greeting in English and Hindi."
        print(f"User: {user_input}")

        conversation.add_user_message(user_input)
        response = provider.generate_response(conversation.get_messages())
        conversation.add_assistant_message(response)

        print(f"VaaniAI: {response}")
        print("\nLLM Module successfully initialized and tested!")
    except Exception as e:
        print(f"Failed to test LLM: {e}")


if __name__ == "__main__":
    test_llm()
