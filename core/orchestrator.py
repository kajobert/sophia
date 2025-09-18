import asyncio
import uuid
import logging
import re
from core.context import SharedContext
from core.llm_config import get_llm
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent
from agents.aider_agent import AiderAgent
from memory.advanced_memory import AdvancedMemory

class AgentOrchestrator:
    """
    Orchestrates the workflow of agents.
    Can route prompts to either the full Planner->Engineer->Tester chain
    or to the AiderAgent for direct code modification.
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
            self.aider = AiderAgent()
            self.memory = AdvancedMemory()
            logging.info("AgentOrchestrator initialized successfully with all agents and memory.")
        except Exception as e:
            logging.error(f"Critical error during AgentOrchestrator initialization: {e}")
            raise

    async def route_prompt(self, prompt: str) -> SharedContext:
        """
        Routes the user prompt to the appropriate agent workflow.
        - If the prompt matches the code modification format, it routes to AiderAgent.
        - Otherwise, it routes to the full planning and execution chain.
        """
        session_id = str(uuid.uuid4())
        context = SharedContext(session_id=session_id, original_prompt=prompt)
        logging.info(f"Orchestration started for session: {session_id}")
        logging.info(f"Routing prompt: {prompt}")

        # Regex to detect code modification commands
        # Format: "modify file(s) `file1.py`, `file2.py`: <instructions>"
        match = re.match(r"modify file(?:s)?\s+((?:`[^`]+`\s*,\s*)*`[^`]+`)\s*:\s*(.*)", prompt, re.DOTALL)

        if match:
            file_paths_str = match.group(1)
            instructions = match.group(2)

            # Extract file paths from the captured string
            file_paths = [path.strip() for path in file_paths_str.replace('`', '').split(',')]

            logging.info(f"Routing to AiderAgent. Files: {file_paths}, Instructions: '{instructions}'")
            return await self.run_code_modification(context, file_paths, instructions)
        else:
            logging.info("Routing to standard orchestration flow.")
            return await self.run_orchestration(context)


    async def run_code_modification(self, context: SharedContext, files: list[str], instructions: str) -> SharedContext:
        """
        Runs the AiderAgent to perform a direct code modification.
        """
        logging.info("--- Running AiderAgent for Code Modification ---")
        try:
            # The AiderAgent might be synchronous, so we run it in a thread
            result = await asyncio.to_thread(self.aider.propose_change, description=instructions, files=files)
            context.payload['aider_result'] = result
            logging.info(f"AiderAgent finished successfully. Result: {result}")

            await self.memory.add_memory(
                content=f"Aider task completed for prompt: {context.original_prompt}",
                mem_type="AIDER_TASK_RESULT",
                metadata=context.payload
            )
            logging.info("Aider task result saved to memory.")

        except Exception as e:
            logging.error(f"An error occurred during AiderAgent execution: {e}", exc_info=True)
            context.payload['error'] = f"An AiderAgent error occurred: {e}"

        logging.info(f"Code modification finished for session: {context.session_id}.")
        return context


    async def run_orchestration(self, context: SharedContext) -> SharedContext:
        """
        Runs the full agent orchestration pipeline (Planner -> Engineer -> Tester).
        This is now called by route_prompt.
        """
        logging.info(f"Standard orchestration running for session: {context.session_id}")

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

            # Step 4: Save result to memory
            logging.info("--- Saving Orchestration Result to Memory ---")
            await self.memory.add_memory(
                content=f"Orchestration completed for prompt: {context.original_prompt}",
                mem_type="ORCHESTRATION_RESULT",
                metadata=context.payload
            )
            logging.info("Orchestration result saved to memory.")

        except Exception as e:
            logging.error(f"An error occurred during agent orchestration: {e}", exc_info=True)
            context.payload['error'] = f"An orchestration error occurred: {e}"

        logging.info(f"Orchestration finished for session: {context.session_id}.")
        return context
