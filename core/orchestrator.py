import asyncio
from typing import Optional

from core.state_manager import StateManager, State
from core.rich_printer import RichPrinter
from core.mcp_client import MCPClient

class NomadOrchestrator:
    """
    The central orchestrator for the Nomad agent.

    This class implements the "Single Brain - State Machine" architecture.
    It manages the agent's entire lifecycle, from receiving user input
    to planning, executing tasks, and responding.
    """

    def __init__(self, project_root: str, session_id: Optional[str] = None):
        """
        Initializes the NomadOrchestrator.

        Args:
            project_root: The root directory of the project.
            session_id: An optional ID to restore a previous session.
        """
        self.project_root = project_root
        self.state_manager = StateManager(project_root, session_id)
        self.mcp_client = MCPClient(project_root=self.project_root, profile="worker")

        # Attempt to restore a previous session
        if session_id and self.state_manager.restore():
            RichPrinter.info(f"Restored session {session_id}. Current state: {self.state_manager.current_state.value}")
        else:
            RichPrinter.info("Starting a new session.")

    async def run(self, initial_prompt: Optional[str] = None):
        """
        The main execution loop for the orchestrator.

        This method drives the state machine based on the current state.
        """
        RichPrinter.info(f"Orchestrator starting in state: {self.state_manager.current_state.value}")

        if initial_prompt:
            # For now, just log the prompt.
            # In the future, this will trigger the PLANNING state.
            RichPrinter.info(f"Received initial prompt: {initial_prompt}")
            self.state_manager.transition_to(State.PLANNING, reason="Initial prompt received.")

        # This will become the main state machine loop.
        # For now, it's just a placeholder.
        await asyncio.sleep(1)

        RichPrinter.info("Orchestrator run finished (placeholder).")

    async def shutdown(self):
        """Gracefully shuts down the orchestrator and its components."""
        RichPrinter.info("Shutting down orchestrator...")
        await self.mcp_client.shutdown()
        self.state_manager.persist()
        RichPrinter.info("Orchestrator shutdown complete.")