import logging
import httpx
from typing import Dict, Any

from src.backend.core.setting import Settings

logger = logging.getLogger(__name__)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

WEATHER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Fetches the current weather for a specified location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state/country, e.g., 'San Francisco, CA' or 'London, UK'",
                }
            },
            "required": ["location"],
        },
    },
}

def execute_weather_check(location: str) -> str:
    """
    Fetches the current weather from OpenWeatherMap.
    
    Args:
        location: The location string to check.
        
    Returns:
        A formatted string describing the weather or an error message.
    """
    logger.info(f"Fetching weather for: '{location}'")
    
    if not Settings.WEATHERAPI_KEY:
        logger.error("WEATHERAPI_KEY is not set.")
        return "Error: The WeatherAPI key is missing. I cannot check the weather."

    try:
        # OpenWeatherMap requires 'appid' and 'q' parameters, and 'units=metric' for Celsius
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
