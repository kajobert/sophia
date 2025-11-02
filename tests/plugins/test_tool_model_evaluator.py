import pytest
from unittest.mock import AsyncMock, MagicMock

from plugins.tool_model_evaluator import ModelEvaluatorTool
from core.context import SharedContext


@pytest.fixture
def mock_llm_tool():
    """Fixture to create a mock LLMTool."""
    return AsyncMock()


@pytest.fixture
def model_evaluator(mock_llm_tool):
    """Fixture to create an instance of ModelEvaluatorTool with a mock LLMTool."""
    evaluator = ModelEvaluatorTool()
    # Manually set the llm_tool since setup is not called in this unit test
    evaluator.llm_tool = mock_llm_tool
    return evaluator


@pytest.mark.asyncio
async def test_evaluate_model_success(model_evaluator, mock_llm_tool):
    """Test the successful evaluation of a model."""
    # Arrange
    context = SharedContext(
        session_id="test_session", logger=MagicMock(), current_state="EXECUTING"
    )
    model_name = "test-model"
    prompt = "Hello, world!"
    evaluation_criteria = ["clarity", "conciseness"]
    judge_model_name = "judge-model"

    # Mock the responses from the LLM tool
    mock_llm_tool.execute.side_effect = [
        # First call for the model being evaluated
        AsyncMock(
            payload={
                "llm_response": "This is a clear and concise response.",
                "llm_response_metadata": {
                    "input_tokens": 10,
                    "output_tokens": 20,
                    "total_tokens": 30,
                    "cost_usd": 0.0001,
                },
            }
        ),
        # Second call for the judge model
        AsyncMock(
            payload={
                "llm_response": (
                    '{"scores": {"clarity": 9, "conciseness": 8}, '
                    '"justification": "Good job.", "overall_score": 8.5}'
                )
            }
        ),
    ]

    # Act
    result = await model_evaluator.evaluate_model(
        context, model_name, prompt, evaluation_criteria, judge_model_name
    )

    # Assert
    assert result["model_name"] == model_name
    assert result["performance"]["input_tokens"] == 10
    assert result["quality"]["overall_score"] == 8.5
    assert "This is a clear and concise response." in result["response"]
    assert mock_llm_tool.execute.call_count == 2


@pytest.mark.asyncio
async def test_evaluate_model_llm_failure(model_evaluator, mock_llm_tool):
    """Test the case where the evaluated model fails."""
    # Arrange
    context = SharedContext(
        session_id="test_session", logger=MagicMock(), current_state="EXECUTING"
    )
    model_name = "failing-model"
    prompt = "This will fail."
    evaluation_criteria = ["resilience"]
    judge_model_name = "judge-model"

    # Mock the LLM tool to raise an exception
    mock_llm_tool.execute.side_effect = Exception("Model API is down")

    # Act
    result = await model_evaluator.evaluate_model(
        context, model_name, prompt, evaluation_criteria, judge_model_name
    )

    # Assert
    assert "error" in result
    assert "Failed to get response from model" in result["error"]
    assert mock_llm_tool.execute.call_count == 1


@pytest.mark.asyncio
async def test_evaluate_model_judge_failure(model_evaluator, mock_llm_tool):
    """Test the case where the judge model fails or returns invalid JSON."""
    # Arrange
    context = SharedContext(
        session_id="test_session", logger=MagicMock(), current_state="EXECUTING"
    )
    model_name = "test-model"
    prompt = "Hello again"
    evaluation_criteria = ["clarity"]
    judge_model_name = "failing-judge"

    # Mock the LLM tool responses
    mock_llm_tool.execute.side_effect = [
        # First call for the model being evaluated (succeeds)
        AsyncMock(
            payload={
                "llm_response": "A valid response.",
                "llm_response_metadata": {"cost_usd": 0.0001},
            }
        ),
        # Second call for the judge model (returns malformed JSON)
        AsyncMock(payload={"llm_response": "this is not json"}),
    ]

    # Act
    result = await model_evaluator.evaluate_model(
        context, model_name, prompt, evaluation_criteria, judge_model_name
    )

    # Assert
    assert "quality" in result
    assert "error" in result["quality"]
    assert "Failed to parse JSON" in result["quality"]["error"]
    assert mock_llm_tool.execute.call_count == 2
