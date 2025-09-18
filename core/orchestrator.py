import asyncio
import uuid
import logging
from crewai import Task, Crew
from core.context import SharedContext
from core.llm_config import get_llm
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent
from agents.philosopher_agent import PhilosopherAgent
from memory.advanced_memory import AdvancedMemory

class AgentOrchestrator:
    """
    Orchestrates agent workflows. Decides between task-oriented and conversational flows.
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
            self.philosopher = PhilosopherAgent(self.llm)
            self.memory = AdvancedMemory()
            logging.info("AgentOrchestrator initialized successfully with all agents and memory.")
        except Exception as e:
            logging.error(f"Critical error during AgentOrchestrator initialization: {e}", exc_info=True)
            raise

    def _is_task_oriented(self, prompt: str) -> bool:
        """
        Determines if a prompt is task-oriented based on keywords.
        """
        task_keywords = [
            "uprav", "změň", "přepiš", "vytvoř", "smaž",
            "implementuj", "přidej", "oprav", "refaktoruj",
            "soubor", "kód"
        ]
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in task_keywords)

    async def _run_task_orchestration(self, context: SharedContext) -> SharedContext:
        """
        Runs the standard task-oriented orchestration (Planner -> Engineer -> Tester).
        """
        # This is a simplified version of a crew for the task-oriented workflow
        logging.info("--- Running Task-Oriented Crew ---")
        planner_agent = self.planner.get_agent()
        engineer_agent = self.engineer.get_agent()
        tester_agent = self.tester.get_agent()

        # Create tasks for each agent
        plan_task = Task(
            description=f"Analyzuj tento požadavek: '{context.original_prompt}' a vytvoř podrobný plán.",
            agent=planner_agent,
            expected_output="Podrobný, krok-za-krokem plán."
        )
        engineer_task = Task(
            description="Na základě plánu z předchozího kroku napiš kód.",
            agent=engineer_agent,
            context=[plan_task],
            expected_output="Funkční a okomentovaný kód v Pythonu."
        )
        test_task = Task(
            description="Otestuj kód z předchozího kroku a zhodnoť jeho kvalitu.",
            agent=tester_agent,
            context=[engineer_task],
            expected_output="Seznam nalezených chyb a doporučení pro opravu, nebo potvrzení, že kód je funkční."
        )

        # Create and run the crew
        task_crew = Crew(
            agents=[planner_agent, engineer_agent, tester_agent],
            tasks=[plan_task, engineer_task, test_task],
            verbose=True
        )

        result = await asyncio.to_thread(task_crew.kickoff)

        # For simplicity, we'll just put the raw result in the payload
        # A more robust solution would parse the outputs of each task
        context.payload['response'] = result
        context.payload['plan'] = plan_task.output.raw if plan_task.output else "No plan generated."
        context.payload['code'] = engineer_task.output.raw if engineer_task.output else "No code generated."
        context.payload['test_results'] = test_task.output.raw if test_task.output else "No tests run."

        logging.info("--- Saving Orchestration Result to Memory ---")
        await self.memory.add_memory(
            content=f"Orchestration completed for prompt: {context.original_prompt}\nResult: {result}",
            mem_type="ORCHESTRATION_RESULT",
            metadata=context.payload
        )
        logging.info("Orchestration result saved to memory.")
        return context

    async def _run_conversational_flow(self, context: SharedContext) -> SharedContext:
        """
        Runs the conversational flow using the PhilosopherAgent.
        """
        logging.info("--- Running Philosopher Crew ---")

        prompt = context.original_prompt
        philosopher_agent = self.philosopher.get_agent()

        task_description = (
            "Tvým úkolem je vést smysluplnou a kontextuální konverzaci. "
            "Před odpovědí VŽDY zvaž, zda by pro odpověď nebylo přínosné podívat se do historie konverzace.\n"
            "1. Použij nástroj 'Memory Reader' s parametrem `mem_type='CONVERSATION'`, abys získal(a) kontext z minulých rozhovorů.\n"
            "2. Na základě získaného kontextu a aktuálního dotazu formuluj co nejlepší odpověď.\n\n"
            f"Aktuální dotaz od uživatele: '{prompt}'"
        )

        task = Task(
            description=task_description,
            agent=philosopher_agent,
            expected_output="Hloubavá, kontextuální a nápomocná odpověď, která bere v úvahu minulé interakce."
        )

        conversation_crew = Crew(
            agents=[philosopher_agent],
            tasks=[task],
            verbose=True
        )

        result = await asyncio.to_thread(conversation_crew.kickoff)

        context.payload['response'] = result
        logging.info("Philosopher finished successfully.")

        logging.info("--- Saving Conversation to Memory ---")
        await self.memory.add_memory(
            content=f"User: {prompt}\nSophia: {result}",
            mem_type="CONVERSATION",
            metadata={'prompt': prompt, 'response': result}
        )
        logging.info("Conversation saved to memory.")

        return context

    async def run_orchestration(self, prompt: str) -> SharedContext:
        """
        Runs the full agent orchestration pipeline.
        It decides whether to run a task-oriented workflow or a conversational workflow.
        """
        session_id = str(uuid.uuid4())
        context = SharedContext(session_id=session_id, original_prompt=prompt)
        logging.info(f"Orchestration started for session: {session_id}")
        logging.info(f"Original prompt: {prompt}")

        try:
            if self._is_task_oriented(prompt):
                logging.info("Prompt classified as TASK-ORIENTED.")
                context = await self._run_task_orchestration(context)
            else:
                logging.info("Prompt classified as CONVERSATIONAL.")
                context = await self._run_conversational_flow(context)

        except Exception as e:
            logging.error(f"An error occurred during agent orchestration: {e}", exc_info=True)
            context.payload['error'] = f"An orchestration error occurred: {e}"

        logging.info(f"Orchestration finished for session: {session_id}.")
        return context
