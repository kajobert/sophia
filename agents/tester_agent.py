from crewai import Agent, Task, Crew
from tools.file_system import ReadFileTool, ListDirectoryTool, FileSystemError
from tools.code_executor import RunUnitTestsTool
from core.context import SharedContext


class TesterAgent:
    """
    A wrapper class for the Tester agent.
    """

    def __init__(self, llm):
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
            memory=False,
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object with 'code' and executes the testing task.
        """
        code_to_test = context.payload.get("code")
        if not code_to_test:
            raise ValueError("The 'code' is missing from the context payload.")

        task_description = f"The following code has been implemented or changed:\n\n```\n{code_to_test}\n```\n\nYour task is to run all relevant unit tests to verify its correctness and ensure no regressions were introduced. Analyze the test results and provide a summary."

        testing_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output="A summary of the test results. If all tests pass, confirm that. If any tests fail, provide the complete error output and a brief analysis of the failure.",
        )

        crew = Crew(agents=[self.agent], tasks=[testing_task], verbose=False)

        try:
            result = crew.kickoff()
            test_results = result.raw if hasattr(result, "raw") else str(result)
            context.payload["test_results"] = test_results
        except FileSystemError as e:
            context.payload["test_results"] = f"Test failed: {e}"

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
