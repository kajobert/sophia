from crewai import Agent, Task, Crew
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool, FileSystemError
from tools.code_executor import ExecutePythonScriptTool
from core.context import SharedContext
from core.agent_config import load_agent_config

class EngineerAgent:
    """
    A wrapper class for the Engineer agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("engineer")
        write_file_tool = WriteFileTool()
        read_file_tool = ReadFileTool()
        list_dir_tool = ListDirectoryTool()
        execute_script_tool = ExecutePythonScriptTool()

        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            tools=[write_file_tool, read_file_tool, list_dir_tool, execute_script_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )
        self.task_description_template = agent_config['task_description']
        self.expected_output_template = agent_config['expected_output']

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object with a 'plan' and executes the engineering task.
        If a FileSystemError occurs, it is caught and re-raised to halt execution.
        """
        plan = context.payload.get('plan')
        if not plan:
            raise ValueError("The 'plan' is missing from the context payload.")

        task_description = self.task_description_template.format(plan=plan)

        coding_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template
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

            context.payload['code'] = generated_code
            return context
        except FileSystemError as e:
            # Re-raise the exception to be handled by the higher-level orchestrator.
            # This is critical because a failure in the engineer's task (e.g., can't write a file)
            # should stop the entire chain.
            print(f"EngineerAgent failed with a file system error: {e}")
            raise e

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
