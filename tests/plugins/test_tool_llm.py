import asyncio
import logging
import os
import yaml
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest
from core.context import SharedContext
from plugins.tool_llm import LLMTool

# Configure logging for tests
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "settings.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"llm": {"model": "configured-model"}}, f)
    return str(config_path)


@pytest.mark.asyncio
async def test_llm_tool_execute_with_config(temp_config_file):
    sophia_dna_prompt = "You are Sophia, an Artificial Mindful Intelligence."
    test_api_key = "test-api-key-from-env"

    def open_side_effect(file, *args, **kwargs):
        if "settings.yaml" in file:
            return mock_open(read_data=yaml.dump({"llm": {"model": "test-model"}})).return_value
        if "sophia_dna.txt" in file:
            return mock_open(read_data=sophia_dna_prompt).return_value
        return mock_open(read_data="").return_value

    with patch("builtins.open", side_effect=open_side_effect), \
         patch.dict(os.environ, {"OPENROUTER_API_KEY": test_api_key}):

        llm_tool = LLMTool()

        context = SharedContext(
            session_id="test",
            current_state="THINKING",
            user_input="Hello",
            history=[{"role": "user", "content": "Hello"}],
            logger=logging.getLogger("test"),
        )

        assert llm_tool.model == "test-model"
        assert llm_tool.system_prompt == sophia_dna_prompt

        mock_response = AsyncMock()
        mock_response.choices[0].message.content = "Hi there!"

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response) as mock_acompletion:
            result_context = await llm_tool.execute(context=context)

        mock_acompletion.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": sophia_dna_prompt},
                {"role": "user", "content": "Hello"},
            ],
            tools=None,
            api_key=test_api_key,
        )
        assert result_context.payload["llm_response"] == "Hi there!"
