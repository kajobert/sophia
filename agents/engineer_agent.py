from crewai import Agent
import core.llm_config
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool
from tools.code_executor import ExecutePythonScriptTool

class EngineerAgent:
    """
    A wrapper class for the Engineer agent.
    This prevents the agent from being instantiated at module import time,
    which helps with testing and prevents import-time side effects.
    """
    def __init__(self):
        # Vytvoření instancí nástrojů
        write_file_tool = WriteFileTool()
        read_file_tool = ReadFileTool()
        list_dir_tool = ListDirectoryTool()
        execute_script_tool = ExecutePythonScriptTool()

        self.agent = Agent(
            role="Engineer",
            goal="Implementovat, upravovat a refaktorovat kód v sandboxu dle zadání. Umí bezpečně číst, zapisovat a spouštět kód.",
            backstory=(
                "Jsem Engineer, tvůrce a realizátor. Převádím plány do funkčního kódu, testuji a refaktoruji. Pracuji pouze v sandboxu, kde je vše bezpečné."
            ),
            llm=core.llm_config.llm,
            tools=[write_file_tool, read_file_tool, list_dir_tool, execute_script_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
