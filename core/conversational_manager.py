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
        This method now acts as a simple dispatcher, passing the task directly
        to the WorkerOrchestrator.
        """
        RichPrinter.info(f"Manager received task: '{task}'")

        # Directly delegate the task to the worker. The worker is now responsible
        # for its own budget and execution flow.
        result = await self.worker.run(
            initial_task=task,
            session_id=self.session_id,
            mission_prompt=mission_prompt
        )
        return result

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