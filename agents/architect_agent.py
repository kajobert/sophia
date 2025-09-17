from crewai import Agent, Task, Crew
from core.context import SharedContext
from core.agent_config import load_agent_config

class ArchitectAgent:
    """
    A wrapper class for the Architect agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("architect")
        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )
        self.task_description_template = agent_config['task_description']
        self.expected_output_template = agent_config['expected_output']

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object and runs the architect task.
        """
        system_description = context.payload.get('system_description')
        if not system_description:
            raise ValueError("The 'system_description' is missing from the context payload.")

        task_description = self.task_description_template.format(system_description=system_description)

        architect_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[architect_task],
            verbose=False
        )

        result = crew.kickoff()

        if hasattr(result, 'raw'):
            architecture = result.raw
        else:
            architecture = str(result)

        context.payload['architecture'] = architecture
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
