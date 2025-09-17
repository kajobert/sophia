from crewai import Agent, Task, Crew
from tools.file_system import ReadFileTool, ListDirectoryTool, FileSystemError
from tools.code_executor import RunUnitTestsTool
from core.context import SharedContext
from core.agent_config import load_agent_config

class TesterAgent:
    """
    A wrapper class for the Tester agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("tester")
        read_file_tool = ReadFileTool()
        list_dir_tool = ListDirectoryTool()
        run_tests_tool = RunUnitTestsTool()

        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            tools=[read_file_tool, list_dir_tool, run_tests_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )
        self.task_description_template = agent_config['task_description']
        self.expected_output_template = agent_config['expected_output']

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object with 'code' and executes the testing task.
        """
        code_to_test = context.payload.get('code')
        if not code_to_test:
            raise ValueError("The 'code' is missing from the context payload.")

        task_description = self.task_description_template.format(code=code_to_test)

        testing_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[testing_task],
            verbose=False
        )

        try:
            result = crew.kickoff()
            test_results = result.raw if hasattr(result, 'raw') else str(result)
            context.payload['test_results'] = test_results
        except FileSystemError as e:
            context.payload['test_results'] = f"Test failed: {e}"

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
