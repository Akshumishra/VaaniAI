import logging
import httpx
from src.backend.core.setting import Settings
from src.backend.llm.agent_core.tools import Tool
from src.backend.llm.agent_core.arg_schema import ArgsSchema

logger = logging.getLogger(__name__)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherSchema:
    args = [
        ("location", ArgsSchema(type=str, description="The city and state/country, e.g., 'San Francisco, CA' or 'London, UK'"))
    ]

def execute_weather_check(location: str) -> str:
    """Fetches the current weather from OpenWeatherMap."""
    logger.info(f"Fetching weather for: '{location}'")
    
    if not Settings.WEATHERAPI_KEY:
        logger.error("WEATHERAPI_KEY is not set.")
        return "Error: The WeatherAPI key is missing. I cannot check the weather."

    try:
        params = {
            "appid": Settings.WEATHERAPI_KEY,
            "q": location,
            "units": "metric"
        }
        
        response = httpx.get(WEATHER_URL, params=params, timeout=10.0)
        
        if response.status_code != 200:
            error_msg = response.json().get("message", "Unknown API error")
            return f"Failed to get weather data: {error_msg}"
            
        data = response.json()
        
        city = data.get("name")
        sys_data = data.get("sys", {})
        country = sys_data.get("country")
        
        main_data = data.get("main", {})
        temp_c = main_data.get("temp")
        humidity = main_data.get("humidity")
        
        weather_list = data.get("weather", [])
        condition = weather_list[0].get("description") if weather_list else "Unknown"
        
        formatted_weather = (
            f"Weather in {city}, {country}:\n"
            f"Condition: {condition}\n"
            f"Temperature: {temp_c}°C\n"
            f"Humidity: {humidity}%"
        )
        
        return formatted_weather
        
    except httpx.RequestError as e:
        logger.exception(f"HTTP request failed: {e}")
        return f"Error connecting to weather service: {e}"
    except Exception as e:
        logger.exception("Failed to parse weather data.")
        return f"Error parsing weather data: {e}"

# Export the Tool instance
weather_tool = Tool(
    func=execute_weather_check,
    description="Fetches the current weather for a specified location.",
    args_schema=WeatherSchema
)
