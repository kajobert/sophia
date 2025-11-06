"""
Cognitive Notes Reader Plugin - AMI 1.0

Reads roberts-notes.txt and autonomously creates tasks from user's ideas.
Triggered by PROACTIVE_HEARTBEAT events to check for file modifications.

This is the foundation for proactive autonomous operation - Sophia reads
your notes and creates her own work without explicit instructions.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveNotesReader(BasePlugin):
    """
    Reads roberts-notes.txt and creates tasks from ideas.
    
    Workflow:
    1. Listen to PROACTIVE_HEARTBEAT events
    2. Check if roberts-notes.txt was modified
    3. If modified, read content
    4. Send to LLM to extract actionable tasks
    5. Parse JSON response
    6. Enqueue tasks to SimplePersistentQueue
    """

    def __init__(self):
        super().__init__()
        self.notes_path = Path("roberts-notes.txt")
        self.last_modified: Optional[float] = None
        self.last_check: Optional[float] = None
        self._all_plugins_map = None  # Will be set during setup

    @property
    def name(self) -> str:
        return "cognitive_notes_reader"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: Dict[str, Any]) -> None:
        """Initialize plugin."""
        try:
            super().setup(config)
            
            logger.info(f"[{self.name}] Starting setup...")
            
            # Store all_plugins_map for LLM access
            if 'all_plugins_map' in config:
                self._all_plugins_map = config['all_plugins_map']
                logger.info(f"[{self.name}] Stored all_plugins_map")
            
            # Register event subscriber if event_bus is available
            if 'event_bus' in config and config['event_bus'] is not None:
                event_bus = config['event_bus']
                event_bus.subscribe(EventType.PROACTIVE_HEARTBEAT, self.handle_event)
                logger.info(f"[{self.name}] ✅ Subscribed to PROACTIVE_HEARTBEAT events")
            else:
                logger.warning(f"[{self.name}] ⚠️  EventBus not available, plugin will not work!")
            
            # Create notes file if doesn't exist
            if not self.notes_path.exists():
                self.notes_path.write_text(
                    "# Robert's Notes - Ideas for Sophia\n\n"
                    "Sophia reads this file and autonomously creates tasks from your ideas.\n\n"
                    "## Example:\n"
                    "- Implementovat feature XYZ pro lepší analýzu\n"
                    "- Prozkoumat knihovnu ABC pro optimalizaci\n"
                    "- Vytvořit dokumentaci pro modul DEF\n",
                    encoding="utf-8"
                )
                logger.info(f"[{self.name}] Created roberts-notes.txt template")
            else:
                logger.info(f"[{self.name}] roberts-notes.txt exists ({self.notes_path.stat().st_size} bytes)")
                
            logger.info(f"[{self.name}] ✅ Setup complete")
            
        except Exception as e:
            logger.error(f"[{self.name}] ❌ Setup failed: {e}", exc_info=True)

    async def handle_event(self, event: Event) -> None:
        """Handle PROACTIVE_HEARTBEAT events."""
        if event.event_type == EventType.PROACTIVE_HEARTBEAT:
            await self._check_and_process_notes()

    async def _check_and_process_notes(self) -> None:
        """Check if notes file changed and process if needed."""
        try:
            # Check if file exists
            if not self.notes_path.exists():
                return

            # Get file modification time
            current_mtime = self.notes_path.stat().st_mtime

            # Skip if not modified since last check
            if self.last_modified is not None and current_mtime == self.last_modified:
                return

            # Update last modified time
            old_mtime = self.last_modified
            self.last_modified = current_mtime

            logger.info(
                f"[{self.name}] roberts-notes.txt modified, processing... "
                f"(was: {old_mtime}, now: {current_mtime})"
            )

            # Read notes content
            notes_content = self.notes_path.read_text(encoding="utf-8")

            # Skip if file is empty or just template
            if len(notes_content.strip()) < 50:
                logger.debug(f"[{self.name}] Notes file too short, skipping")
                return

            # Extract tasks using LLM
            tasks = await self._extract_tasks_from_notes(notes_content)

            # Enqueue tasks
            if tasks:
                await self._enqueue_tasks(tasks)
                logger.info(f"[{self.name}] Created {len(tasks)} tasks from roberts-notes.txt")
            else:
                logger.debug(f"[{self.name}] No actionable tasks found in notes")

        except Exception as e:
            logger.error(f"[{self.name}] Error processing notes: {e}", exc_info=True)

    async def _extract_tasks_from_notes(self, notes_content: str) -> list:
        """
        Use LLM to extract actionable tasks from notes.
        
        Returns:
            List of task dicts: [{"priority": 90, "instruction": "...", "category": "..."}]
        """
        # Get LLM plugin from stored map
        llm_plugin = None
        
        if self._all_plugins_map:
            llm_plugin = self._all_plugins_map.get("tool_local_llm")
            if not llm_plugin:
                llm_plugin = self._all_plugins_map.get("tool_llm")
        
        if not llm_plugin:
            logger.warning(f"[{self.name}] No LLM plugin available, cannot extract tasks")
            return []

        # Create extraction prompt
        extraction_prompt = self._create_extraction_prompt(notes_content)

        try:
            # Call LLM
            context = SharedContext(
                user_input=extraction_prompt,
                session_id=f"notes-reader-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                current_state="EXTRACTING_TASKS",
                logger=logger,
                offline_mode=getattr(self.context, 'offline_mode', False) if hasattr(self, 'context') else False
            )
            
            # Execute LLM
            result_context = await llm_plugin.execute(context)
            
            # Extract text response from SharedContext
            if hasattr(result_context, 'payload') and 'llm_response' in result_context.payload:
                response_text = result_context.payload['llm_response']
                logger.info(f"[{self.name}] LLM returned {len(response_text)} chars: {response_text[:200]}...")
            else:
                logger.error(f"[{self.name}] LLM returned unexpected format: {type(result_context)}")
                return []
            
            # Parse JSON response
            tasks = self._parse_llm_response(response_text)
            
            return tasks

        except Exception as e:
            logger.error(f"[{self.name}] LLM extraction failed: {e}", exc_info=True)
            return []

    def _create_extraction_prompt(self, notes_content: str) -> str:
        """Create prompt for LLM to extract tasks."""
        return f"""Extract actionable tasks from Robert's notes for SOPHIA AI assistant.

NOTES:
{notes_content}

RULES:
1. Identify ONLY actionable tasks (not vague ideas)
2. Prioritize: 90-100=urgent, 50-89=important, 1-49=nice-to-have
3. Categories: development, research, optimization, documentation, testing, bugfix

RESPONSE FORMAT - CRITICAL:
You MUST return a JSON ARRAY (list), even if there's only ONE task!

CORRECT format (array with square brackets):
[
  {{"priority": 85, "instruction": "Test Phase 1 implementation", "category": "development"}},
  {{"priority": 70, "instruction": "Create unit tests for plugin", "category": "testing"}}
]

WRONG format (single object without array):
{{"priority": 85, "instruction": "...", "category": "..."}}  ← THIS IS WRONG!

If no tasks found, return empty array: []

Remember: ALWAYS use square brackets [] for the array!
"""

    def _parse_llm_response(self, response: str) -> list:
        """Parse LLM response and extract task list."""
        try:
            # Try to find JSON array in response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
            
            # Parse JSON
            tasks = json.loads(response)
            
            # Handle wrapped response (e.g., {"tasks": [...]})
            if isinstance(tasks, dict) and 'tasks' in tasks:
                logger.info(f"[{self.name}] LLM wrapped tasks in object, extracting array")
                tasks = tasks['tasks']
            
            # Validate structure
            if not isinstance(tasks, list):
                logger.warning(f"[{self.name}] LLM returned single object instead of array, wrapping it")
                # If LLM returned a single task object, wrap it in an array
                if isinstance(tasks, dict) and 'instruction' in tasks:
                    tasks = [tasks]
                else:
                    logger.error(f"[{self.name}] LLM response is not a valid task structure: {response[:100]}")
                    return []
            
            # Validate each task
            valid_tasks = []
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                
                # Required fields
                if "instruction" not in task or "priority" not in task:
                    continue
                
                # Ensure category exists
                if "category" not in task:
                    task["category"] = "development"
                
                # Validate priority range
                task["priority"] = max(1, min(100, int(task["priority"])))
                
                valid_tasks.append(task)
            
            return valid_tasks

        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] Failed to parse JSON from LLM: {e}")
            logger.debug(f"LLM response was: {response[:200]}")
            return []
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing LLM response: {e}", exc_info=True)
            return []

    async def _enqueue_tasks(self, tasks: list) -> None:
        """Enqueue extracted tasks to persistent queue."""
        try:
            # Get queue from context
            queue = None
            if hasattr(self, 'context') and self.context:
                queue = getattr(self.context, 'queue', None)
            
            if not queue:
                # Try to import and create queue directly
                from core.simple_persistent_queue import SimplePersistentQueue
                queue = SimplePersistentQueue('.data/tasks.sqlite')
            
            if not queue:
                logger.error(f"[{self.name}] No task queue available")
                return

            # Enqueue each task
            for task in tasks:
                task_data = {
                    "instruction": task["instruction"],
                    "metadata": {
                        "source": "roberts-notes",
                        "category": task.get("category", "development"),
                        "created_at": datetime.now().isoformat(),
                        "auto_generated": True
                    }
                }
                
                task_id = queue.enqueue(task_data, priority=task["priority"])
                
                logger.info(
                    f"[{self.name}] Enqueued task #{task_id}: {task['instruction'][:60]}... "
                    f"(priority={task['priority']}, category={task.get('category')})"
                )

        except Exception as e:
            logger.error(f"[{self.name}] Error enqueueing tasks: {e}", exc_info=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """Manual execution for testing."""
        self.context = context
        await self._check_and_process_notes()
        return context
