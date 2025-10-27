"""
Autonomous Interface Plugin

HKA Layer: INTERFACE (User Command Processing)
Detects 'autonomous:' commands and delegates to Strategic Orchestrator.

This interface plugin maintains clean separation of concerns by keeping
command detection logic out of the Core kernel, in compliance with
Golden Rule #1 from AGENTS.md: "DON'T TOUCH THE CORE!"
"""

import logging
from typing import Any

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class AutonomousInterface(BasePlugin):
    """
    Interface plugin for autonomous development missions.
    
    This plugin intercepts user commands starting with 'autonomous:' and
    orchestrates the autonomous workflow by delegating to the Strategic
    Orchestrator (cognitive_orchestrator).
    
    Command format:
        autonomous: <goal description>
    
    Example:
        autonomous: implement user authentication with JWT tokens
    
    Workflow:
    1. Detect 'autonomous:' prefix in user input
    2. Extract goal text
    3. Delegate to cognitive_orchestrator for analysis
    4. Delegate to cognitive_orchestrator for execution
    5. Update WORKLOG.md with mission progress
    6. Return formatted result to user
    
    HKA Layer: INTERFACE (not part of cognitive hierarchy)
    Dependencies:
    - cognitive_orchestrator (CONSCIOUSNESS layer) - required
    """
    
    # Plugin Metadata
    name: str = "interface_autonomous"
    plugin_type = PluginType.INTERFACE
    version: str = "1.0.0"
    
    def __init__(self):
        """Initialize the autonomous interface."""
        super().__init__()
        self.orchestrator = None
        self.worklog_path = "WORKLOG.md"
        logger.info("AutonomousInterface initialized")
    
    def setup(self, config: dict[str, Any]) -> None:
        """
        Configure the interface with orchestrator dependency.
        
        Args:
            config: Configuration dictionary with:
                - cognitive_orchestrator: Strategic orchestrator plugin (required)
                - worklog_path: Path to WORKLOG.md (default: 'WORKLOG.md')
        """
        self.orchestrator = config.get("cognitive_orchestrator")
        self.worklog_path = config.get("worklog_path", "WORKLOG.md")
        
        if not self.orchestrator:
            logger.warning(
                "AutonomousInterface: cognitive_orchestrator not configured. "
                "Autonomous commands will not work."
            )
        
        logger.info(
            f"AutonomousInterface configured: "
            f"orchestrator={'available' if self.orchestrator else 'missing'}"
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Process autonomous commands.
        
        Detects 'autonomous:' prefix and delegates to orchestrator.
        If input doesn't match, returns context unchanged (pass-through).
        
        Args:
            context: Shared context with user input
        
        Returns:
            Updated context with autonomous_response if command detected,
            otherwise unchanged context for other plugins to process
        """
        user_input = context.user_input.strip()
        
        # Check if this is an autonomous command
        if not user_input.startswith("autonomous:"):
            # Not our command, pass through
            return context
        
        # Extract goal text
        goal_text = user_input[11:].strip()  # Remove "autonomous:" prefix
        
        if not goal_text:
            context.autonomous_response = (
                "Error: No goal specified. "
                "Usage: autonomous: <goal description>"
            )
            return context
        
        # Check if orchestrator is available
        if not self.orchestrator:
            context.autonomous_response = (
                "Error: Strategic Orchestrator not available. "
                "Cannot execute autonomous mission."
            )
            return context
        
        try:
            # Execute autonomous workflow
            result = await self._execute_autonomous_workflow(
                goal_text=goal_text,
                context=context
            )
            
            context.autonomous_response = result
            return context
        
        except Exception as e:
            logger.error(f"Autonomous workflow failed: {e}", exc_info=True)
            context.autonomous_response = (
                f"Error executing autonomous mission: {str(e)}"
            )
            return context
    
    async def _execute_autonomous_workflow(
        self,
        goal_text: str,
        context: SharedContext
    ) -> str:
        """
        Execute the full autonomous workflow.
        
        Phases:
        1. Goal analysis (create task via orchestrator)
        2. Mission execution (strategic planning via orchestrator)
        3. WORKLOG update
        4. Format user response
        
        Args:
            goal_text: User's goal description
            context: Current shared context
        
        Returns:
            Formatted result message for user
        """
        logger.info(f"Executing autonomous workflow for goal: {goal_text}")
        
        # Phase 1: Analyze goal and create task
        logger.info("Phase 1: Goal analysis")
        context.current_state = "AUTONOMOUS_ANALYZING"
        context.payload = {
            "action": "analyze_goal",
            "goal": goal_text
        }
        
        result_context = await self.orchestrator.execute(context)
        analysis_result = result_context.payload.get("result", {})
        
        if not analysis_result.get("success"):
            error_msg = analysis_result.get("error", "Unknown error")
            message = analysis_result.get("message", error_msg)
            logger.error(f"Goal analysis failed: {message}")
            return f"Goal analysis failed: {message}"
        
        task_id = analysis_result.get("task_id")
        logger.info(f"Task created: {task_id}")
        
        # Phase 2: Execute mission (strategic planning)
        logger.info("Phase 2: Mission execution")
        context.current_state = "AUTONOMOUS_EXECUTING"
        context.payload = {
            "action": "execute_mission",
            "task_id": task_id
        }
        
        result_context = await self.orchestrator.execute(context)
        execution_result = result_context.payload.get("result", {})
        
        if not execution_result.get("success"):
            error_msg = execution_result.get("error", "Unknown error")
            logger.error(f"Mission execution failed: {error_msg}")
            return f"Mission execution failed: {error_msg}"
        
        # Phase 3: Update WORKLOG.md
        logger.info("Phase 3: WORKLOG update")
        await self._update_worklog_autonomous(
            task_id=task_id,
            goal=goal_text,
            analysis=analysis_result.get("analysis", {}),
            plan=execution_result.get("plan", {}),
            status="PLANNED"
        )
        
        # Phase 4: Format success message
        plan = execution_result.get("plan", {})
        message = execution_result.get("message", "")
        
        result_text = (
            f"✅ Autonomous Mission Initiated\n\n"
            f"Task ID: {task_id}\n"
            f"Status: {execution_result.get('status', 'unknown')}\n\n"
            f"Next Steps:\n"
        )
        
        for i, step in enumerate(plan.get("next_steps", []), 1):
            result_text += f"{i}. {step}\n"
        
        result_text += f"\n{message}"
        
        logger.info(f"Autonomous workflow completed for task {task_id}")
        return result_text
    
    async def _update_worklog_autonomous(
        self,
        task_id: str,
        goal: str,
        analysis: dict[str, Any],
        plan: dict[str, Any],
        status: str
    ) -> None:
        """
        Update WORKLOG.md with autonomous mission entry.
        
        Appends a new section to WORKLOG.md documenting the autonomous
        mission initiation, analysis, and strategic plan.
        
        Args:
            task_id: Task identifier
            goal: Original goal text
            analysis: Analysis result from NotesAnalyzer
            plan: Strategic plan from Orchestrator
            status: Current mission status
        """
        from pathlib import Path
        from datetime import datetime
        
        worklog_file = Path(self.worklog_path)
        
        try:
            # Read existing content
            if worklog_file.exists():
                content = worklog_file.read_text(encoding="utf-8")
            else:
                content = "# WORKLOG\n\n"
            
            # Format autonomous entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            entry = f"\n## [{timestamp}] AUTONOMOUS MISSION: {task_id}\n\n"
            entry += f"**Status:** {status}\n\n"
            entry += f"**Goal:**\n{goal}\n\n"
            
            if analysis:
                entry += "**Analysis:**\n"
                entry += f"- Type: {analysis.get('type', 'unknown')}\n"
                entry += f"- Scope: {analysis.get('scope', 'unknown')}\n"
                
                tags = analysis.get('tags', [])
                if tags:
                    entry += f"- Tags: {', '.join(tags)}\n"
                
                description = analysis.get('description', '')
                if description:
                    entry += f"- Description: {description}\n"
                
                entry += "\n"
            
            if plan:
                entry += "**Strategic Plan:**\n"
                
                next_steps = plan.get('next_steps', [])
                if next_steps:
                    entry += "\nNext Steps:\n"
                    for i, step in enumerate(next_steps, 1):
                        entry += f"{i}. {step}\n"
                
                phases = plan.get('estimated_phases', {})
                if phases:
                    entry += "\nEstimated Phases:\n"
                    for phase_name, phase_desc in phases.items():
                        entry += f"- **{phase_name}**: {phase_desc}\n"
                
                entry += "\n"
            
            entry += "---\n"
            
            # Append entry
            updated_content = content + entry
            worklog_file.write_text(updated_content, encoding="utf-8")
            
            logger.info(f"WORKLOG updated for autonomous mission {task_id}")
        
        except Exception as e:
            logger.error(f"Failed to update WORKLOG: {e}", exc_info=True)
            # Non-critical error, don't fail the mission
