import requests
from typing import Dict, Any

from src.backend.core.setting import Settings
from src.backend.llm.agent_core.arg_schema import ArgsSchema

class SearchSchema:
    args = [
        ("query", ArgsSchema(type=str, description="The search query to look up information for."))
    ]

def search_tool(query: str) -> Dict[str, Any]:
    """Search the web for current information."""
    if not Settings.TAVILY_API:
        return {"error": "TAVILY_API key not configured in settings."}

    url = Settings.TAVILY_URL
    payload = {
        "api_key": Settings.TAVILY_API,
        "query": query,
        "search_depth": "basic",
        "include_answer": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return {"results": data.get("results", []), "answer": data.get("answer", "")}
    except Exception as e:
        return {"error": str(e)}
