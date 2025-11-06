"""
SOPHIA Self-Reflection Plugin

Provides Sophia with the ability to log her own thoughts, decisions, and learnings
into a persistent journal for future analysis and self-improvement.

This forms the foundation for Phase 3: Self-Tuning Framework from 01_SOPHIA AMI 1.0.md
"""
import logging
from datetime import datetime
from pathlib import Path
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class SelfReflectionPlugin(BasePlugin):
    """Allows Sophia to write reflective journal entries about her operations."""
    
    def __init__(self):
        self.journal_path = Path("sandbox/sophia_reflection_journal.md")
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize journal with header if it doesn't exist
        if not self.journal_path.exists():
            with open(self.journal_path, "w", encoding="utf-8") as f:
                f.write("# SOPHIA Self-Reflection Journal\n\n")
                f.write("*This journal contains Sophia's autonomous reflections, learnings, and insights.*\n\n")
                f.write(f"Journal initialized: {datetime.utcnow().isoformat()}Z\n\n")
                f.write("---\n\n")
    
    @property
    def name(self) -> str:
        return "tool_self_reflection"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        """Configure the plugin."""
        logger.info(f"Self-reflection journal: {self.journal_path.absolute()}")
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Not used - this plugin provides methods for explicit calls."""
        return context
    
    def log(self, context: str, message: str, category: str = "REFLECTION") -> bool:
        """
        Append a timestamped reflection entry to the journal.
        
        Args:
            context: Brief context about what Sophia is doing (e.g., "Processing task #42")
            message: The reflection/insight to log
            category: Type of entry (REFLECTION, LEARNING, DECISION, ERROR, SUCCESS)
        
        Returns:
            True if logged successfully, False otherwise
        
        Example:
            >>> plugin.log(
            ...     context="Processing file write task",
            ...     message="Discovered that 8B model struggles with nested JSON. Should simplify prompts.",
            ...     category="LEARNING"
            ... )
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(f"## [{category}] {timestamp}\n\n")
                f.write(f"**Context:** {context}\n\n")
                f.write(f"{message}\n\n")
                f.write("---\n\n")
            
            logger.info(f"Reflection logged: [{category}] {context}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to write reflection: {e}")
            return False
    
    def log_task_start(self, task_id: int, instruction: str) -> bool:
        """Log the start of a new task."""
        return self.log(
            context=f"Task #{task_id} started",
            message=f"Beginning work on: {instruction[:200]}",
            category="TASK_START"
        )
    
    def log_task_complete(self, task_id: int, result: str) -> bool:
        """Log successful task completion."""
        return self.log(
            context=f"Task #{task_id} completed",
            message=f"Result: {result[:500]}",
            category="SUCCESS"
        )
    
    def log_task_failed(self, task_id: int, error: str) -> bool:
        """Log task failure for future learning."""
        return self.log(
            context=f"Task #{task_id} failed",
            message=f"Error encountered: {error[:500]}\n\nThis failure will be analyzed during next reflection cycle.",
            category="ERROR"
        )
    
    def log_insight(self, insight: str) -> bool:
        """Log a general insight or observation."""
        return self.log(
            context="Autonomous insight",
            message=insight,
            category="LEARNING"
        )
    
    def log_decision(self, decision: str, reasoning: str) -> bool:
        """Log an important decision and its reasoning."""
        return self.log(
            context="Decision made",
            message=f"**Decision:** {decision}\n\n**Reasoning:** {reasoning}",
            category="DECISION"
        )
    
    def get_recent_entries(self, count: int = 10) -> list:
        """
        Read the last N entries from the journal.
        
        Args:
            count: Number of entries to return (default: 10)
        
        Returns:
            List of entry strings
        """
        try:
            if not self.journal_path.exists():
                return []
            
            with open(self.journal_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Split by entry separator
            entries = content.split("---\n")
            
            # Filter out header and empty entries
            entries = [e.strip() for e in entries if e.strip() and e.strip() != "# SOPHIA Self-Reflection Journal"]
            
            # Return last N entries
            return entries[-count:]
        
        except Exception as e:
            logger.error(f"Failed to read journal: {e}")
            return []
