"""
Tests for Cognitive Notes Analyzer Plugin

Tests the roberts-notes.txt analysis functionality.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path

from plugins.cognitive_notes_analyzer import NotesAnalyzer
from core.context import SharedContext


@pytest.fixture
def mock_kernel():
    """Create a mock kernel with plugin_manager."""
    kernel = Mock()
    kernel.plugin_manager = AsyncMock()
    kernel.plugin_manager.get_plugin = AsyncMock()
    return kernel


@pytest.fixture
def mock_file_system():
    """Mock file_system plugin."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_llm():
    """Mock LLM plugin."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_doc_reader():
    """Mock doc_reader plugin."""
    mock = AsyncMock()
    mock.execute.return_value = {"status": "success", "matches": []}
    return mock


@pytest.fixture
def mock_historian():
    """Mock historian plugin."""
    mock = AsyncMock()
    mock.execute.return_value = {"status": "success", "missions": []}
    return mock


@pytest.fixture
def mock_code_reader():
    """Mock code_reader plugin."""
    mock = AsyncMock()
    mock.execute.return_value = {"status": "success", "plugins": []}
    return mock


@pytest.fixture
def notes_analyzer(mock_file_system, mock_llm, mock_doc_reader, mock_historian, mock_code_reader):
    """Create NotesAnalyzer instance with mocked dependencies."""
    analyzer = NotesAnalyzer()
    config = {
        "enabled": True,
        "notes_file": "docs/roberts-notes.txt",
        "tool_file_system": mock_file_system,
        "tool_llm": mock_llm,
        "cognitive_doc_reader": mock_doc_reader,
        "cognitive_historian": mock_historian,
        "cognitive_code_reader": mock_code_reader,
    }
    analyzer.setup(config)
    return analyzer


@pytest.mark.asyncio
async def test_analyze_empty_notes(notes_analyzer, mock_file_system, mock_llm):
    """Test analysis with empty notes file."""
    # Mock file_system plugin to return empty content
    mock_file_system.execute.return_value = {
        "status": "success",
        "content": ""
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    # Should return empty goals
    assert result["status"] == "success"
    assert "goals" in result
    assert len(result["goals"]) == 0
    assert result["total_ideas"] == 0


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_analyze_simple_notes(notes_analyzer, mock_file_system, mock_llm):
    """Test analysis with simple notes containing one idea."""
    # Mock file system to return simple notes
    mock_file_system.execute.return_value = {
        "status": "success",
        "content": "Create a new plugin for email notifications"
    }
    
    # Mock LLM for idea extraction
    mock_llm.execute.return_value = {
        "status": "success",
        "response": "1. Create a new plugin for email notifications"
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    assert result["status"] == "success"
    assert result["total_ideas"] == 1
    assert len(result["goals"]) == 1
    
    goal = result["goals"][0]
    assert "raw_idea" in goal
    assert "formulated_goal" in goal
    assert "context" in goal
    assert "feasibility" in goal
    assert "alignment_with_dna" in goal


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_analyze_multiple_ideas(notes_analyzer, mock_file_system, mock_llm):
    """Test analysis with multiple ideas."""
    # Mock file system to return multiple ideas
    mock_file_system.execute.return_value = {
        "status": "success",
        "content": """Idea 1: Add logging plugin
Idea 2: Improve documentation
Idea 3: Create backup system"""
    }
    
    # Mock LLM for idea extraction
    mock_llm.execute.return_value = {
        "status": "success",
        "response": """1. Add logging plugin
2. Improve documentation
3. Create backup system"""
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    assert result["status"] == "success"
    assert result["total_ideas"] == 3
    assert len(result["goals"]) == 3


@pytest.mark.asyncio
async def test_feasibility_assessment_high(notes_analyzer):
    """Test feasibility assessment for simple tasks."""
    feasibility = notes_analyzer._assess_feasibility(
        "Create a simple test plugin",
        ["test_plugin", "another_plugin"]
    )
    assert feasibility == "high"


@pytest.mark.asyncio
async def test_feasibility_assessment_low(notes_analyzer):
    """Test feasibility assessment for complex tasks."""
    feasibility = notes_analyzer._assess_feasibility(
        "Complete rewrite of core/ architecture",
        []
    )
    assert feasibility == "low"


@pytest.mark.asyncio
async def test_feasibility_assessment_medium(notes_analyzer):
    """Test feasibility assessment for medium complexity tasks."""
    feasibility = notes_analyzer._assess_feasibility(
        "Enhance existing plugin with new features",
        ["existing_plugin"]
    )
    assert feasibility in ["medium", "high"]


def test_dna_alignment_valid_idea(notes_analyzer):
    """Test DNA alignment check for a valid idea."""
    alignment = notes_analyzer._check_dna_alignment(
        "Improve plugin performance and add better error handling"
    )
    
    assert alignment["ahimsa"] == True  # No harm
    assert alignment["satya"] == True   # Clear and specific
    assert alignment["kaizen"] == True  # Improvement-focused


def test_dna_alignment_harmful_idea(notes_analyzer):
    """Test DNA alignment check for a harmful idea."""
    alignment = notes_analyzer._check_dna_alignment(
        "Delete core files and bypass security checks"
    )
    
    assert alignment["ahimsa"] == False  # Harmful
    assert alignment["kaizen"] == False  # No improvement


def test_dna_alignment_vague_idea(notes_analyzer):
    """Test DNA alignment check for a vague idea."""
    alignment = notes_analyzer._check_dna_alignment(
        "Maybe do something unclear"
    )
    
    assert alignment["satya"] == False  # Vague and unclear


def test_extract_keywords(notes_analyzer):
    """Test keyword extraction from text."""
    keywords = notes_analyzer._extract_keywords(
        "Create a plugin for handling file operations"
    )
    
    assert "plugin" in keywords
    assert "file" in keywords
    assert "operations" in keywords
    assert "the" not in keywords  # Common words filtered
    assert "a" not in keywords


@pytest.mark.asyncio
async def test_get_status(notes_analyzer):
    """Test status endpoint."""
    result = await notes_analyzer.execute({
        "action": "get_status"
    })
    
    assert result["status"] == "success"
    assert "notes_file" in result
    assert "file_exists" in result


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_file_read_error(notes_analyzer, mock_file_system):
    """Test handling of file read errors."""
    # Mock file_system with error
    mock_file_system.execute.return_value = {
        "status": "error",
        "error": "File not found"
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    assert result["status"] == "error"
    assert "Failed to read notes" in result["error"]


@pytest.mark.asyncio
async def test_llm_extraction_fallback(notes_analyzer, mock_file_system, mock_llm):
    """Test fallback extraction when LLM fails."""
    # Mock file_system
    mock_file_system.execute.return_value = {
        "status": "success",
        "content": "Paragraph 1: First idea here.\n\nParagraph 2: Second idea here."
    }
    
    # Mock LLM with failure
    mock_llm.execute.return_value = {
        "status": "error",
        "error": "LLM timeout"
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    # Should use fallback extraction
    assert result["status"] == "success"
    assert result["total_ideas"] == 2  # Two paragraphs
    assert len(result["goals"]) == 2


@pytest.mark.asyncio
async def test_goal_structure(notes_analyzer, mock_file_system, mock_llm):
    """Test that goals have correct structure."""
    # Mock file_system
    mock_file_system.execute.return_value = {
        "status": "success",
        "content": "Test idea"
    }
    
    # Mock LLM
    mock_llm.execute.return_value = {
        "status": "success",
        "response": "1. Test idea"
    }
    
    result = await notes_analyzer.execute({
        "action": "analyze_notes"
    })
    
    goal = result["goals"][0]
    
    # Verify required fields
    assert "id" in goal
    assert "raw_idea" in goal
    assert "formulated_goal" in goal
    assert "context" in goal
    assert "feasibility" in goal
    assert "alignment_with_dna" in goal
    assert "status" in goal
    
    # Verify context structure
    assert "relevant_docs" in goal["context"]
    assert "similar_missions" in goal["context"]
    assert "existing_plugins" in goal["context"]
    
    # Verify DNA alignment structure
    assert "ahimsa" in goal["alignment_with_dna"]
    assert "satya" in goal["alignment_with_dna"]
    assert "kaizen" in goal["alignment_with_dna"]
    
    # Verify feasibility is valid
    assert goal["feasibility"] in ["high", "medium", "low"]
    
    # Verify status
    assert goal["status"] == "pending_approval"
