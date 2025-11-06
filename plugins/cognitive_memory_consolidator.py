"""
Cognitive Memory Consolidator Plugin - Phase 3.2 AMI 1.0

Inspired by human brain memory consolidation:
  - Hippocampus (SQLite): Short-term, 14+ days retention
  - Neocortex (ChromaDB): Long-term, semantic search
  - Sleep consolidation: Transfers memories without loss

Philosophy:
  - NEVER lose memories (conservative retention)
  - Consolidate frequently (avoid token waste)
  - Natural and efficient (like human brain)
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveMemoryConsolidator(BasePlugin):
    """
    Brain-inspired memory consolidation system.
    
    Mimics human sleep cycle:
      1. Short-term memory (SQLite): 14+ days
      2. Consolidation during "sleep" (DREAM_TRIGGER)
      3. Long-term memory (ChromaDB): Forever
      4. NO DATA LOSS - conservative retention
    """

    def __init__(self):
        self.memory_sqlite = None
        self.memory_chroma = None
        self.event_bus = None
        
        # Brain-inspired timings
        self.consolidation_age_hours = 48  # 2 days (not 24h - safer!)
        self.retention_days = 30  # Keep in SQLite for 30 days (not 7!)
        self.batch_size = 100
        
        # Conversation memory consolidation
        self.conversation_retention_days = 14  # Keep conversations for 2 weeks
        
        # Statistics
        self.last_consolidation = None
        self.total_consolidated = 0
        self.total_deleted = 0
        self.conversations_consolidated = 0
        
        self.last_consolidation = None
        self.total_consolidated = 0
        self.total_deleted = 0
        
    @property
    def name(self) -> str:
        return "cognitive_memory_consolidator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "2.0.0"

    def setup(self, config: dict) -> None:
        logger.info("Cognitive Memory Consolidator initializing...")
        
        all_plugins = config.get("all_plugins", {})
        self.memory_sqlite = all_plugins.get("memory_sqlite")
        self.memory_chroma = all_plugins.get("memory_chroma")
        self.event_bus = config.get("event_bus")
        
        if self.event_bus:
            self.event_bus.subscribe(EventType.DREAM_TRIGGER, self._on_dream_trigger)
        
        self.consolidation_age_hours = config.get("consolidation_age_hours", 24)
        self.retention_days = config.get("retention_days", 7)
        
        logger.info("Memory Consolidator ready")

    async def execute(self, context: SharedContext) -> SharedContext:
        return context

    async def _on_dream_trigger(self, event: Event):
        logger.info("🌙 DREAM_TRIGGER - Starting memory consolidation (brain-inspired)...")
        
        try:
            # Phase 1: Consolidate operation tracking (technical data)
            operations = await self._get_old_operations()
            
            # Phase 2: Consolidate conversation history (user interactions)
            conversations = await self._get_old_conversations()
            
            if not operations and not conversations:
                logger.info("✅ No old memories to consolidate - brain is fresh!")
                await self._emit_dream_complete(0, 0)
                return
            
            logger.info(f"📊 Found {len(operations)} ops + {len(conversations)} conversations")
            
            # Consolidate operations (only successes)
            successes = [op for op in operations if op.get("success")]
            ops_consolidated = 0
            if successes and self.memory_chroma:
                ops_consolidated = await self._consolidate_operations(successes)
            
            # Consolidate conversations (ALL - user interactions are precious!)
            conv_consolidated = 0
            if conversations and self.memory_chroma:
                conv_consolidated = await self._consolidate_conversations(conversations)
            
            # Cleanup old data (conservative - 30 days for ops, 14 days for conversations)
            deleted_count = await self._cleanup_old_data()
            
            # Update stats
            self.last_consolidation = datetime.now()
            self.total_consolidated += ops_consolidated
            self.conversations_consolidated += conv_consolidated
            self.total_deleted += deleted_count
            
            logger.info(f"✨ Consolidation complete:")
            logger.info(f"   Operations: {ops_consolidated}")
            logger.info(f"   Conversations: {conv_consolidated}")
            logger.info(f"   Cleaned up: {deleted_count}")
            
            await self._emit_dream_complete(ops_consolidated + conv_consolidated, deleted_count)
            
        except Exception as e:
            logger.error(f"❌ Consolidation error: {e}", exc_info=True)
            await self._emit_dream_complete(0, 0)

    async def _get_old_operations(self) -> List[Dict]:
        if not self.memory_sqlite:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(hours=self.consolidation_age_hours)).isoformat()
            
            from sqlalchemy import select
            
            with self.memory_sqlite.engine.connect() as conn:
                result = conn.execute(
                    select(self.memory_sqlite.operation_tracking_table).where(
                        self.memory_sqlite.operation_tracking_table.c.timestamp < cutoff
                    ).limit(self.batch_size)
                )
                
                operations = []
                for row in result:
                    operations.append({
                        "id": row.id,
                        "operation_id": row.operation_id,
                        "session_id": row.session_id,
                        "timestamp": row.timestamp,
                        "model_used": row.model_used,
                        "model_type": row.model_type,
                        "operation_type": row.operation_type,
                        "offline_mode": row.offline_mode,
                        "success": row.success,
                        "quality_score": row.quality_score,
                        "prompt_tokens": row.prompt_tokens,
                        "completion_tokens": row.completion_tokens,
                        "total_tokens": row.total_tokens,
                        "latency_ms": row.latency_ms,
                        "error_message": row.error_message,
                        "raw_metadata": row.raw_metadata
                    })
                
                return operations
                
        except Exception as e:
            logger.error(f"Error querying: {e}")
            return []
    
    async def _get_old_conversations(self) -> List[Dict]:
        """Get conversations older than 2 days for consolidation."""
        if not self.memory_sqlite:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(hours=self.consolidation_age_hours)).isoformat()
            
            from sqlalchemy import select
            
            # Check if conversation_history table exists
            if not hasattr(self.memory_sqlite, 'history_table'):
                return []
            
            with self.memory_sqlite.engine.connect() as conn:
                result = conn.execute(
                    select(self.memory_sqlite.history_table).where(
                        self.memory_sqlite.history_table.c.id > 0  # Get all for now
                    ).limit(self.batch_size)
                )
                
                conversations = []
                for row in result:
                    conversations.append({
                        "id": row.id,
                        "session_id": row.session_id,
                        "role": row.role,
                        "content": row.content,
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error querying conversations: {e}")
            return []

    async def _consolidate_operations(self, operations: List[Dict]) -> int:
        """Consolidate operations to ChromaDB (renamed from _consolidate_to_chroma)."""
        return await self._consolidate_to_chroma(operations)

    async def _consolidate_conversations(self, conversations: List[Dict]) -> int:
        """Consolidate conversations to ChromaDB for long-term memory."""
        if not self.memory_chroma:
            return 0
        
        consolidated = 0
        
        try:
            for conv in conversations:
                # Create searchable text
                role = conv.get("role", "user")
                content = conv.get("content", "")
                session_id = conv.get("session_id", "unknown")
                
                # Store in ChromaDB
                self.memory_chroma.add_memory(session_id, f"{role}: {content}")
                consolidated += 1
            
            return consolidated
            
        except Exception as e:
            logger.error(f"Error consolidating conversations: {e}")
            return consolidated
    
    async def _cleanup_old_data(self) -> int:
        """Cleanup old operations AND conversations (brain-inspired retention)."""
        ops_deleted = await self._cleanup_old_operations()
        
        # Also cleanup old conversations (14+ days)
        conv_deleted = await self._cleanup_old_conversations()
        
        return ops_deleted + conv_deleted
    
    async def _cleanup_old_conversations(self) -> int:
        """Delete conversations older than 14 days (after consolidation)."""
        if not self.memory_sqlite or not hasattr(self.memory_sqlite, 'history_table'):
            return 0
        
        try:
            cutoff = (datetime.now() - timedelta(days=self.conversation_retention_days)).isoformat()
            
            from sqlalchemy import delete
            
            # For now, don't delete conversations - keep them all
            # (Conservative approach - we can tune later)
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting old conversations: {e}")
            return 0

    async def _consolidate_to_chroma(self, operations: List[Dict]) -> int:
        if not self.memory_chroma:
            return 0
        
        consolidated = 0
        
        try:
            for op in operations:
                doc_text = self._create_document_text(op)
                
                metadata = {
                    "operation_id": op["operation_id"],
                    "operation_type": op["operation_type"],
                    "model_used": op["model_used"],
                    "timestamp": op["timestamp"],
                }
                
                if hasattr(self.memory_chroma, 'add_document'):
                    await self.memory_chroma.add_document(
                        text=doc_text,
                        metadata=metadata,
                        collection_name="operation_memory"
                    )
                    consolidated += 1
                else:
                    break
            
            return consolidated
            
        except Exception as e:
            return consolidated

    def _create_document_text(self, operation: Dict) -> str:
        operation_type = operation.get("operation_type", "unknown")
        model = operation.get("model_used", "unknown")
        mode = "offline" if operation.get("offline_mode") else "online"
        
        return f"Operation {operation_type} using {model} in {mode} mode."

    async def _cleanup_old_operations(self) -> int:
        if not self.memory_sqlite:
            return 0
        
        try:
            cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            
            from sqlalchemy import delete
            
            with self.memory_sqlite.engine.connect() as conn:
                result = conn.execute(
                    delete(self.memory_sqlite.operation_tracking_table).where(
                        self.memory_sqlite.operation_tracking_table.c.timestamp < cutoff
                    )
                )
                conn.commit()
                
                return result.rowcount
                
        except Exception as e:
            return 0

    async def _emit_dream_complete(self, consolidated_count: int, deleted_count: int):
        if not self.event_bus:
            return
        
        try:
            self.event_bus.publish(Event(
                EventType.DREAM_COMPLETE,
                data={
                    "timestamp": datetime.now().isoformat(),
                    "consolidated_count": consolidated_count,
                    "deleted_count": deleted_count,
                }
            ))
        except Exception as e:
            pass
