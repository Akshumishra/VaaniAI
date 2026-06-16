from src.backend.llm.prompt import VAANI_AI_SYSTEM_PROMPT
from src.backend.llm.agent_core.agent import Agent
from src.backend.llm.agent_core.tools import Tool
from src.backend.llm.tools.search import search_tool, SearchSchema
from src.backend.llm.tools.weather import weather_tool, WeatherSchema


class VaaniAI(Agent):
    """
    VaaniAI is the core assistant agent implementation.
    It inherits from the base Agent and comes pre-equipped with
    weather and search tools.
    """
    def __init__(
        self, 
        system_prompt: str = VAANI_AI_SYSTEM_PROMPT, 
        **kwargs):
        
        super().__init__(system_prompt=system_prompt, **kwargs)
        
        self.add_tool(Tool(
            func=search_tool,
            description="Search the web for current events, facts, or information.",
            args_schema=SearchSchema
        ))
        
        self.add_tool(Tool(
            func=weather_tool,
            description="Get the current weather for a specific location.",
            args_schema=WeatherSchema
        ))
