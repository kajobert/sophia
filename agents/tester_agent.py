from crewai import Agent
from core.llm_config import llm
from tools.file_system import ReadFileTool, ListDirectoryTool
from tools.code_executor import RunUnitTestsTool

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

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
