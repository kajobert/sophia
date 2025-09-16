from crewai import Agent, Task, Crew
from core.llm_config import llm
from tools.file_system import ReadFileTool, ListDirectoryTool
from tools.code_executor import RunUnitTestsTool
from core.context import SharedContext

class TesterAgent:
    """
    A wrapper class for the Tester agent.
    """
    def __init__(self):
        # Vytvoření instancí nástrojů
        read_file_tool = ReadFileTool()
        list_dir_tool = ListDirectoryTool()
        run_tests_tool = RunUnitTestsTool()

        self.agent = Agent(
            role="Tester",
            goal="Testovat a validovat kód v sandboxu pomocí unit testů. Umí číst soubory a spouštět testy.",
            backstory=(
                "Jsem Tester, strážce kvality. Spouštím unit testy, analyzuji výsledky a reportuji chyby. Pracuji pouze v sandboxu."
            ),
            llm=llm,
            tools=[read_file_tool, list_dir_tool, run_tests_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object with 'code' and executes the testing task.
        The test results are added back to the context.

        Args:
            context (SharedContext): The shared context containing the code to test.

        Returns:
            SharedContext: The updated context with the test results.
        """
        code_to_test = context.payload.get('code')
        if not code_to_test:
            raise ValueError("The 'code' is missing from the context payload.")

        # Vytvoření a spuštění CrewAI úlohy
        testing_task = Task(
            description=f"Otestuj následující kód a zhodnoť, zda je funkční:\n---\n{code_to_test}",
            agent=self.agent,
            expected_output="Stručné a jasné zhodnocení výsledků testů. V případě chyby popiš, co selhalo."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[testing_task],
            verbose=False
        )

        result = crew.kickoff()

        # Uložení výsledku do kontextu
        test_results = result.raw if hasattr(result, 'raw') else str(result)
        context.payload['test_results'] = test_results
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
