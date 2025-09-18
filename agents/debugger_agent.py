from crewai import Agent, Task, Crew
from core.agent_config import load_agent_config
from core.llm_config import get_llm
import json

class DebuggerAgent:
    """
    A wrapper class for the Debugger agent.
    """
    def __init__(self, llm=None):
        if llm is None:
            llm = get_llm()

        agent_config = load_agent_config("debugger")
        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        self.task_description_template = agent_config['task_description']
        self.expected_output_template = agent_config['expected_output']

    def run_task(self, failure_details: dict) -> str:
        """
        Runs the debugging task using the provided failure details.

        Args:
            failure_details: A dictionary with details about the failed test.

        Returns:
            A string containing the agent's analysis and suggestion.
        """
        # Převedeme slovník na hezky formátovaný JSON string pro lepší čitelnost v promptu
        failure_details_str = json.dumps(failure_details, indent=2)

        task_description = self.task_description_template.format(
            failure_details=failure_details_str
        )

        debugging_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[debugging_task],
            verbose=True
        )

        result = crew.kickoff()

        return result.raw if hasattr(result, 'raw') else str(result)
