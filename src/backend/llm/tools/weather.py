from typing import Dict, Any
import requests

from src.backend.core.setting import Settings
from src.backend.llm.agent_core.arg_schema import ArgsSchema

class WeatherSchema:
    args = [
        ("location", ArgsSchema(type=str, description="The city and state, e.g. San Francisco, CA"))
    ]

def weather_tool(location: str) -> Dict[str, Any]:
    """Get the current weather for a specific location."""
    if not Settings.WEATHER_API:
        return {"error": "WEATHER_API key not configured in settings."}

    url = f"{Settings.WEATHER_URL}?key={Settings.WEATHER_API}&q={location}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "location": data["location"]["name"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"]
        }
    except Exception as e:
        return {"error": str(e)}
        