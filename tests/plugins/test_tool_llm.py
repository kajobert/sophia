from unittest.mock import patch, AsyncMock
import pytest
from plugins.tool_llm import LLMTool
from core.context import SharedContext
import logging

@pytest.mark.asyncio
async def test_llm_tool_execute():
    llm_tool = LLMTool()
    llm_tool.setup({})
    context = SharedContext(
        session_id="test",
        current_state="THINKING",
        user_input="Hello",
        logger=logging.getLogger("test")
    )

    mock_response = AsyncMock()
    mock_response.choices[0].message.content = "Hi there!"

    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response) as mock_acompletion:
        result_context = await llm_tool.execute(context)
        mock_acompletion.assert_called_once()
        assert result_context.payload["llm_response"] == "Hi there!"
