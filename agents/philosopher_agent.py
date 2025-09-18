from crewai import Agent, Task, Crew
from tools.memory_tools import MemoryReaderTool
from core.context import SharedContext
from core.llm_config import llm

class PhilosopherAgent:
    """
    A wrapper class for the Philosopher agent.
    """
    def __init__(self, llm):
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
            memory=False
        )

    def reflect(self, context: SharedContext) -> SharedContext:
        """
        Runs the philosopher task to reflect on recent events.
        """
        task = Task(
            description="Read the most recent memories and provide a brief, insightful summary of the last operational cycle. Focus on key decisions, outcomes, and potential areas for improvement or learning.",
            agent=self.agent,
            expected_output="A concise, reflective summary of the last cycle's events, highlighting key learnings or questions for future consideration."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()

        if hasattr(result, 'raw'):
            reflection = result.raw
        else:
            reflection = str(result)

        context.payload['reflection'] = reflection
        print(f"PHILOSOPHER'S REFLECTION:\n{reflection}")
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
