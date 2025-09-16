from crewai import Agent, Task, Crew
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool
from tools.code_executor import ExecutePythonScriptTool
from core.context import SharedContext

class EngineerAgent:
    """
    A wrapper class for the Engineer agent.
    This prevents the agent from being instantiated at module import time,
    which helps with testing and prevents import-time side effects.
    """
    def __init__(self, llm):
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
            llm=llm,
            tools=[write_file_tool, read_file_tool, list_dir_tool, execute_script_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object with a 'plan' and executes the engineering task.
        The resulting code is added back to the context.

        Args:
            context (SharedContext): The shared context containing the plan.

        Returns:
            SharedContext: The updated context with the generated code.
        """
        plan = context.payload.get('plan')
        if not plan:
            raise ValueError("The 'plan' is missing from the context payload.")

        # Vytvoření a spuštění CrewAI úlohy
        coding_task = Task(
            description=f"Na základě tohoto plánu vytvoř kód v Pythonu:\n---\n{plan}",
            agent=self.agent,
            expected_output="Funkční a okomentovaný kód v Pythonu, připravený k přímému spuštění."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[coding_task],
            verbose=False  # Keep it clean for this level
        )

        result = crew.kickoff()

        # Uložení výsledku do kontextu
        # Předpokládáme, že 'result' je objekt, kde 'raw' obsahuje čistý kód
        if hasattr(result, 'raw'):
            generated_code = result.raw
        else:
            generated_code = str(result)

        context.payload['code'] = generated_code
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
