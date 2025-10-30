from unittest.mock import patch, AsyncMock, mock_open, MagicMock
import pytest
from plugins.tool_llm import LLMTool
from core.context import SharedContext
import logging
import os
import yaml


@pytest.fixture
def temp_config_file(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "settings.yaml"
    config_data = {"llm": {"model": "test-model"}}
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_llm_tool_execute_with_config(temp_config_file):
    sophia_dna_prompt = "You are Sophia, an Artificial Mindful Intelligence."

    # Mock reading of both settings.yaml and sophia_dna.txt
    def open_side_effect(file, *args, **kwargs):
        if "settings.yaml" in file:
            config_data = {"llm": {"model": "test-model"}}
            return mock_open(read_data=yaml.dump(config_data)).return_value
        elif "sophia_dna.txt" in file:
            return mock_open(read_data=sophia_dna_prompt).return_value
        return mock_open(read_data="").return_value

    with patch("builtins.open", side_effect=open_side_effect):
        llm_tool = LLMTool()
        # The __init__ calls setup, so the mocks are already in effect

        mock_logger = MagicMock()
        mock_logger.level = logging.INFO
        with patch("logging.getLogger", return_value=mock_logger):
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

        with patch(
            "litellm.acompletion", new_callable=AsyncMock, return_value=mock_response
        ) as mock_acompletion:
            result_context = await llm_tool.execute(context=context)

        # The tool should now be called with the history, which includes the user input.
        mock_acompletion.assert_called_once_with(
            model="test-model",
            messages=[
                {
                    "role": "system",
                    "content": "You are Sophia, an Artificial Mindful Intelligence.",
                },
                {"role": "user", "content": "Hello"},
            ],
            tools=None,
        )
        assert result_context.payload["llm_response"] == "Hi there!"
