"""
Cognitive Memory Manager - Smart Memory System

Purpose: Decide WHEN to remember and WHEN to recall memories

Intelligence:
  - Filters noise (don't store "ahoj", "ok", "díky")
  - Detects significant content (facts, preferences, personal info)
  - Auto-recalls relevant memories when needed
  - Prevents memory spam and latency

Version: 1.0.0
"""

import logging
import re
from typing import List, Dict, Optional

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveMemoryManager(BasePlugin):
    """
    Intelligent memory orchestrator - decides what to remember and when to recall.
    
    Key Features:
      1. Significance Detection - filters noise
      2. Smart Recall - searches only when relevant
      3. Efficient Storage - consolidates similar memories
      4. Context Injection - adds memories to LLM context
    """

    def __init__(self):
        self.memory_chroma = None
        self.memory_sqlite = None
        self.event_bus = None
        
        # Significance patterns (Czech + English)
        self.significant_patterns = [
            # Personal info
            r"jmenuji se|my name is|called|volám se",
            r"pracuji|work as|profession|povolání",
            r"mám rád|mám ráda|i like|i love|oblíbený",
            r"nesnáším|i hate|i don't like|nemám rád",
            
            # Facts
            r"je to|this is|to je|that is",
            r"funguje|works|doesn't work|nefunguje",
            r"používám|i use|i'm using|použivam",
            
            # Preferences
            r"preferuji|prefer|radši|rather",
            r"chci|i want|potřebuji|i need",
            
            # Important events
            r"naučil|learned|zjistil|discovered",
            r"problém|problem|issue|bug|chyba",
            r"úspěch|success|fungovalo|worked",
        ]
        
        # Noise patterns (ignore these)
        self.noise_patterns = [
            r"^(ahoj|hello|hi|hey|čau)$",
            r"^(ok|okay|ano|yes|ne|no)$",
            r"^(díky|thanks|thx|děkuji)$",
            r"^(dobře|good|fine|super)$",
        ]
        
        # Recall triggers (when to search memories)
        self.recall_triggers = [
            r"pamatuješ|remember|vzpomínáš",
            r"řekl jsem|i told you|mentioned",
            r"minule|last time|previously|předtím",
            r"co jsem|what did i|what have i",
        ]
        
        # Stats
        self.memories_stored = 0
        self.memories_recalled = 0
        self.noise_filtered = 0
        
    @property
    def name(self) -> str:
        return "cognitive_memory_manager"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        logger.info("Cognitive Memory Manager initializing...")
        
        # Get plugin references
        all_plugins = config.get("all_plugins", {})
        self.memory_chroma = all_plugins.get("memory_chroma")
        self.memory_sqlite = all_plugins.get("memory_sqlite")
        self.event_bus = config.get("event_bus")
        
        if not self.memory_chroma:
            logger.warning("memory_chroma not available - long-term memory disabled")
        
        if not self.memory_sqlite:
            logger.warning("memory_sqlite not available - conversation history disabled")
        
        logger.info("Memory Manager ready")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Main memory processing pipeline.
        
        Workflow:
          1. Check if user message triggers memory recall
          2. If yes, search and inject memories into context
          3. After LLM response, check if worth storing
          4. If yes, extract and store significant facts
        """
        user_input = context.user_input
        
        # STEP 1: Should we recall memories?
        if self._should_recall(user_input):
            memories = await self._recall_memories(user_input)
            if memories:
                # Inject into context for LLM
                context.payload["recalled_memories"] = memories
                logger.info(f"Recalled {len(memories)} memories for context")
                self.memories_recalled += len(memories)
        
        # STEP 2: After LLM response, check if worth storing
        # (This happens in a separate method called after LLM execution)
        
        return context

    async def process_response(self, context: SharedContext) -> None:
        """
        Called AFTER LLM response to decide if conversation worth remembering.
        
        This should be called by Kernel after LLM execution.
        """
        user_input = context.user_input
        llm_response = context.payload.get("llm_response", "")
        
        # Check if user message is significant
        if self._is_significant(user_input):
            await self._store_memory(user_input, source="user")
        
        # Check if LLM learned something important
        if self._is_significant(llm_response):
            # Extract facts from response (e.g., "User works as DevOps engineer")
            facts = self._extract_facts(llm_response)
            for fact in facts:
                await self._store_memory(fact, source="assistant")

    def _should_recall(self, text: str) -> bool:
        """
        Determine if user is asking about past conversations.
        
        Examples that trigger recall:
          - "Pamatuješ si co jsem ti říkal?"
          - "Remember what I told you about my work?"
          - "What did I mention last time?"
        """
        text_lower = text.lower()
        
        for pattern in self.recall_triggers:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False

    def _is_significant(self, text: str) -> bool:
        """
        Determine if text contains significant information worth storing.
        
        Returns:
          True if significant (facts, preferences, personal info)
          False if noise ("ahoj", "ok", "díky")
        """
        text_lower = text.lower().strip()
        
        # Filter out noise
        for pattern in self.noise_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                self.noise_filtered += 1
                return False
        
        # Check for significant patterns
        for pattern in self.significant_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # If longer than 50 chars, might be significant
        if len(text) > 50:
            return True
        
        return False

    def _extract_facts(self, text: str) -> List[str]:
        """
        Extract atomic facts from text.
        
        Example:
          Input: "Uživatel pracuje jako DevOps engineer a má rád Python."
          Output: ["User works as DevOps engineer", "User likes Python"]
        
        For now, simple sentence splitting. Future: LLM-powered extraction.
        """
        # Simple sentence split
        sentences = re.split(r'[.!?]\s+', text)
        
        # Filter significant sentences
        facts = []
        for sentence in sentences:
            if self._is_significant(sentence):
                facts.append(sentence.strip())
        
        return facts

    async def _recall_memories(self, query: str) -> List[str]:
        """
        Search long-term memory for relevant context.
        
        Args:
          query: User's question (e.g., "What did I tell you about my job?")
        
        Returns:
          List of relevant memories (max 3 to avoid context bloat)
        """
        if not self.memory_chroma:
            return []
        
        try:
            memories = self.memory_chroma.search_memories(query, n_results=3)
            return memories
        except Exception as e:
            logger.error(f"Error recalling memories: {e}")
            return []

    async def _store_memory(self, text: str, source: str = "user") -> None:
        """
        Store significant text in long-term memory.
        
        Args:
          text: Content to remember
          source: "user" or "assistant"
        """
        if not self.memory_chroma:
            return
        
        try:
            # Use current session ID (should be in context)
            session_id = "default"  # TODO: Get from context
            
            self.memory_chroma.add_memory(session_id, text)
            self.memories_stored += 1
            logger.info(f"Stored memory ({source}): {text[:50]}...")
        except Exception as e:
            logger.error(f"Error storing memory: {e}")

    def get_stats(self) -> Dict:
        """Return memory statistics for monitoring."""
        return {
            "memories_stored": self.memories_stored,
            "memories_recalled": self.memories_recalled,
            "noise_filtered": self.noise_filtered,
            "chroma_available": self.memory_chroma is not None,
        }
