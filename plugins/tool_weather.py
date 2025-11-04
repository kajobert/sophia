from plugins.base_plugin import BasePlugin, PluginType
from typing import Dict, Any, List
import logging
import requests
from core.context import SharedContext


class ToolWeather(BasePlugin):
    """OpenWeatherMap API integration for weather data"""

    @property
    def name(self) -> str:
        return "tool_weather"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Setup with dependency injection pattern"""
        self.logger = config.get("logger", logging.getLogger(self.name))
        self.all_plugins = config.get("all_plugins", {})

        # Get API key from config
        self.api_key = config.get("api_key", "")

        if not self.api_key:
            self.logger.warning(f"{self.name} API key not configured")

    async def execute(self, context: SharedContext) -> SharedContext:
        """A placeholder execute method."""
        return context

    def get_current_weather(
        self, context: SharedContext, location: str, units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get the current weather for a location.

        :param context: The shared context for the operation.
        :param location: The city name and optional country code (e.g., "London,uk").
        :param units: The units of measurement (metric, imperial, standard).
        :return: A dictionary with the weather data or an error message.
        """
        if not self.api_key:
            return {"error": "API key not configured"}

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": self.api_key, "units": units}

        try:
            self.logger.info(f"Fetching current weather for {location}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            return {"error": f"HTTP error occurred: {http_err}"}
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            return {"error": f"Request error occurred: {req_err}"}

    def get_forecast(
        self, context: SharedContext, location: str, units: str = "metric", days: int = 3
    ) -> Dict[str, Any]:
        """
        Get the weather forecast for a location.

        :param context: The shared context for the operation.
        :param location: The city name and optional country code (e.g., "London,uk").
        :param units: The units of measurement (metric, imperial, standard).
        :param days: The number of days for the forecast (max 5).
        :return: A dictionary with the forecast data or an error message.
        """
        if not self.api_key:
            return {"error": "API key not configured"}

        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units,
            "cnt": days * 8,
        }  # 3-hour forecast, so 8 per day

        try:
            self.logger.info(f"Fetching weather forecast for {location}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            return {"error": f"HTTP error occurred: {http_err}"}
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            return {"error": f"Request error occurred: {req_err}"}

    def get_tool_definitions(self) -> List[dict]:
        return [
            {
                "name": "get_current_weather",
                "description": "Get the current weather for a specified location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and country code (e.g., 'London,uk').",
                        },
                        "units": {
                            "type": "string",
                            "description": "Units of measurement: 'metric' for Celsius, 'imperial' for Fahrenheit.",
                            "enum": ["metric", "imperial"],
                        },
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_forecast",
                "description": "Get the weather forecast for a specified location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and country code (e.g., 'London,uk').",
                        },
                        "units": {
                            "type": "string",
                            "description": "Units of measurement: 'metric' for Celsius, 'imperial' for Fahrenheit.",
                            "enum": ["metric", "imperial"],
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days for the forecast (1-5).",
                        },
                    },
                    "required": ["location"],
                },
            },
        ]
