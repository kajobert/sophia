import pytest
from unittest.mock import MagicMock, patch
from plugins.tool_weather import ToolWeather
import logging
import requests
from core.context import SharedContext


@pytest.fixture
def logger():
    return logging.getLogger("test_logger")


@pytest.fixture
def shared_context():
    return MagicMock(spec=SharedContext)


@pytest.fixture
def plugin(logger):
    plugin = ToolWeather()
    plugin.setup({"logger": logger, "api_key": "test_api_key"})
    return plugin


def test_get_current_weather_success(plugin, shared_context):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"weather": "sunny"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = plugin.get_current_weather(shared_context, "London,uk")
        assert result == {"weather": "sunny"}
        mock_get.assert_called_once()


def test_get_current_weather_http_error(plugin, shared_context):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error"
        )
        mock_get.return_value = mock_response

        result = plugin.get_current_weather(shared_context, "London,uk")
        assert "error" in result
        assert "HTTP error" in result["error"]


def test_get_forecast_success(plugin, shared_context):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"forecast": "sunny"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = plugin.get_forecast(shared_context, "London,uk")
        assert result == {"forecast": "sunny"}
        mock_get.assert_called_once()


def test_get_forecast_request_error(plugin, shared_context):
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = plugin.get_forecast(shared_context, "London,uk")
        assert "error" in result
        assert "Request error" in result["error"]


def test_no_api_key(logger, shared_context):
    plugin = ToolWeather()
    plugin.setup({"logger": logger})
    result = plugin.get_current_weather(shared_context, "London,uk")
    assert "error" in result
    assert "API key not configured" in result["error"]
