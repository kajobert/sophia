# tests/plugins/test_cognitive_task_router.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import yaml
import logging

from core.context import SharedContext
from plugins.cognitive_task_router import CognitiveTaskRouter


@pytest.fixture
def mock_strategy_file():
    """Fixture to mock the 'open' call for the strategy YAML file."""
    strategy_config = {
        "task_strategies": [
            {
                "task_type": "jednoduchy_dotaz",
                "description": "...",
                "model": "openrouter/anthropic/claude-3-haiku",
            },
            {
                "task_type": "sumarizace_textu",
                "description": "...",
                "model": "openrouter/mistralai/mistral-small",
            },
            {
                "task_type": "generovani_planu",
                "description": "...",
                "model": "openrouter/anthropic/claude-3.5-sonnet",
            },
        ]
    }
    m = mock_open(read_data=yaml.dump(strategy_config))
    with patch("builtins.open", m):
        yield


@pytest.fixture
def router(mock_strategy_file):
    """Fixture to create and set up a CognitiveTaskRouter instance for tests."""
    router_instance = CognitiveTaskRouter()
    mock_llm_tool = MagicMock()
    mock_llm_tool.execute = AsyncMock()

    config = {"plugins": {"tool_llm": mock_llm_tool}}
    router_instance.setup(config)

    router_instance.mock_llm_tool = mock_llm_tool
    return router_instance


def create_test_context(user_input: str) -> SharedContext:
    """Helper function to create a SharedContext for tests."""
    return SharedContext(
        session_id="test_session",
        current_state="testing",
        user_input=user_input,
        logger=MagicMock(spec=logging.Logger),
    )


@pytest.mark.asyncio
@patch("builtins.open", new_callable=mock_open, read_data="Test prompt")
@pytest.mark.parametrize(
    "task_type, expected_model",
    [
        ("jednoduchy_dotaz", "openrouter/anthropic/claude-3-haiku"),
        ("sumarizace_textu", "openrouter/mistralai/mistral-small"),
        ("generovani_planu", "openrouter/anthropic/claude-3.5-sonnet"),
    ],
)
async def test_successful_classification_and_routing(mock_file, router, task_type, expected_model):
    """Test that the router correctly classifies tasks and selects the right model."""
    context = create_test_context("Some user input")
    llm_response_context = create_test_context("LLM response")
    llm_response_context.payload["llm_response"] = task_type
    router.mock_llm_tool.execute.return_value = llm_response_context

    updated_context = await router.execute(context=context)

    assert "model_config" in updated_context.payload
    assert updated_context.payload["model_config"]["model"] == expected_model
    context.logger.info.assert_called_with(
        f"Task classified as '{task_type}'. Using model: {expected_model}",
        extra={"plugin_name": router.name},
    )


@pytest.mark.asyncio
@patch("builtins.open", new_callable=mock_open, read_data="Test prompt")
async def test_routing_fallback_on_invalid_classification(mock_file, router):
    """Test that the router falls back to the default model on an invalid classification."""
    context = create_test_context("Some ambiguous input")
    llm_response_context = create_test_context("LLM response")
    llm_response_context.payload["llm_response"] = "invalid_task_type"
    router.mock_llm_tool.execute.return_value = llm_response_context

    updated_context = await router.execute(context=context)

    default_model = "openrouter/anthropic/claude-3.5-sonnet"
    assert "model_config" in updated_context.payload
    assert updated_context.payload["model_config"]["model"] == default_model
    context.logger.warning.assert_called_with(
        "Could not classify task. Defaulting to high-quality model. LLM response: 'invalid_task_type'",
        extra={"plugin_name": router.name},
    )


@pytest.mark.asyncio
@patch("builtins.open", new_callable=mock_open, read_data="Test prompt")
async def test_routing_fallback_on_llm_error(mock_file, router):
    """Test that the router falls back to the default model if the LLM tool fails."""
    context = create_test_context("Some input")
    router.mock_llm_tool.execute.side_effect = Exception("LLM API Error")

    updated_context = await router.execute(context=context)

    default_model = "openrouter/anthropic/claude-3.5-sonnet"
    assert "model_config" in updated_context.payload
    assert updated_context.payload["model_config"]["model"] == default_model
    # fmt: off
    context.logger.error.assert_called_with(
        "Error during task routing: LLM API Error. "
        "Defaulting to high-quality model.",
        extra={"plugin_name": router.name},
    )
    # fmt: on
