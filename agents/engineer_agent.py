from crewai import Agent, Task, Crew
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool, FileSystemError
from tools.code_executor import ExecutePythonScriptTool
from core.context import SharedContext
from core.llm_config import llm

class EngineerAgent:
    """
    A wrapper class for the Engineer agent.
    """
    def __init__(self, llm):
        write_file_tool = WriteFileTool()
        read_file_tool = ReadFileTool()
        list_dir_tool = ListDirectoryTool()
        execute_script_tool = ExecutePythonScriptTool()

        self.agent = Agent(
            role="Engineer",
            goal="Implementovat, upravovat a refaktorovat kód v sandboxu dle zadání. Umí bezpečně číst, zapisovat a spouštět kód.",
            backstory=(
                "Jsem Engineer, tvůrce a realizátor. Převádím plány do funkčního kódu, testuji a refaktoruji. "
                "Pracuji pouze v sandboxu, kde je vše bezpečné."
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
        """
        plan = context.payload.get('plan')
        if not plan:
            raise ValueError("The 'plan' is missing from the context payload.")

        task_description = f"Implement the following plan:\n\n{plan}"

        coding_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output="The final, complete code that implements the plan. No extra chatter."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[coding_task],
            verbose=False
        )

        try:
            result = crew.kickoff()
            if hasattr(result, 'raw'):
                generated_code = result.raw
            else:
                generated_code = str(result)
        except FileSystemError as e:
            print(f"EngineerAgent encountered a critical file system error: {e}")
            raise

        context.payload['code'] = generated_code
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
