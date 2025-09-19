import asyncio
import os
import importlib
import inspect
from crewai import Task
from core.context import SharedContext
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent
from agents.aider_agent import AiderAgent
from tools.base_tool import BaseTool

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Orchestrator:
    """
    Central orchestrator for running the agentic workflow (Planner -> Engineer -> Tester)
    with a retry loop.
    """

    MAX_RETRIES = 3

    def __init__(self):
        self.planner = PlannerAgent()
        self.engineer = EngineerAgent()
        self.tester = TesterAgent()
        self.aider = AiderAgent()
        self.tools = self._load_tools()

    def _load_tools(self) -> dict:
        """
        Dynamically loads all tools from the 'tools' directory that inherit from BaseTool.
        """
        tools = {}
        tools_dir = "tools"
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{tools_dir}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        if issubclass(cls, BaseTool) and cls is not BaseTool:
                            try:
                                tools[name] = cls()
                                logging.info(f"Successfully loaded tool: {name}")
                            except Exception as e:
                                logging.error(f"Failed to instantiate tool {name}: {e}")
                except Exception as e:
                    logging.error(f"Failed to load module {module_name}: {e}")
        return tools

    async def execute_task(self, context: SharedContext, task_description: str):
        logging.info(f"Orchestrator starting task: {task_description}")

        # Pass the loaded tools to the context
        context.available_tools = self.tools

        # 1. Plánování
        planning_task = Task(
            description=f"Analyze the following user request and create a detailed, step-by-step execution plan. The user's request is: '{task_description}'",
            agent=self.planner,
            expected_output="A list of actionable steps to be executed by other agents.",
        )
        logging.info("Spouštím PlannerAgenta pro vytvoření plánu...")
        try:
            plan = await asyncio.to_thread(planning_task.execute)
            context.plan = plan
            logging.info(f"Plánovač vytvořil plán:\n{plan}")
        except Exception as e:
            logging.error(f"CHYBA: Selhání při zpracování úkolu PlannerAgentem: {e}")
            context.feedback = f"Planner failed: {e}"
            return context

        # 2. Implementace a Testování s cyklem pro opravy
        for i in range(self.MAX_RETRIES):
            logging.info(
                f"Pokus o implementaci a testování č. {i + 1}/{self.MAX_RETRIES}"
            )

            # 2a. Implementace (Engineer nebo AiderAgent)
            try:
                if any(
                    word in task_description.lower()
                    for word in [
                        "refaktoruj",
                        "oprav",
                        "vylepši",
                        "refactor",
                        "fix",
                        "improve",
                    ]
                ):
                    logging.info(
                        "Detekován úkol pro AiderAgent (refaktorace/oprava/vylepšení)..."
                    )
                    # AiderAgent might not fit the standard task.execute() model, needs careful implementation
                    # For now, we assume a similar interface for simplicity in the orchestrator
                    # In a real scenario, this might need a different call pattern
                    context.code = await asyncio.to_thread(
                        self.aider.propose_change,
                        description=task_description,
                        context=context,
                    )
                    logging.info(f"AiderAgent výsledek: {context.code}")
                else:
                    logging.info("Spouštím EngineerAgenta pro implementaci...")
                    engineer_task = Task(
                        description=f"Based on the following plan, implement the code. Previous feedback (if any): {context.feedback}\n\nPlan:\n{context.plan}",
                        agent=self.engineer,
                        expected_output="Implemented code in sandbox.",
                    )
                    context.code = await asyncio.to_thread(engineer_task.execute)
                    logging.info(f"EngineerAgent výsledek: {context.code}")
            except Exception as e:
                logging.error(f"CHYBA: Implementační agent selhal: {e}")
                context.feedback = f"Implementation agent failed: {e}"
                # This is a critical failure, no point in retrying if the agent itself crashes
                break

            # 2b. Testování
            logging.info("Spouštím TesterAgenta...")
            try:
                tester_task = Task(
                    description=f"Otestuj nově implementovaný/refaktorovaný kód v sandboxu pomocí unit testů. Kód k otestování:\n\n{context.code}",
                    agent=self.tester,
                    expected_output="Výsledek testů (PASS nebo FAIL s detaily).",
                )
                test_result = await asyncio.to_thread(tester_task.execute)
                context.test_results = str(test_result)
                logging.info(f"TesterAgent výsledek: {context.test_results}")

                if "pass" in context.test_results.lower():
                    logging.info("Testy úspěšné, úkol dokončen.")
                    context.feedback = "Task successfully completed."
                    return context
                else:
                    logging.warning("Testy selhaly, připravuji další pokus.")
                    context.feedback = f"Tests failed. Please fix the code. Test results:\n{context.test_results}"

            except Exception as e:
                logging.error(f"CHYBA: TesterAgent selhal: {e}")
                context.feedback = f"Tester agent failed: {e}"
                # If the tester itself crashes, we should probably stop.
                break

        logging.error(f"Úkol selhal po {self.MAX_RETRIES} pokusech.")
        return context
