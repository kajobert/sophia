import asyncio
import uuid
import logging
from core.context import SharedContext
from core.llm_config import get_llm
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent

class AgentOrchestrator:
    """
    Orchestrates the workflow of agents (Planner, Engineer, Tester).
    This class is the single source of truth for the agent chain logic.
    """
    def __init__(self):
        """
        Initializes the orchestrator and all required agents.
        """
        try:
            self.llm = get_llm()
            self.planner = PlannerAgent(self.llm)
            self.engineer = EngineerAgent(self.llm)
            self.tester = TesterAgent(self.llm)
            logging.info("AgentOrchestrator initialized successfully with all agents.")
        except Exception as e:
            logging.error(f"Critical error during AgentOrchestrator initialization: {e}")
            raise

    async def run_orchestration(self, prompt: str) -> SharedContext:
        """
        Runs the full agent orchestration pipeline.

        Args:
            prompt (str): The initial user prompt or task.

        Returns:
            SharedContext: The final context after all agents have run.
        """
        session_id = str(uuid.uuid4())
        context = SharedContext(session_id=session_id, original_prompt=prompt)
        logging.info(f"Orchestration started for session: {session_id}")
        logging.info(f"Original task: {prompt}")

        try:
            # Step 1: Planner
            logging.info("--- Running Planner ---")
            context = await asyncio.to_thread(self.planner.run_task, context)
            if not context.payload.get('plan'):
                logging.error("Planner failed to return a plan. Halting orchestration.")
                context.payload['error'] = "Planner failed to return a plan."
                return context
            logging.info("Planner finished successfully.")

            # Step 2: Engineer
            logging.info("--- Running Engineer ---")
            context = await asyncio.to_thread(self.engineer.run_task, context)
            if not context.payload.get('code'):
                logging.error("Engineer failed to return code. Halting orchestration.")
                context.payload['error'] = "Engineer failed to return code."
                return context
            logging.info("Engineer finished successfully.")

            # Step 3: Tester
            logging.info("--- Running Tester ---")
            context = await asyncio.to_thread(self.tester.run_task, context)
            logging.info("Tester finished successfully.")

        except Exception as e:
            logging.error(f"An error occurred during agent orchestration: {e}", exc_info=True)
            context.payload['error'] = f"An orchestration error occurred: {e}"

        logging.info(f"Orchestration finished for session: {session_id}.")
        return context
