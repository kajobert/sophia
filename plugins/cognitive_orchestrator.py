"""
Strategic Orchestrator Plugin

HKA Layer: VĚDOMÍ (Neocortex) - Strategic Planning and Decision Making
Coordinates autonomous development workflow by delegating tasks to specialized plugins.

This plugin represents the highest cognitive layer in the Hierarchical Cognitive Architecture,
responsible for strategic thinking, planning, and coordinating complex multi-step operations.

According to 02_COGNITIVE_ARCHITECTURE.md:
"Neocortex - Strategic thinking, abstract reasoning, long-term planning"
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from plugins.base_plugin import BasePlugin
from core.context import SharedContext

logger = logging.getLogger(__name__)


class StrategicOrchestrator(BasePlugin):
    """
    Strategic orchestrator for autonomous development workflows.
    
    This cognitive plugin coordinates the entire autonomous mission lifecycle:
    1. Goal analysis and context gathering (SUBCONSCIOUS enrichment)
    2. Strategic planning and specification (CONSCIOUS decision)
    3. Delegation to external agents (if configured)
    4. Progress monitoring and quality validation
    5. Integration decision and learning consolidation
    
    HKA Layer: VĚDOMÍ (Neocortex)
    Dependencies:
    - cognitive_task_manager (PODVĚDOMÍ layer)
    - cognitive_notes_analyzer (PODVĚDOMÍ layer)
    - cognitive_ethical_guardian (INSTINKTY layer)
    - cognitive_doc_reader (optional - for context)
    - cognitive_code_reader (optional - for context)
    - cognitive_historian (optional - for pattern recognition)
    
    Note: This is a foundational implementation focused on coordination logic.
    External agent integration (Jules API, etc.) will be added in future iterations.
    """
    
    # Plugin Metadata
    name: str = "cognitive_orchestrator"
    plugin_type: str = "COGNITIVE"
    version: str = "1.0.0"
    
    def __init__(self):
        """Initialize the strategic orchestrator."""
        super().__init__()
        
        # Plugin dependencies (injected via setup)
        self.task_manager: Optional[BasePlugin] = None
        self.notes_analyzer: Optional[BasePlugin] = None
        self.ethical_guardian: Optional[BasePlugin] = None
        self.doc_reader: Optional[BasePlugin] = None
        self.code_reader: Optional[BasePlugin] = None
        self.historian: Optional[BasePlugin] = None
        self.llm: Optional[BasePlugin] = None
        
        # Configuration
        self.require_approval: bool = True  # Human approval gate
        self.max_concurrent_missions: int = 3
        
        logger.info("StrategicOrchestrator initialized")
    
    def setup(self, config: dict[str, Any]) -> None:
        """
        Configure the orchestrator with dependency injection.
        
        Args:
            config: Configuration dictionary with plugin dependencies:
                - cognitive_task_manager: Task tracking plugin
                - cognitive_notes_analyzer: Goal analysis plugin
                - cognitive_ethical_guardian: Ethics validation plugin
                - cognitive_doc_reader: Documentation context (optional)
                - cognitive_code_reader: Code context (optional)
                - cognitive_historian: Historical patterns (optional)
                - tool_llm: LLM for strategic decisions (optional)
                - require_approval: Human approval gate (default: True)
                - max_concurrent_missions: Max parallel missions (default: 3)
        """
        # Core dependencies (required)
        self.task_manager = config.get("cognitive_task_manager")
        self.notes_analyzer = config.get("cognitive_notes_analyzer")
        self.ethical_guardian = config.get("cognitive_ethical_guardian")
        
        # Optional dependencies for context enrichment
        self.doc_reader = config.get("cognitive_doc_reader")
        self.code_reader = config.get("cognitive_code_reader")
        self.historian = config.get("cognitive_historian")
        self.llm = config.get("tool_llm")
        
        # Configuration
        self.require_approval = config.get("require_approval", True)
        self.max_concurrent_missions = config.get("max_concurrent_missions", 3)
        
        logger.info(
            f"StrategicOrchestrator configured: "
            f"approval={self.require_approval}, "
            f"max_missions={self.max_concurrent_missions}"
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute orchestration action based on payload.
        
        Supported actions:
        - analyze_goal: Analyze a raw goal and create task
        - execute_mission: Execute autonomous mission for a task
        - get_mission_status: Get status of ongoing mission
        
        Args:
            context: Shared context with:
                - payload.action: Action to execute
                - payload.goal: Goal text (for analyze_goal)
                - payload.task_id: Task ID (for execute_mission, get_mission_status)
        
        Returns:
            Updated context with result in payload
        """
        action = context.payload.get("action")
        
        if action == "analyze_goal":
            result = await self._analyze_goal(
                context.payload.get("goal", ""),
                context
            )
            context.payload["result"] = result
        
        elif action == "execute_mission":
            result = await self._execute_mission(
                context.payload.get("task_id", ""),
                context
            )
            context.payload["result"] = result
        
        elif action == "get_mission_status":
            result = await self._get_mission_status(
                context.payload.get("task_id", "")
            )
            context.payload["result"] = result
        
        else:
            context.payload["result"] = {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        return context
    
    async def _analyze_goal(
        self,
        goal_text: str,
        context: SharedContext
    ) -> dict[str, Any]:
        """
        Analyze a raw goal and create a task.
        
        Workflow (HKA layers):
        1. PODVĚDOMÍ: Use NotesAnalyzer to structure goal
        2. INSTINKTY: Use EthicalGuardian to validate ethics
        3. VĚDOMÍ: Strategic decision to create task or reject
        4. PODVĚDOMÍ: Create task in TaskManager
        
        Args:
            goal_text: Raw goal text
            context: Shared context for plugin communication
        
        Returns:
            {
                "success": bool,
                "task_id": str (if successful),
                "analysis": dict (from NotesAnalyzer),
                "ethical_validation": dict (from EthicalGuardian),
                "message": str
            }
        """
        if not self.notes_analyzer or not self.ethical_guardian:
            return {
                "success": False,
                "error": "Missing required plugins (notes_analyzer or ethical_guardian)"
            }
        
        try:
            # STEP 1 (PODVĚDOMÍ): Analyze goal structure and context
            logger.info(f"Analyzing goal: {goal_text[:100]}...")
            
            analysis_context = SharedContext(
                session_id=context.session_id,
                user_input=goal_text,
                current_state="analyzing_goal",
                logger=logger,
                payload={"goals": [goal_text]}
            )
            
            analysis_context = await self.notes_analyzer.execute(analysis_context)
            analysis = analysis_context.payload.get("result", {})
            
            if not analysis or not isinstance(analysis, list) or len(analysis) == 0:
                return {
                    "success": False,
                    "error": "Goal analysis failed or returned empty result"
                }
            
            structured_goal = analysis[0]  # First analyzed goal
            
            # STEP 2 (INSTINKTY): Ethical validation
            logger.info("Performing ethical validation...")
            
            ethics_context = SharedContext(
                session_id=context.session_id,
                user_input=goal_text,
                current_state="validating_ethics",
                logger=logger,
                payload={
                    "action": "validate_goal",
                    "goal": structured_goal
                }
            )
            
            ethics_context = await self.ethical_guardian.execute(ethics_context)
            ethical_validation = ethics_context.payload.get("result", {})
            
            if not ethical_validation.get("approved", False):
                return {
                    "success": False,
                    "analysis": structured_goal,
                    "ethical_validation": ethical_validation,
                    "message": (
                        "Goal rejected due to ethical concerns: "
                        f"{ethical_validation.get('concerns', [])}"
                    )
                }
            
            # STEP 3 (VĚDOMÍ): Strategic decision - create task
            logger.info("Creating task...")
            
            task_context = SharedContext(
                session_id=context.session_id,
                user_input=goal_text,
                current_state="creating_task",
                logger=logger,
                payload={
                    "action": "create_task",
                    "goal": structured_goal,
                    "context": {
                        "ethical_validation": ethical_validation,
                        "analyzed_at": datetime.now().isoformat()
                    }
                }
            )
            
            task_context = await self.task_manager.execute(task_context)
            task_id = task_context.payload.get("result")
            
            if not task_id:
                return {
                    "success": False,
                    "error": "Task creation failed"
                }
            
            return {
                "success": True,
                "task_id": task_id,
                "analysis": structured_goal,
                "ethical_validation": ethical_validation,
                "message": f"Task {task_id} created and ready for execution"
            }
        
        except Exception as e:
            logger.error(f"Goal analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Goal analysis error: {str(e)}"
            }
    
    async def _execute_mission(
        self,
        task_id: str,
        context: SharedContext
    ) -> dict[str, Any]:
        """
        Execute autonomous mission for a task.
        
        This is a foundational implementation that demonstrates the workflow.
        Future versions will integrate with external coding agents (Jules API, etc.).
        
        Current workflow:
        1. Load task from TaskManager
        2. Gather context (similar tasks, relevant docs)
        3. Update task status to 'analyzing'
        4. Return strategic plan (future: delegate to external agent)
        
        Args:
            task_id: Task identifier
            context: Shared context
        
        Returns:
            {
                "success": bool,
                "task_id": str,
                "status": str,
                "plan": dict (strategic plan for implementation),
                "message": str
            }
        """
        if not self.task_manager:
            return {
                "success": False,
                "error": "TaskManager not available"
            }
        
        try:
            # STEP 1: Load task
            logger.info(f"Executing mission for task {task_id}...")
            
            get_context = SharedContext(
                session_id=context.session_id,
                user_input="",
                current_state="loading_task",
                logger=logger,
                payload={
                    "action": "get_task",
                    "task_id": task_id
                }
            )
            
            get_context = await self.task_manager.execute(get_context)
            task = get_context.payload.get("result")
            
            if not task:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # STEP 2: Gather context (PODVĚDOMÍ - pattern recognition)
            similar_tasks = []
            if self.task_manager:
                similar_context = SharedContext(
                    session_id=context.session_id,
                    user_input="",
                    current_state="finding_similar",
                    logger=logger,
                    payload={
                        "action": "get_similar_tasks",
                        "task": task,
                        "top_k": 3
                    }
                )
                
                similar_context = await self.task_manager.execute(similar_context)
                similar_tasks = similar_context.payload.get("result", [])
            
            # STEP 3: Update task status
            update_context = SharedContext(
                session_id=context.session_id,
                user_input="",
                current_state="updating_task",
                logger=logger,
                payload={
                    "action": "update_task",
                    "task_id": task_id,
                    "status": "analyzing",
                    "notes": "Strategic analysis in progress"
                }
            )
            
            await self.task_manager.execute(update_context)
            
            # STEP 4: Create strategic plan (VĚDOMÍ - strategic thinking)
            plan = {
                "task_id": task_id,
                "goal": task.get("goal", {}),
                "context": {
                    "similar_tasks_found": len(similar_tasks),
                    "similar_tasks": similar_tasks[:3]  # Top 3
                },
                "next_steps": [
                    "Formulate detailed specification",
                    "Delegate to external coding agent (future)",
                    "Monitor progress",
                    "Validate results",
                    "Integrate if approved"
                ],
                "estimated_phases": {
                    "specification": "Strategic planning",
                    "delegation": "Not yet implemented - manual development required",
                    "validation": "QA and ethical review",
                    "integration": "Safe integration with rollback"
                }
            }
            
            logger.info(f"Mission plan created for task {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "status": "analyzing",
                "plan": plan,
                "message": (
                    f"Strategic plan created. Task is in 'analyzing' state. "
                    "External agent integration coming in future updates."
                )
            }
        
        except Exception as e:
            logger.error(f"Mission execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Mission execution error: {str(e)}"
            }
    
    async def _get_mission_status(self, task_id: str) -> dict[str, Any]:
        """
        Get status of an ongoing mission.
        
        Args:
            task_id: Task identifier
        
        Returns:
            {
                "success": bool,
                "task_id": str,
                "status": str,
                "history": list,
                "message": str
            }
        """
        if not self.task_manager:
            return {
                "success": False,
                "error": "TaskManager not available"
            }
        
        try:
            get_context = SharedContext(
                session_id="mission_status",
                user_input="",
                current_state="getting_status",
                logger=logger,
                payload={
                    "action": "get_task",
                    "task_id": task_id
                }
            )
            
            get_context = await self.task_manager.execute(get_context)
            task = get_context.payload.get("result")
            
            if not task:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            return {
                "success": True,
                "task_id": task_id,
                "status": task.get("status", "unknown"),
                "history": task.get("history", []),
                "message": f"Task {task_id} status: {task.get('status', 'unknown')}"
            }
        
        except Exception as e:
            logger.error(f"Status check failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Status check error: {str(e)}"
            }
