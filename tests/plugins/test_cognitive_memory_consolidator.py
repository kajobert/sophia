"""
Unit tests for CognitiveMemoryConsolidator plugin.

Tests memory extraction, deduplication, storage, and tool execution.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from plugins.cognitive_memory_consolidator import (
    CognitiveMemoryConsolidator,
    MemoryType,
    ImportanceLevel,
    ExtractedMemory,
    ConsolidationResult,
    ConsolidationMetrics
)
from plugins.base_plugin import PluginType
from core.context import SharedContext
from core.event_bus import EventBus
from core.events import EventType


@pytest.fixture
def consolidator():
    """Create a MemoryConsolidator instance for testing."""
    plugin = CognitiveMemoryConsolidator()
    config = {
        "min_importance": 2,
        "dedup_threshold": 0.85,
        "llm_model": "test-model",
        "llm_max_tokens": 2000,
        "llm_temperature": 0.3
    }
    plugin.setup(config)
    return plugin


@pytest.fixture
def event_bus():
    """Create an EventBus for testing."""
    return EventBus()


@pytest.fixture
def mock_context():
    """Create a mock SharedContext."""
    import logging
    return SharedContext(
        session_id="test_session",
        current_state="processing",
        logger=logging.getLogger("test"),
        user_input="test input"
    )


class TestPluginMetadata:
    """Test plugin metadata and initialization."""
    
    def test_plugin_name(self, consolidator):
        """Test plugin name."""
        assert consolidator.name == "cognitive_memory_consolidator"
    
    def test_plugin_type(self, consolidator):
        """Test plugin type."""
        assert consolidator.plugin_type == PluginType.COGNITIVE
    
    def test_plugin_version(self, consolidator):
        """Test plugin version."""
        assert consolidator.version == "1.0.0"
    
    def test_setup_config(self, consolidator):
        """Test configuration is loaded correctly."""
        assert consolidator.min_importance == 2
        assert consolidator.dedup_threshold == 0.85
        assert consolidator.llm_model == "test-model"
        assert consolidator.llm_max_tokens == 2000
        assert consolidator.llm_temperature == 0.3


class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_extracted_memory_valid(self):
        """Test valid ExtractedMemory creation."""
        memory = ExtractedMemory(
            memory_type=MemoryType.INSIGHT,
            summary="Test insight about async programming",
            importance=4,
            keywords=["async", "python", "best-practice"]
        )
        assert memory.memory_type == MemoryType.INSIGHT
        assert memory.importance == 4
        assert len(memory.keywords) == 3
    
    def test_extracted_memory_importance_validation(self):
        """Test importance level validation."""
        with pytest.raises(ValueError):
            ExtractedMemory(
                memory_type=MemoryType.FACT,
                summary="Invalid importance",
                importance=10  # Should fail - max is 5
            )
    
    def test_consolidation_result_empty(self):
        """Test empty ConsolidationResult."""
        result = ConsolidationResult()
        assert result.insights == []
        assert result.patterns == []
        assert result.facts == []
        assert result.procedures == []
        assert result.error_lessons == []
    
    def test_consolidation_metrics_defaults(self):
        """Test ConsolidationMetrics default values."""
        metrics = ConsolidationMetrics()
        assert metrics.sessions_processed == 0
        assert metrics.memories_created == 0
        assert metrics.memories_merged == 0
        assert metrics.duration_seconds == 0.0


class TestEventBusIntegration:
    """Test EventBus integration."""
    
    @pytest.mark.asyncio
    async def test_set_event_bus(self, consolidator, event_bus):
        """Test EventBus injection."""
        consolidator.set_event_bus(event_bus)
        assert consolidator.event_bus is event_bus
    
    @pytest.mark.asyncio
    async def test_dream_started_event_emitted(self, consolidator, event_bus):
        """Test DREAM_STARTED event is emitted."""
        consolidator.set_event_bus(event_bus)
        
        # Start the event bus dispatcher
        await event_bus.start()
        
        received_events = []
        
        async def capture_event(event):
            received_events.append(event)
        
        # NOTE: subscribe() is NOT async - no await
        event_bus.subscribe(EventType.DREAM_STARTED, capture_event)
        
        # Trigger consolidation (will complete with no sessions)
        await consolidator.trigger_consolidation()
        
        # Give event loop time to process
        await asyncio.sleep(0.1)
        
        # Stop the event bus
        await event_bus.stop()
        
        # Check event was emitted
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.DREAM_STARTED
        assert received_events[0].source == "cognitive_memory_consolidator"


class TestMemoryExtraction:
    """Test memory extraction logic."""
    
    def test_build_extraction_prompt(self, consolidator):
        """Test extraction prompt generation."""
        conversation = "User: How do I use async?\nSophia: Use async/await..."
        
        prompt = consolidator._build_extraction_prompt(conversation)
        
        assert "CONVERSATION:" in prompt
        assert conversation in prompt
        assert "INSIGHTS" in prompt
        assert "PATTERNS" in prompt
        assert "FACTS" in prompt
        assert "PROCEDURES" in prompt
        assert "ERRORS & LESSONS" in prompt
        assert "JSON" in prompt
    
    @pytest.mark.asyncio
    async def test_extract_memories_with_llm_stub(self, consolidator):
        """Test LLM extraction (stub implementation)."""
        result = await consolidator._extract_memories_with_llm("test conversation")
        
        # Should return empty result until LLM is integrated
        assert isinstance(result, ConsolidationResult)
        assert result.insights == []


class TestMemoryStorage:
    """Test memory storage and deduplication."""
    
    @pytest.mark.asyncio
    async def test_store_consolidated_memories_filters_low_importance(self, consolidator):
        """Test low-importance memories are filtered."""
        result = ConsolidationResult(
            insights=[
                ExtractedMemory(
                    memory_type=MemoryType.INSIGHT,
                    summary="Important insight",
                    importance=4,
                    keywords=["important"]
                ),
                ExtractedMemory(
                    memory_type=MemoryType.INSIGHT,
                    summary="Trivial insight",
                    importance=1,  # Below min_importance=2
                    keywords=["trivial"]
                )
            ]
        )
        
        metrics = await consolidator._store_consolidated_memories("test_session", result)
        
        # Should only count the high-importance memory
        assert metrics.memories_created == 1
        assert metrics.insights == 1
    
    @pytest.mark.asyncio
    async def test_store_consolidated_memories_counts_by_type(self, consolidator):
        """Test metrics are counted correctly by memory type."""
        result = ConsolidationResult(
            insights=[
                ExtractedMemory(
                    memory_type=MemoryType.INSIGHT,
                    summary="Insight 1",
                    importance=3,
                    keywords=[]
                ),
                ExtractedMemory(
                    memory_type=MemoryType.INSIGHT,
                    summary="Insight 2",
                    importance=4,
                    keywords=[]
                )
            ],
            patterns=[
                ExtractedMemory(
                    memory_type=MemoryType.PATTERN,
                    summary="Pattern 1",
                    importance=3,
                    keywords=[]
                )
            ],
            facts=[
                ExtractedMemory(
                    memory_type=MemoryType.FACT,
                    summary="Fact 1",
                    importance=5,
                    keywords=[]
                )
            ]
        )
        
        metrics = await consolidator._store_consolidated_memories("test_session", result)
        
        assert metrics.insights == 2
        assert metrics.patterns == 1
        assert metrics.facts == 1
        assert metrics.procedures == 0
        assert metrics.error_lessons == 0
        assert metrics.memories_created == 4


class TestConsolidationWorkflow:
    """Test full consolidation workflow."""
    
    @pytest.mark.asyncio
    async def test_trigger_consolidation_no_sessions(self, consolidator, event_bus):
        """Test consolidation with no unconsolidated sessions."""
        consolidator.set_event_bus(event_bus)
        
        metrics = await consolidator.trigger_consolidation()
        
        assert metrics.sessions_processed == 0
        assert metrics.memories_created == 0
    
    @pytest.mark.asyncio
    async def test_trigger_consolidation_updates_tracking(self, consolidator, event_bus):
        """Test consolidation updates internal tracking even with empty sessions."""
        consolidator.set_event_bus(event_bus)
        
        initial_count = consolidator.total_consolidations
        
        # Mock some sessions to force processing
        async def mock_gather(session_ids, force):
            return {"test_session": "User: test\nSophia: response"}
        
        consolidator._gather_unconsolidated_sessions = mock_gather
        
        await consolidator.trigger_consolidation()
        
        # Tracking should be updated even if no memories created
        assert consolidator.total_consolidations == initial_count + 1
        assert consolidator.last_consolidation is not None
        assert isinstance(consolidator.last_consolidation, datetime)


class TestToolDefinitions:
    """Test LLM tool definitions."""
    
    def test_get_tool_definitions(self, consolidator):
        """Test tool definitions are provided."""
        tools = consolidator.get_tool_definitions()
        
        assert len(tools) == 3
        
        tool_names = [t["function"]["name"] for t in tools]
        assert "trigger_memory_consolidation" in tool_names
        assert "get_consolidation_status" in tool_names
        assert "search_consolidated_memories" in tool_names
    
    def test_trigger_consolidation_tool_schema(self, consolidator):
        """Test trigger_memory_consolidation tool schema."""
        tools = consolidator.get_tool_definitions()
        trigger_tool = next(
            t for t in tools if t["function"]["name"] == "trigger_memory_consolidation"
        )
        
        params = trigger_tool["function"]["parameters"]["properties"]
        assert "session_ids" in params
        assert "force" in params
        assert params["session_ids"]["type"] == "array"
        assert params["force"]["type"] == "boolean"


class TestToolExecution:
    """Test tool execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_trigger_consolidation(self, consolidator, mock_context, event_bus):
        """Test trigger_memory_consolidation tool execution."""
        consolidator.set_event_bus(event_bus)
        
        result = await consolidator.execute_tool(
            "trigger_memory_consolidation",
            {"force": False},
            mock_context
        )
        
        assert result["success"] is True
        assert "metrics" in result
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_get_status(self, consolidator, mock_context):
        """Test get_consolidation_status tool execution."""
        result = await consolidator.execute_tool(
            "get_consolidation_status",
            {},
            mock_context
        )
        
        assert result["success"] is True
        assert "status" in result
        assert "total_consolidations" in result["status"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_search_memories_not_implemented(self, consolidator, mock_context):
        """Test search_consolidated_memories returns not implemented."""
        result = await consolidator.execute_tool(
            "search_consolidated_memories",
            {"query": "test"},
            mock_context
        )
        
        assert result["success"] is False
        assert "not yet implemented" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_tool_unknown_tool(self, consolidator, mock_context):
        """Test unknown tool returns error."""
        result = await consolidator.execute_tool(
            "unknown_tool",
            {},
            mock_context
        )
        
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestMemoryPluginIntegration:
    """Test integration with other memory plugins."""
    
    def test_set_memory_plugins(self, consolidator):
        """Test memory plugin injection."""
        mock_chroma = object()
        mock_sqlite = object()
        mock_llm = object()
        
        consolidator.set_memory_plugins(mock_chroma, mock_sqlite, mock_llm)
        
        assert consolidator.chroma_plugin is mock_chroma
        assert consolidator.sqlite_plugin is mock_sqlite
        assert consolidator.llm_plugin is mock_llm
    
    @pytest.mark.asyncio
    async def test_execute_returns_context_unchanged(self, consolidator, mock_context):
        """Test execute() is passive and returns context unchanged."""
        result = await consolidator.execute(mock_context)
        
        assert result is mock_context
