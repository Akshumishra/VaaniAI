from src.backend.llm.agent_core.agent import Agent
from src.backend.llm.agent_core.tools import Tool
from src.backend.llm.tools.web_search import web_search_tool
from src.backend.llm.tools.weather import weather_tool
from src.backend.llm.tools.pdf_search import pdf_search_tool

from src.backend.llm.vaani_agent.prompt import VAANI_AI_SYSTEM_PROMPT
from src.backend.llm.vaani_agent.constant import VaaniConstants


class VaaniAI(Agent):
    """
    VaaniAI is the core assistant agent implementation.
    It inherits from the base Agent and comes pre-equipped with
    web search, weather, and pdf search (RAG) tools.
    """

    def __init__(
        self,
        system_prompt: str = VAANI_AI_SYSTEM_PROMPT,
        model: str = VaaniConstants.MODEL,
        temperature: float = VaaniConstants.TEMPERATURE,
        max_iteration: int = VaaniConstants.MAX_ITERATION,
        **kwargs,
    ):

        super().__init__(
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_iteration=max_iteration,
            **kwargs,
        )

        self.add_tool(web_search_tool)
        self.add_tool(weather_tool)
        self.add_tool(pdf_search_tool)
