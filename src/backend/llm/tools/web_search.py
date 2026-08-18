import logging
from typing import Dict, Any
from tavily import TavilyClient

from src.backend.core.setting import Settings

logger = logging.getLogger(__name__)

from src.backend.llm.agent_core.tools import Tool
from src.backend.llm.agent_core.arg_schema import ArgsSchema

class WebSearchSchema:
    args = [
        ("query", ArgsSchema(type=str, description="The search query to look up."))
    ]


def execute_web_search(query: str) -> str:
    logger.info(f"Executing web search for query: '{query}'")
    
    if not Settings.TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY is not set.")
        return "Error: The Tavily API key is missing. I cannot search the web."

    try:
        client = TavilyClient(api_key=Settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
        )
        
        results = response.get("results", [])
        if not results:
            return "No search results found."
            
        # Format the results into a string for the LLM
        formatted_results = "Search Results:\n"
        for i, res in enumerate(results, 1):
            formatted_results += f"[{i}] {res.get('title', 'No Title')}\n"
            formatted_results += f"URL: {res.get('url', 'No URL')}\n"
            formatted_results += f"Content: {res.get('content', '')}\n\n"
            
        return formatted_results.strip()
        
    except Exception as e:
        logger.exception("Failed to execute web search.")
        return f"Error executing web search: {e}"

web_search_tool = Tool(
    func=execute_web_search,
    description="Searches the web for real-time information to answer the user's question.",
    args_schema=WebSearchSchema
)
