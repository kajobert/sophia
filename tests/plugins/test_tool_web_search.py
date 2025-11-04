import pytest
import logging
from plugins.tool_web_search import WebSearchTool
from unittest.mock import patch, MagicMock
from core.context import SharedContext


@pytest.fixture
def mock_context():
    context = SharedContext(
        session_id="test_session", current_state="TESTING", logger=MagicMock(spec=logging.Logger)
    )
    return context


@pytest.fixture
def web_search_tool():
    """Fixture to provide a WebSearchTool instance with a mocked API service."""
    tool = WebSearchTool()
    # Mock the configuration
    config = {"google_api_key": "test_api_key", "google_cse_id": "test_cse_id"}
    # Mock the `build` function to avoid actual API calls during setup
    with patch("plugins.tool_web_search.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        tool.setup(config)
        yield tool


def test_web_search_success(web_search_tool, mock_context):
    """Tests a successful web search."""
    mock_results = {
        "items": [
            {
                "title": "Test Title",
                "link": "https://example.com",
                "snippet": "This is a test snippet.",
            }
        ]
    }
    # Configure the mock service to return our mock results
    web_search_tool.service.cse().list().execute.return_value = mock_results
    results = web_search_tool.search(context=mock_context, query="test query")
    assert len(results) == 1
    assert results[0]["title"] == "Test Title"
    web_search_tool.service.cse().list.assert_called_with(q="test query", cx="test_cse_id", num=5)
    mock_context.logger.info.assert_called_with("Performing web search for: 'test query'")


def test_web_search_not_configured(mock_context):
    """Tests that the tool handles being called without proper configuration."""
    tool = WebSearchTool()
    tool.setup({})  # No API key or CSE ID
    results = tool.search(context=mock_context, query="test query")
    assert len(results) == 1
    assert "not configured" in results[0].get("error", "")
    mock_context.logger.error.assert_called_with("Web search tool is not configured.")


def test_web_search_api_error(web_search_tool, mock_context):
    """Tests how the tool handles an error from the Google API."""
    # Configure the mock service to raise an exception
    web_search_tool.service.cse().list().execute.side_effect = Exception("API Error")
    results = web_search_tool.search(context=mock_context, query="test query")
    assert len(results) == 1
    assert "API Error" in results[0].get("error", "")
    mock_context.logger.error.assert_called_with(
        "An error occurred during web search: API Error", exc_info=True
    )
