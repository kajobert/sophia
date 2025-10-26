"""
Cognitive Task Manager Plugin

HKA Layer: SUBCONSCIOUS (Pattern Recognition & Long-term Tracking)
Purpose: Track autonomous tasks, find patterns in history, consolidate learning

This plugin operates at the SUBCONSCIOUS layer (Mammalian Brain), managing
long-term task persistence, pattern recognition via ChromaDB, and insight
consolidation from completed missions.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from plugins.base_plugin import BasePlugin
from core.context import SharedContext

logger = logging.getLogger(__name__)


class TaskManager(BasePlugin):
    """
    Subconscious task tracking and pattern recognition.
    
    Manages autonomous task lifecycle, finds similar historical tasks,
    and consolidates learned insights into long-term memory.
    
    HKA Layer: SUBCONSCIOUS (Mammalian Brain)
    - Long-term tracking (persistence)
    - Pattern recognition (similar tasks via ChromaDB)
    - Learning consolidation (insight extraction)
    
    Dependencies:
    - memory_chroma (for similar task search)
    - tool_file_system (for task persistence)
    """
    
    name = "cognitive_task_manager"
    plugin_type = "COGNITIVE"
    version = "1.0.0"
    
    TASK_STATUSES = [
        "pending",      # Task created, awaiting analysis
        "analyzing",    # Being analyzed by SUBCONSCIOUS layer
        "delegated",    # Delegated to external agent (Jules)
        "reviewing",    # Code review and validation in progress
        "integrating",  # Changes being integrated into system
        "completed",    # Successfully completed
        "failed"        # Failed with errors
    ]
    
    PRIORITY_LEVELS = ["high", "medium", "low"]
    
    def __init__(self):
        super().__init__()
        self.tasks_dir: Optional[Path] = None
        self.memory_chroma = None
        self.file_system = None
    
    def setup(self, config: dict):
        """
        Setup task manager with dependencies.
        
        Args:
            config: Configuration dict containing:
                - enabled: bool
                - tasks_dir: Path to task storage (default: data/tasks/)
                - memory_chroma: ChromaDB plugin instance (injected by Kernel)
                - tool_file_system: FileSystem plugin instance (injected by Kernel)
        """
        self.enabled = config.get("enabled", True)
        
        # Task storage directory
        tasks_dir = config.get("tasks_dir", "data/tasks")
        self.tasks_dir = Path(tasks_dir)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Dependencies (injected by Kernel)
        self.memory_chroma = config.get("memory_chroma")
        self.file_system = config.get("tool_file_system")
        
        logger.info(
            f"TaskManager initialized: tasks_dir={self.tasks_dir}, "
            f"memory_chroma={'✓' if self.memory_chroma else '✗'}, "
            f"file_system={'✓' if self.file_system else '✗'}"
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute task management command.
        
        Supported commands in context.payload:
        - action: "create_task" - Create new task
        - action: "update_task" - Update task status
        - action: "get_task" - Get task details
        - action: "list_tasks" - List all tasks
        - action: "get_similar_tasks" - Find similar tasks
        - action: "consolidate_insights" - Consolidate task insights
        
        Returns:
            SharedContext: Updated context with result in payload["result"]
        """
        action = context.payload.get("action")
        
        if action == "create_task":
            result = await self._create_task(context.payload)
            context.payload["result"] = result
        elif action == "update_task":
            result = await self._update_task(context.payload)
            context.payload["result"] = result
        elif action == "get_task":
            result = await self._get_task(context.payload)
            context.payload["result"] = result
        elif action == "list_tasks":
            result = await self._list_tasks(context.payload)
            context.payload["result"] = result
        elif action == "get_similar_tasks":
            result = await self._get_similar_tasks(context.payload, context)
            context.payload["result"] = result
        elif action == "consolidate_insights":
            result = await self._consolidate_insights(context.payload, context)
            context.payload["result"] = result
        else:
            context.payload["result"] = {"error": f"Unknown action: {action}"}
        
        return context
    
    async def _create_task(self, payload: dict) -> dict:
        """
        Create new task from approved goal.
        
        Args:
            payload: Must contain:
                - goal: dict from NotesAnalyzer (raw_idea, formulated_goal, etc.)
                - context: dict with enriched context
                - priority: "high"|"medium"|"low" (optional, default: "medium")
        
        Returns:
            dict: {
                "task_id": str,
                "status": "pending",
                "created_at": timestamp
            }
        """
        goal = payload.get("goal")
        if not goal:
            return {"error": "Missing required field: goal"}
        
        context_data = payload.get("context", {})
        priority = payload.get("priority", "medium")
        
        if priority not in self.PRIORITY_LEVELS:
            return {"error": f"Invalid priority: {priority}. Must be one of {self.PRIORITY_LEVELS}"}
        
        # Generate task ID
        task_id = str(uuid4())
        
        # Create task structure
        task = {
            "task_id": task_id,
            "title": goal.get("formulated_goal", goal.get("raw_idea", "Untitled Task"))[:100],
            "description": goal.get("formulated_goal", goal.get("raw_idea", "")),
            "goal": goal,
            "context": context_data,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending",
                    "notes": "Task created from approved goal"
                }
            ]
        }
        
        # Persist to disk
        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task, indent=2))
        
        logger.info(f"Created task {task_id}: {task['title']}")
        
        return {
            "task_id": task_id,
            "status": "pending",
            "created_at": task["created_at"],
            "title": task["title"]
        }
    
    async def _update_task(self, payload: dict) -> dict:
        """
        Update task status and add notes.
        
        Args:
            payload: Must contain:
                - task_id: str
                - status: str (must be in TASK_STATUSES)
                - notes: str (optional)
        
        Returns:
            dict: {
                "task_id": str,
                "status": str,
                "updated_at": timestamp
            }
        """
        task_id = payload.get("task_id")
        new_status = payload.get("status")
        notes = payload.get("notes", "")
        
        if not task_id:
            return {"error": "Missing required field: task_id"}
        if not new_status:
            return {"error": "Missing required field: status"}
        if new_status not in self.TASK_STATUSES:
            return {"error": f"Invalid status: {new_status}. Must be one of {self.TASK_STATUSES}"}
        
        # Load task
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return {"error": f"Task not found: {task_id}"}
        
        task = json.loads(task_file.read_text())
        
        # Update status
        old_status = task["status"]
        task["status"] = new_status
        task["updated_at"] = datetime.now().isoformat()
        
        # Add history entry
        task["history"].append({
            "timestamp": datetime.now().isoformat(),
            "status": new_status,
            "notes": notes or f"Status changed from {old_status} to {new_status}"
        })
        
        # Persist changes
        task_file.write_text(json.dumps(task, indent=2))
        
        logger.info(f"Updated task {task_id}: {old_status} → {new_status}")
        
        return {
            "task_id": task_id,
            "status": new_status,
            "updated_at": task["updated_at"]
        }
    
    async def _get_task(self, payload: dict) -> dict:
        """
        Get task details.
        
        Args:
            payload: Must contain:
                - task_id: str
        
        Returns:
            dict: Full task object or error
        """
        task_id = payload.get("task_id")
        if not task_id:
            return {"error": "Missing required field: task_id"}
        
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return {"error": f"Task not found: {task_id}"}
        
        task = json.loads(task_file.read_text())
        return task
    
    async def _list_tasks(self, payload: dict) -> dict:
        """
        List all tasks.
        
        Args:
            payload: Optional filters:
                - status: str (filter by status)
                - priority: str (filter by priority)
                - limit: int (max results, default: 100)
        
        Returns:
            dict: {
                "tasks": [list of task summaries],
                "total": int
            }
        """
        status_filter = payload.get("status")
        priority_filter = payload.get("priority")
        limit = payload.get("limit", 100)
        
        tasks = []
        
        for task_file in self.tasks_dir.glob("*.json"):
            task = json.loads(task_file.read_text())
            
            # Apply filters
            if status_filter and task["status"] != status_filter:
                continue
            if priority_filter and task["priority"] != priority_filter:
                continue
            
            # Summary only
            tasks.append({
                "task_id": task["task_id"],
                "title": task["title"],
                "status": task["status"],
                "priority": task["priority"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"]
            })
        
        # Sort by priority (high first) then by created_at (newest first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(
            key=lambda t: (priority_order.get(t["priority"], 3), -datetime.fromisoformat(t["created_at"]).timestamp())
        )
        
        # Apply limit
        tasks = tasks[:limit]
        
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    
    async def _get_similar_tasks(self, payload: dict, context) -> dict:
        """
        Find similar historical tasks using ChromaDB.
        
        This is the "Subconscious" memory recall - finding patterns
        from past experiences.
        
        Args:
            payload: Must contain:
                - task: dict (current task to compare)
                - top_k: int (number of similar tasks to return, default: 5)
            context: SharedContext for creating sub-queries
        
        Returns:
            dict: {
                "similar_tasks": [list of similar task summaries],
                "count": int
            }
        """
        task = payload.get("task")
        top_k = payload.get("top_k", 5)
        
        if not task:
            return {"error": "Missing required field: task"}
        
        if not self.memory_chroma:
            logger.warning("ChromaDB not available, cannot find similar tasks")
            return {"similar_tasks": [], "count": 0}
        
        # Create search query from task
        query = f"{task.get('title', '')} {task.get('description', '')}"
        
        # Search ChromaDB for similar task descriptions
        # Memory format: {"text": task_description, "metadata": {"task_id": ...}}
        try:
            from core.context import SharedContext
            
            search_context = SharedContext(
                session_id=context.session_id,
                current_state=context.current_state,
                logger=context.logger,
                user_input=query,
                payload={"query": query, "top_k": top_k, "collection": "tasks"}
            )
            
            search_result = await self.memory_chroma.execute(search_context)
            
            if "error" in search_result:
                return {"similar_tasks": [], "count": 0}
            
            memories = search_result.get("memories", [])
            
            # Load full task details for each similar task
            similar_tasks = []
            for memory in memories:
                task_id = memory.get("metadata", {}).get("task_id")
                if task_id:
                    task_file = self.tasks_dir / f"{task_id}.json"
                    if task_file.exists():
                        similar_task = json.loads(task_file.read_text())
                        similar_tasks.append({
                            "task_id": similar_task["task_id"],
                            "title": similar_task["title"],
                            "status": similar_task["status"],
                            "similarity_score": memory.get("score", 0.0)
                        })
            
            return {
                "similar_tasks": similar_tasks,
                "count": len(similar_tasks)
            }
        
        except Exception as e:
            logger.error(f"Error searching similar tasks: {e}")
            return {"similar_tasks": [], "count": 0}
    
    async def _consolidate_insights(self, payload: dict, context) -> dict:
        """
        Consolidate insights from completed task into long-term memory.
        
        This is the "Dreaming" process - extracting key learnings and
        storing them in ChromaDB for future pattern recognition.
        
        Args:
            payload: Must contain:
                - task_id: str
            context: SharedContext for creating sub-queries
        
        Returns:
            dict: {
                "task_id": str,
                "insights_stored": int,
                "status": "success"|"error"
            }
        """
        task_id = payload.get("task_id")
        if not task_id:
            return {"error": "Missing required field: task_id"}
        
        # Load task
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return {"error": f"Task not found: {task_id}"}
        
        task = json.loads(task_file.read_text())
        
        if not self.memory_chroma:
            logger.warning("ChromaDB not available, cannot consolidate insights")
            return {
                "task_id": task_id,
                "insights_stored": 0,
                "status": "skipped",
                "reason": "ChromaDB not available"
            }
        
        # Extract insights from task
        insights = []
        
        # 1. Store task description for future similarity search
        insights.append({
            "text": f"{task['title']}\n{task['description']}",
            "metadata": {
                "task_id": task_id,
                "type": "task_description",
                "status": task["status"],
                "created_at": task["created_at"]
            }
        })
        
        # 2. Store key learnings from history notes
        for entry in task.get("history", []):
            notes = entry.get("notes", "")
            if notes and len(notes) > 50:  # Only meaningful notes
                insights.append({
                    "text": notes,
                    "metadata": {
                        "task_id": task_id,
                        "type": "learning",
                        "timestamp": entry["timestamp"]
                    }
                })
        
        # Store insights in ChromaDB
        try:
            from core.context import SharedContext
            
            for insight in insights:
                memory_context = SharedContext(
                    session_id=context.session_id,
                    current_state=context.current_state,
                    logger=context.logger,
                    user_input=insight["text"],
                    payload={
                        "text": insight["text"],
                        "metadata": insight["metadata"],
                        "collection": "tasks"
                    }
                )
                
                await self.memory_chroma.execute(memory_context)
            
            logger.info(f"Consolidated {len(insights)} insights from task {task_id}")
            
            return {
                "task_id": task_id,
                "insights_stored": len(insights),
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error consolidating insights: {e}")
            return {
                "task_id": task_id,
                "insights_stored": 0,
                "status": "error",
                "reason": str(e)
            }
