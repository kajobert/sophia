import logging
import pytest
from unittest.mock import MagicMock, AsyncMock

from core.context import SharedContext
from plugins.interface_webui import WebUIInterface


@pytest.fixture
def webui_plugin():
    """Provides a fresh, configured instance of the WebUIInterface plugin."""
    plugin = WebUIInterface()
    plugin.setup(config={"host": "127.0.0.1", "port": 8000})
    return plugin


@pytest.mark.asyncio
async def test_webui_plugin_initialization(webui_plugin):
    """Tests that the plugin initializes with the correct properties."""
    assert webui_plugin.name == "interface_webui"
    assert webui_plugin.plugin_type.name == "INTERFACE"
    assert webui_plugin.version == "1.0.0"
    assert not webui_plugin._server_started


@pytest.mark.asyncio
async def test_webui_server_starts_on_first_execute(webui_plugin):
    """
    Tests that the web server is started only on the first call to execute.
    """

    async def mock_start_server():
        webui_plugin._server_started = True

    webui_plugin.start_server = AsyncMock(side_effect=mock_start_server)
    webui_plugin.input_queue.put_nowait(("test input", lambda msg: None))

    context = SharedContext(
        session_id="test_session", current_state="TESTING", logger=logging.getLogger()
    )
    await webui_plugin.execute(context)

    webui_plugin.start_server.assert_called_once()

    # Call execute again to ensure start_server is not called a second time
    webui_plugin.input_queue.put_nowait(("test input 2", lambda msg: None))
    await webui_plugin.execute(context)
    webui_plugin.start_server.assert_called_once()


@pytest.mark.asyncio
async def test_webui_execute_updates_context(webui_plugin):
    """
    Tests that the execute method correctly updates the context with user
    input and a response callback.
    """
    webui_plugin._server_started = True  # Pretend server is already started
    mock_callback = MagicMock()
    webui_plugin.input_queue.put_nowait(("hello from web", mock_callback))

    context = SharedContext(
        session_id="test_session", current_state="TESTING", logger=logging.getLogger()
    )
    updated_context = await webui_plugin.execute(context)

    assert updated_context.user_input == "hello from web"
    assert updated_context.payload["_response_callback"] is mock_callback
