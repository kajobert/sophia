import os
import uuid
import json
import re
from typing import Optional

from core.rich_printer import RichPrinter
from core.llm_manager import LLMManager
from core.orchestrator import WorkerOrchestrator


class ConversationalManager:
    """
    Acts as a stateless task dispatcher. It receives a task from the
    MissionManager, delegates it to the WorkerOrchestrator, and returns
    the result. It no longer manages plans or mission state.
    """
    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.status_widget = status_widget
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.worker = WorkerOrchestrator(project_root=self.project_root, status_widget=status_widget)
        self.session_id = str(uuid.uuid4()) # Unique ID for this conversational session

        RichPrinter.info("ConversationalManager initialized.")

    async def initialize(self):
        """Initializes the subordinate Worker."""
        await self.worker.initialize()
        RichPrinter.info("ConversationalManager and Worker are ready.")

    async def shutdown(self):
        """Safely shuts down the subordinate Worker."""
        await self.worker.shutdown()
        RichPrinter.info("ConversationalManager services have been safely shut down.")

    async def handle_task(self, task: str, mission_prompt: Optional[str] = None) -> dict:
        """
        Handles a single, specific task delegated by the MissionManager.
        This method is now the primary entry point, replacing handle_user_input.
        """
        RichPrinter.info(f"Manager received task: '{task}'")
        # The triage and budget logic could be simplified or moved,
        # but for now, we'll keep it to guide the worker.
        task_directives = await self._get_task_directives(task)
        budget = task_directives.get("budget", 8)

        # The context of the overall mission is passed to the worker
        result = await self.worker.run(
            initial_task=task,
            session_id=self.session_id,
            budget=budget,
            mission_prompt=mission_prompt
        )
        return result

    async def _get_task_directives(self, task: str) -> dict:
        """
        Analyzes a task using a specialized prompt to determine its type and a suggested budget.
        """
        RichPrinter.info("Getting directives for task (triage & budget)...")
        try:
            with open(os.path.join(self.project_root, "prompts/triage_and_budget_prompt.txt"), "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.error("Triage and budget prompt not found. Using default values.")
            return {"type": "complex", "budget": 8}

        prompt = prompt_template.format(task=task)
        # Use a fast model for this classification task
        model = self.llm_manager.get_llm(self.llm_manager.config.get("llm_models", {}).get("fast_model", "default"))

        response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})

        try:
            match = re.search(r"```(json)?\s*\n(.*?)\n```", response_text, re.DOTALL)
            json_str = match.group(2).strip() if match else response_text.strip()
            directives = json.loads(json_str)

            if "type" in directives and "budget" in directives:
                RichPrinter.log_communication("Task Directives", directives, style="bold blue")
                return directives
            else:
                RichPrinter.warning("Missing keys in directives. Using fallback.")
                return {"type": "complex", "budget": 8}
        except json.JSONDecodeError:
            RichPrinter.log_error_panel("Failed to parse JSON from triage prompt", response_text)
            return {"type": "complex", "budget": 8}

    async def generate_final_response(self, context: str, touched_files: list[str] | None = None) -> str:
        """
        Generates a user-friendly final response after a mission or task is complete.
        This is called by the MissionManager.
        """
        RichPrinter.info("Manager is formulating the final response for the user...")

        prompt_parts = [
            "Based on the following context, write a brief, friendly, and informative response to the user in Czech.",
            f"Context: {context}"
        ]

        if touched_files:
            files_str = "\n".join(f"- `{f}`" for f in touched_files)
            prompt_parts.append(
                "\nDuring the operation, the following files were modified or created. "
                "Explicitly mention them in the response as a list so the user knows what has changed:\n"
                f"{files_str}"
            )

        prompt = "\n\n".join(prompt_parts)
        model = self.llm_manager.get_llm("default")
        final_response, _ = await model.generate_content_async(prompt)
        return final_response

    # The complex project management loop and reflection logic have been moved to MissionManager.
    # _run_reflection is removed as MissionManager now handles it directly via ReflectionServer.