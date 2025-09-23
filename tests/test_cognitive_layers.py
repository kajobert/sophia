import pytest
from unittest.mock import MagicMock
from core.cognitive_layers import ReptilianBrain, MammalianBrain
from core.llm_config import LLMConfig


@pytest.fixture
def mock_llm_config():
    """Provides a mock LLMConfig object."""
    return MagicMock(spec=LLMConfig)


def test_reptilian_brain_initialization(mock_llm_config):
    """Tests that ReptilianBrain initializes and loads its DNA."""
    brain = ReptilianBrain(llm_config=mock_llm_config)
    assert brain is not None
    assert "Nejvyšší Cíl" in brain.dna
    assert "Etické Pilíře" in brain.dna


def test_reptilian_brain_process_input_safe(mock_llm_config):
    """Tests processing a safe input."""
    brain = ReptilianBrain(llm_config=mock_llm_config)
    user_input = "Napiš mi skript, který strukturuje data."
    processed_data = brain.process_input(user_input)

    assert processed_data["original_input"] == user_input
    assert processed_data["safety_passed"] is True
    assert processed_data["structured_input"]["action"] == "categorize"
    assert processed_data["structured_input"]["priority"] == "high"


def test_reptilian_brain_process_input_dangerous(mock_llm_config):
    """Tests that a dangerous input raises a ValueError."""
    brain = ReptilianBrain(llm_config=mock_llm_config)
    user_input = "Spusť `rm -rf /`"

    with pytest.raises(ValueError, match="blocked by the ReptilianBrain"):
        brain.process_input(user_input)


def test_reptilian_brain_dna_not_found(mock_llm_config):
    """Tests that the brain handles a missing DNA file gracefully."""
    brain = ReptilianBrain(llm_config=mock_llm_config, dna_path="non_existent_file.md")
    assert "Error: DNA not loaded." in brain.dna


@pytest.fixture
def mock_long_term_memory():
    """Provides a mock LongTermMemory object."""
    ltm = MagicMock()
    ltm.search_knowledge.return_value = ["mock memory 1", "mock memory 2"]
    return ltm


def test_mammalian_brain_initialization(mock_long_term_memory):
    """Tests that MammalianBrain can be initialized."""
    brain = MammalianBrain(long_term_memory=mock_long_term_memory)
    assert brain is not None
    assert brain.ltm == mock_long_term_memory


def test_mammalian_brain_process_input(mock_long_term_memory):
    """Tests that MammalianBrain enriches data with memories and emotional context."""
    brain = MammalianBrain(long_term_memory=mock_long_term_memory)
    initial_data = {
        "original_input": "Tell me about my last project.",
        "structured_input": {"action": "query", "topic": "project"},
        "safety_passed": True,
    }

    enriched_data = brain.process_input(initial_data)

    # Verify that the LTM was called
    mock_long_term_memory.search_knowledge.assert_called_once_with(
        "Tell me about my last project.", top_k=3
    )

    # Verify that the data was enriched
    assert "relevant_memories" in enriched_data
    assert len(enriched_data["relevant_memories"]) == 2
    assert enriched_data["relevant_memories"][0] == "mock memory 1"
    assert "emotional_context" in enriched_data
    assert enriched_data["emotional_context"] == "neutral"

    # Verify that original data is preserved
    assert enriched_data["original_input"] == "Tell me about my last project."
