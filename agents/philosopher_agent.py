# /agents/philosopher_agent.py
"""
Agent Filosofa (PhilosopherAgent) pro Sophii.
Jeho úkolem je sebereflexe, analýza minulých událostí a generování vhledů.
"""

from crewai import Agent
from tools.memory_tools import MemoryReaderTool
from core.agent_config import load_agent_config

class PhilosopherAgent:
    """
    A wrapper class for the Philosopher agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("philosopher")
        memory_reader_tool = MemoryReaderTool()

        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            tools=[memory_reader_tool],
            verbose=True,
            allow_delegation=False,
            memory=False
        )

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
