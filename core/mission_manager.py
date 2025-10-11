import os
import yaml
import asyncio
import uuid
from typing import Optional, List, Dict, Any

from core.conversational_manager import ConversationalManager
from core.rich_printer import RichPrinter
from tui.messages import ChatMessage
from mcp_servers.worker.planning_server import PlanningServer
from mcp_servers.worker.reflection_server import ReflectionServer


class MissionManager:
    """
    Acts as the single source of truth for the mission state. It holds the main
    prompt, creates a plan, and dispatches sub-tasks to the ConversationalManager.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        # Managers and Servers
        self.conversational_manager = ConversationalManager(project_root=self.project_root)
        self.planning_server = PlanningServer(project_root=self.project_root)
        self.reflection_server = ReflectionServer(project_root=self.project_root)

        # Mission State
        self.mission_prompt: Optional[str] = None
        self.is_mission_active: bool = False
        self.sub_tasks: List[Dict[str, Any]] = []
        self.current_task_index: int = -1
        self.total_touched_files: set = set()
        self.project_history: list = []

        # Configuration
        self.completed_missions_count: int = 0
        self.default_jules_source: Optional[str] = None
        self._load_config()

    def _load_config(self):
        """Loads configuration and sets the default source for Jules."""
        try:
            config_path = os.path.join(self.project_root, "config/config.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            self.default_jules_source = config.get("jules_api", {}).get("default_source")
        except (FileNotFoundError, yaml.YAMLError):
            self.default_jules_source = None
            RichPrinter.warning("Could not load default source for Jules from config.yaml.")

    async def initialize(self):
        """Initializes the subordinate conversational manager and servers."""
        RichPrinter.info("MissionManager is initializing...")
        await self.conversational_manager.initialize()
        # Servers are managed by MCPClient, no separate init needed for them here
        RichPrinter.info("MissionManager is ready.")

    async def shutdown(self):
        """Safely shuts down the subordinate conversational manager."""
        await self.conversational_manager.shutdown()
        RichPrinter.info("MissionManager has been safely shut down.")

    def get_mission_status(self) -> dict:
        """Returns the current status of the mission."""
        return {
            "is_active": self.is_mission_active,
            "mission_prompt": self.mission_prompt,
            "sub_task_count": len(self.sub_tasks),
            "current_task_index": self.current_task_index,
            "completed_missions": self.completed_missions_count,
        }

    async def start_mission(self, prompt: str):
        """
        Initiates a new mission, creates a plan, and starts the execution loop.
        """
        RichPrinter.info(f"New mission received: '{prompt}'")
        self._reset_mission_state(prompt)

        # 1. Create the plan
        plan_created = await self._create_initial_plan()
        if not plan_created:
            RichPrinter._post(ChatMessage("I couldn't create a plan for this mission. Please try again or rephrase your request.", owner='agent', msg_type='error'))
            self.is_mission_active = False
            return

        # 2. Run the mission loop
        await self._run_mission_loop()

    def _reset_mission_state(self, prompt: str):
        """Resets all state variables for a new mission."""
        self.mission_prompt = prompt
        self.is_mission_active = True
        self.sub_tasks = []
        self.current_task_index = -1
        self.total_touched_files = set()
        self.project_history = [f"MISSION GOAL: {prompt}"]
        self.planning_server.reset_plan() # Clear any previous plan


    async def _create_initial_plan(self) -> bool:
        """
        Uses the planning server to create a hierarchical plan for the mission.
        """
        RichPrinter._post(ChatMessage("This task is complex. Creating a project plan...", owner='agent', msg_type='inform'))
        self.planning_server.update_task_description(self.mission_prompt)
        # The first sub-task is to create the actual plan
        self.planning_server.add_subtask(description=f"Based on the goal '{self.mission_prompt}', create a detailed, step-by-step plan.", priority=1)

        # The first task is always the planning task.
        planning_task = self.planning_server.get_next_executable_task()
        if not planning_task:
            RichPrinter.error("Could not get the initial planning task.")
            return False

        RichPrinter._post(ChatMessage("Delegating planning task to the specialist...", owner='agent', msg_type='info'))
        # Delegate the creation of the plan to the worker
        worker_result = await self.conversational_manager.handle_task(planning_task['description'])

        if worker_result.get("status") != "completed":
            RichPrinter.error(f"The planning sub-task failed: {worker_result.get('summary')}")
            return False

        # The result of the planning task should be the plan itself, which we now load.
        # We assume the worker used the planning_server tools to populate the plan.
        self.planning_server.mark_task_as_completed(planning_task['id'])
        self.sub_tasks = self.planning_server.get_all_tasks()

        # Filter out the main goal and the initial planning task
        self.sub_tasks = [task for task in self.sub_tasks if task['id'] > 1 and not task['completed']]

        if not self.sub_tasks:
             RichPrinter.warning("The initial planning did not produce any sub-tasks.")
             # This might not be an error; the task might be simple enough to be done in one step.
             # We can treat the original prompt as the only task.
             self.planning_server.add_subtask(description=self.mission_prompt, priority=1)
             self.sub_tasks = [task for task in self.planning_server.get_all_tasks() if task['id'] > 1 and not task['completed']]

        RichPrinter._post(ChatMessage(f"Plan created successfully. The mission consists of {len(self.sub_tasks)} steps.", owner='agent', msg_type='success'))
        return True


    async def _run_mission_loop(self):
        """
        The main loop that iterates through sub-tasks and dispatches them.
        """
        for i, task in enumerate(self.sub_tasks):
            self.current_task_index = i
            task_id = task['id']
            task_desc = task['description']

            self.project_history.append(f"EXECUTING SUB-TASK: {task_desc}")
            RichPrinter._post(ChatMessage(f"Working on step {i+1}/{len(self.sub_tasks)}: {task_desc}", owner='agent', msg_type='inform'))

            # Delegate the actual work to the simplified ConversationalManager
            worker_result = await self.conversational_manager.handle_task(task_desc, self.mission_prompt)

            self.project_history.append(f"WORKER RESULT: {worker_result.get('summary', 'No summary.')}")

            if worker_result.get("status") == "completed":
                RichPrinter.info(f"Sub-task '{task_desc}' completed successfully.")
                self.planning_server.mark_task_as_completed(task_id)
                touched_files = worker_result.get("touched_files", [])
                if touched_files:
                    self.total_touched_files.update(touched_files)
                    RichPrinter._post(ChatMessage(f"Files affected by this step: {', '.join(touched_files)}", owner='agent', msg_type='info'))
            else:
                # Failure case
                await self._handle_task_failure(task_desc, worker_result)
                return # Stop the mission on failure

            await asyncio.sleep(1) # Small delay for UX

        # Mission Completion
        self.is_mission_active = False
        self.completed_missions_count += 1
        final_summary = (
            "All mission steps have been successfully completed. "
            f"The overall goal '{self.mission_prompt}' has been achieved."
        )
        final_response = await self.conversational_manager.generate_final_response(final_summary, list(self.total_touched_files))
        RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='success'))

        # Run final reflection on the whole project
        await self._run_final_reflection()

    async def _handle_task_failure(self, task_desc: str, worker_result: dict):
        """Handles a failed sub-task, performs reflection, and reports to the user."""
        error_summary = worker_result.get('summary', 'Unknown error.')
        RichPrinter.error(f"Error executing sub-task '{task_desc}': {error_summary}")
        self.project_history.append(f"ERROR: {error_summary}")

        RichPrinter._post(ChatMessage("I've encountered a problem. Performing self-reflection to find a solution...", owner='agent', msg_type='inform'))

        worker_history = worker_result.get("history", [])
        reflection = await self.reflection_server.reflect_on_recent_steps(worker_history, self.mission_prompt)

        RichPrinter._post(ChatMessage(f"**Self-Reflection Result:**\n{reflection}", owner='agent', msg_type='warning'))
        self.project_history.append(f"REFLECTION: {reflection}")

        # Stop the mission and report to the user.
        final_response = await self.conversational_manager.generate_final_response(
            f"While working on the task '{task_desc}', an error occurred: {error_summary}. "
            f"After analysis, I came to this conclusion: {reflection}. "
            "The mission has been halted. Please provide further instructions on how to proceed.",
            list(self.total_touched_files)
        )
        RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='error'))
        self.is_mission_active = False


    async def _run_final_reflection(self):
        """
        Triggers a self-reflection process based on the entire project history
        to generate a "learning" and save it to long-term memory.
        """
        RichPrinter.info("Running post-mission reflection...")
        # We now pass the mission prompt directly to the reflection server
        learning = await self.reflection_server.reflect_on_project(
            history="\n".join(self.project_history),
            mission_goal=self.mission_prompt
        )

        if not learning or len(learning) < 10:
            RichPrinter.warning("The generated learning is too short, ignoring.")
            return

        # The worker's LTM is used to store the learning
        self.conversational_manager.worker.ltm.add(
            documents=[learning],
            metadatas=[{"type": "learning", "source": "mission_reflection"}],
            ids=[str(uuid.uuid4())]
        )
        RichPrinter.log_communication("New learning from mission stored in LTM", learning, style="bold green")

    def get_completed_missions_count(self) -> int:
        """Returns the number of successfully completed missions."""
        return self.completed_missions_count

    async def continue_mission(self, user_input: str):
        """
        Handles follow-up user input. For now, it just starts a new mission.
        In the future, this could be used for interactive error recovery.
        """
        RichPrinter.warning("Interactive continuation is not fully implemented. Starting a new mission with the provided input.")
        await self.start_mission(user_input)