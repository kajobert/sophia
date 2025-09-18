from crewai import Agent
from tools.memory_tools import read_memory
from core.agent_config import load_agent_config

class PhilosopherAgent:
    """
    A wrapper class for the Philosopher agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("philosopher")

        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            tools=[read_memory],
            verbose=True,
            allow_delegation=False,
            memory=False
        )

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
