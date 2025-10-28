import asyncio
from unittest.mock import MagicMock, AsyncMock
import pytest
from core.kernel import Kernel
from plugins.base_plugin import PluginType


@pytest.mark.asyncio
async def test_kernel_uses_interface_plugin():
    """
    Tests that the Kernel calls the `execute` method on a loaded interface
    plugin.
    """
    kernel = Kernel()
    await kernel.initialize()

    # Replace the actual plugin with a mock to track its calls
    mock_plugin = MagicMock()
    mock_plugin.execute = AsyncMock()

    # Manually insert the mock plugin into the plugin manager
    kernel.plugin_manager._plugins[PluginType.INTERFACE] = [mock_plugin]

    # Run the loop for a very short time and then cancel it
    main_task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.01)
    main_task.cancel()

    # Wait for the task to finish and verify that the `execute` method was called
    try:
        await main_task
    except asyncio.CancelledError:
        pass  # Expected termination

    mock_plugin.execute.assert_called_once()
