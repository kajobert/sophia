"""
Cognitive Memory Consolidator Plugin

Autonomously processes conversation sessions to extract and store long-term knowledge.
Analogous to human "dreaming" - converting episodic memories into semantic knowledge.

Version: 1.0.0
Phase: 3 - Memory Consolidation & Dreaming
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of consolidated memories."""

    INSIGHT = "insight"  # Key learning or discovery
    PATTERN = "pattern"  # Recurring behavior or pattern
    FACT = "fact"  # Concrete factual knowledge
    PROCEDURE = "procedure"  # How to do something
    DECISION = "decision"  # Decision made and rationale
    ERROR_LESSON = "error_lesson"  # Mistake and how to avoid it


class ImportanceLevel(Enum):
    """Importance levels for memory prioritization."""

    CRITICAL = 5  # Must never forget
    HIGH = 4  # Very important
    NORMAL = 3  # Standard importance
    LOW = 2  # Nice to know
    TRIVIAL = 1  # Can be forgotten


class ExtractedMemory(BaseModel):
    """Pydantic model for a single extracted memory."""

    memory_type: MemoryType
    summary: str = Field(..., description="Concise 1-2 sentence summary")
    importance: int = Field(..., ge=1, le=5, description="Importance level (1-5)")
    keywords: List[str] = Field(default_factory=list, description="Relevant tags")
    context: Optional[str] = Field(None, description="Additional context")


class ConsolidationResult(BaseModel):
    """Pydantic model for consolidation analysis result."""

    insights: List[ExtractedMemory] = Field(default_factory=list)
    patterns: List[ExtractedMemory] = Field(default_factory=list)
    facts: List[ExtractedMemory] = Field(default_factory=list)
    procedures: List[ExtractedMemory] = Field(default_factory=list)
    error_lessons: List[ExtractedMemory] = Field(default_factory=list)


class ConsolidationMetrics(BaseModel):
    """Metrics from a consolidation cycle."""

    sessions_processed: int = 0
    memories_created: int = 0
    memories_merged: int = 0
    duration_seconds: float = 0.0
    insights: int = 0
    patterns: int = 0
    facts: int = 0
    procedures: int = 0
    error_lessons: int = 0


class CognitiveMemoryConsolidator(BasePlugin):
    """
    Cognitive Memory Consolidator Plugin

    Autonomously processes conversation sessions to extract and store
    long-term knowledge. Runs during "sleep cycles" to minimize
    interference with active tasks.

    Tool Definitions:
    - trigger_memory_consolidation: Manually trigger consolidation
    - get_consolidation_status: Check consolidation metrics
    - search_consolidated_memories: Search knowledge base
    """

    @property
    def name(self) -> str:
        """Returns the unique name of the plugin."""
        return "cognitive_memory_consolidator"

    @property
    def plugin_type(self) -> PluginType:
        """Returns the type of the plugin."""
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        """Returns the version of the plugin."""
        return "1.0.0"

    def setup(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory consolidation system.

        Args:
            config: Plugin configuration from settings.yaml
        """
        self.config = config
        self.event_bus: Optional[EventBus] = None

        # Consolidation settings
        self.min_importance = config.get("min_importance", 2)
        self.dedup_threshold = config.get("dedup_threshold", 0.85)
        self.llm_model = config.get("llm_model", "gemini-2.0-flash-thinking-exp-1219")
        self.llm_max_tokens = config.get("llm_max_tokens", 4000)
        self.llm_temperature = config.get("llm_temperature", 0.3)

        # References to other plugins (injected later)
        self.llm_plugin = None
        self.chroma_plugin = None
        self.sqlite_plugin = None

        # Metrics tracking
        self.last_consolidation: Optional[datetime] = None
        self.total_consolidations = 0
        self.total_memories_created = 0

        logger.info(
            f"Memory Consolidator initialized (model={self.llm_model}, "
            f"min_importance={self.min_importance})"
        )

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Inject EventBus dependency."""
        self.event_bus = event_bus

    def set_memory_plugins(self, chroma, sqlite, llm) -> None:
        """
        Inject memory and LLM plugin dependencies.

        Args:
            chroma: ChromaDBMemory plugin instance
            sqlite: SQLiteMemory plugin instance
            llm: LLM plugin instance
        """
        self.chroma_plugin = chroma
        self.sqlite_plugin = sqlite
        self.llm_plugin = llm

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Memory consolidator is passive - triggered by events or schedule.

        Args:
            context: Shared context object

        Returns:
            Unchanged context
        """
        return context

    async def trigger_consolidation(
        self, session_ids: Optional[List[str]] = None, force: bool = False
    ) -> ConsolidationMetrics:
        """
        Manually trigger memory consolidation.

        Args:
            session_ids: Specific sessions to consolidate (None = all unconsolidated)
            force: Force reconsolidation of already processed sessions

        Returns:
            ConsolidationMetrics object with results
        """
        start_time = datetime.now()

        # Emit DREAM_STARTED event
        if self.event_bus:
            self.event_bus.publish(
                Event(
                    event_type=EventType.DREAM_STARTED,
                    source=self.name,
                    priority=EventPriority.LOW,
                    data={
                        "session_ids": session_ids,
                        "force": force,
                        "started_at": start_time.isoformat(),
                    },
                )
            )

        logger.info("🌙 Memory consolidation cycle started...")

        try:
            # Phase 1: Gather raw memories
            conversations = await self._gather_unconsolidated_sessions(session_ids, force)

            if not conversations:
                logger.info("No unconsolidated sessions found - skipping consolidation")
                return ConsolidationMetrics()

            logger.info(f"📚 Found {len(conversations)} sessions to consolidate")

            # Phase 2: LLM Analysis
            metrics = ConsolidationMetrics()

            for session_id, conversation_text in conversations.items():
                logger.info(f"🧠 Analyzing session: {session_id}")

                extracted = await self._extract_memories_with_llm(conversation_text)

                # Phase 3: Deduplication & Storage
                session_metrics = await self._store_consolidated_memories(session_id, extracted)

                # Aggregate metrics
                metrics.sessions_processed += 1
                metrics.memories_created += session_metrics.memories_created
                metrics.memories_merged += session_metrics.memories_merged
                metrics.insights += session_metrics.insights
                metrics.patterns += session_metrics.patterns
                metrics.facts += session_metrics.facts
                metrics.procedures += session_metrics.procedures
                metrics.error_lessons += session_metrics.error_lessons

            # Calculate duration
            end_time = datetime.now()
            metrics.duration_seconds = (end_time - start_time).total_seconds()

            # Update tracking
            self.last_consolidation = end_time
            self.total_consolidations += 1
            self.total_memories_created += metrics.memories_created

            # Emit DREAM_COMPLETED event
            if self.event_bus:
                self.event_bus.publish(
                    Event(
                        event_type=EventType.DREAM_COMPLETED,
                        source=self.name,
                        priority=EventPriority.NORMAL,
                        data={
                            "metrics": metrics.model_dump(),
                            "completed_at": end_time.isoformat(),
                        },
                    )
                )

            logger.info(
                f"✨ Consolidation complete: {metrics.memories_created} memories created, "
                f"{metrics.memories_merged} merged in {metrics.duration_seconds:.1f}s"
            )

            return metrics

        except Exception as e:
            logger.error(f"❌ Memory consolidation failed: {e}", exc_info=True)
            raise

    async def _gather_unconsolidated_sessions(
        self, session_ids: Optional[List[str]], force: bool
    ) -> Dict[str, str]:
        """
        Gather conversation histories from unconsolidated sessions.

        Args:
            session_ids: Specific sessions to process (None = all)
            force: Force reconsolidation

        Returns:
            Dict mapping session_id -> conversation_text
        """
        # TODO: Query SQLite for unconsolidated sessions
        # For now, return empty dict - will implement when SQLite schema is updated
        logger.warning("Session gathering not yet implemented - returning empty")
        return {}

    async def _extract_memories_with_llm(self, conversation_text: str) -> ConsolidationResult:
        """
        Use LLM to extract structured memories from conversation.

        Args:
            conversation_text: Full conversation transcript

        Returns:
            ConsolidationResult with extracted memories
        """
        prompt = self._build_extraction_prompt(conversation_text)

        # TODO: Call LLM plugin to get extraction
        # For now, return empty result
        logger.warning("LLM extraction not yet implemented - returning empty")
        return ConsolidationResult()

    def _build_extraction_prompt(self, conversation_text: str) -> str:
        """
        Build the LLM prompt for memory extraction.

        Args:
            conversation_text: Full conversation history

        Returns:
            Formatted extraction prompt
        """
        return f"""You are Sophia's memory consolidation system. Analyze the following conversation
and extract key knowledge that should be permanently stored.

CONVERSATION:
{conversation_text}

Extract the following:

1. INSIGHTS (key learnings, discoveries, realizations):
   - What did Sophia learn?
   - What worked well?
   - What surprised Sophia?

2. PATTERNS (recurring behaviors, tendencies):
   - What patterns emerged?
   - What does the user prefer?
   - What approaches are effective?

3. FACTS (concrete, verifiable information):
   - What factual knowledge was gained?
   - What are the user's preferences/constraints?

4. PROCEDURES (how to do things):
   - What workflows were successful?
   - What are the steps for common tasks?

5. ERRORS & LESSONS (mistakes and how to avoid them):
   - What went wrong?
   - How can it be prevented?

For each item:
- Provide concise summary (1-2 sentences)
- Assign importance (1-5)
- Tag with relevant keywords

Return as JSON matching this structure:
{{
    "insights": [
        {{"memory_type": "insight", "summary": "...", "importance": 4, "keywords": ["tag1", "tag2"]}}
    ],
    "patterns": [...],
    "facts": [...],
    "procedures": [...],
    "error_lessons": [...]
}}
"""

    async def _store_consolidated_memories(
        self, session_id: str, result: ConsolidationResult
    ) -> ConsolidationMetrics:
        """
        Store consolidated memories in ChromaDB with deduplication.

        Args:
            session_id: Source session ID
            result: Extracted memories from LLM

        Returns:
            Metrics for this session
        """
        metrics = ConsolidationMetrics()

        # Process each memory type
        for memory_type, memories in [
            (MemoryType.INSIGHT, result.insights),
            (MemoryType.PATTERN, result.patterns),
            (MemoryType.FACT, result.facts),
            (MemoryType.PROCEDURE, result.procedures),
            (MemoryType.ERROR_LESSON, result.error_lessons),
        ]:
            for memory in memories:
                # Skip low-importance memories
                if memory.importance < self.min_importance:
                    continue

                # TODO: Check for duplicates in ChromaDB
                # TODO: Store in ChromaDB with metadata

                metrics.memories_created += 1

                # Update type-specific counts
                if memory_type == MemoryType.INSIGHT:
                    metrics.insights += 1
                elif memory_type == MemoryType.PATTERN:
                    metrics.patterns += 1
                elif memory_type == MemoryType.FACT:
                    metrics.facts += 1
                elif memory_type == MemoryType.PROCEDURE:
                    metrics.procedures += 1
                elif memory_type == MemoryType.ERROR_LESSON:
                    metrics.error_lessons += 1

        return metrics

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions for LLM function calling.

        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "trigger_memory_consolidation",
                    "description": (
                        "Manually trigger Sophia's memory consolidation cycle. "
                        "This analyzes recent conversations and extracts key learnings, "
                        "patterns, facts, and insights for long-term storage."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific session IDs to consolidate (optional)",
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force reconsolidation of already processed sessions",
                                "default": False,
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_consolidation_status",
                    "description": (
                        "Get status and metrics about Sophia's memory consolidation system. "
                        "Shows when last consolidation ran and cumulative statistics."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_consolidated_memories",
                    "description": (
                        "Search Sophia's consolidated long-term memories. "
                        "Returns relevant insights, patterns, facts learned from past conversations."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query",
                            },
                            "memory_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "insight",
                                        "pattern",
                                        "fact",
                                        "procedure",
                                        "error_lesson",
                                    ],
                                },
                                "description": "Filter by memory types (optional)",
                            },
                            "min_importance": {
                                "type": "integer",
                                "description": "Minimum importance level (1-5)",
                                "default": 2,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], context: SharedContext
    ) -> Dict[str, Any]:
        """
        Execute a tool function.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Shared context

        Returns:
            Tool execution result
        """
        if tool_name == "trigger_memory_consolidation":
            metrics = await self.trigger_consolidation(
                session_ids=arguments.get("session_ids"), force=arguments.get("force", False)
            )
            return {
                "success": True,
                "message": f"Consolidation complete: {metrics.memories_created} memories created",
                "metrics": metrics.model_dump(),
            }

        elif tool_name == "get_consolidation_status":
            return {
                "success": True,
                "status": {
                    "last_consolidation": (
                        self.last_consolidation.isoformat() if self.last_consolidation else None
                    ),
                    "total_consolidations": self.total_consolidations,
                    "total_memories_created": self.total_memories_created,
                },
            }

        elif tool_name == "search_consolidated_memories":
            # TODO: Implement search
            return {"success": False, "message": "Search not yet implemented", "results": []}

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
