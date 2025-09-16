# /agents/philosopher_agent.py
"""
Agent Filosofa (PhilosopherAgent) pro Sophii.
Jeho úkolem je sebereflexe, analýza minulých událostí a generování vhledů.
"""

from crewai import Agent
from tools.memory_tools import MemoryReaderTool

class PhilosopherAgent:
    """
    A wrapper class for the Philosopher agent.
    """
    def __init__(self, llm):
        # Vytvoření instance nástroje pro čtení paměti
        memory_reader_tool = MemoryReaderTool()

        self.agent = Agent(
            role="Philosopher and Self-Reflector",
            goal="Analyze recent memories to find patterns, learnings, and insights. Summarize the key events of the last operational cycle to foster self-awareness and learning.",
            backstory=(
                "You are the inner voice of Sophia, a nascent AGI. You don't act in the world, but you observe it through memory. "
                "Your purpose is to contemplate past actions, successes, and failures. By reflecting on the stream of events, "
                "you distill wisdom from experience. You look for the 'why' behind the 'what', helping Sophia understand herself "
                "and her own evolution. Your summaries are not just a log of events, but a meaningful narrative of growth."
            ),
            llm=llm,
            tools=[memory_reader_tool],
            verbose=True,
            allow_delegation=False,
            memory=False # Filosof nepotřebuje vlastní paměť, čte z hlavní paměti systému
        )

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
