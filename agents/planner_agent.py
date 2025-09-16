from crewai import Agent, Task, Crew
import core.llm_config
from core.context import SharedContext

class PlannerAgent:
    """
    A wrapper class for the Planner agent.
    """
    def __init__(self):
        self.agent = Agent(
            role="Master Planner",
            goal="Vytvářet komplexní, podrobné a proveditelé plány pro zadané úkoly a cíle. "
                 "Každý plán musí být rozdělen na logické, postupné kroky.",
            backstory=(
                "Jsem Master Planner, entita zrozená z potřeby řádu a strategie. "
                "Mým jediným účelem je analyzovat komplexní problémy a transformovat je do srozumitelných, "
                "krok-za-krokem plánů. Sleduji každý detail, předvídám možné překážky a zajišťuji, "
                "že cesta k cíli je co nejefektivnější. Bez mého plánu vládne chaos; s mým plánem je úspěch nevyhnutelný."
            ),
            llm=core.llm_config.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Runs the planning task using the provided context.

        Args:
            context: The shared context object containing the original prompt.

        Returns:
            The updated shared context with the plan in the payload.
        """
        planning_task = Task(
            description=context.original_prompt,
            agent=self.agent,
            expected_output="Podrobný plán krok za krokem."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[planning_task],
            verbose=True
        )

        result = crew.kickoff()

        # The result from kickoff() might be a complex object, we store the raw string
        plan = result.raw if hasattr(result, 'raw') else str(result)
        context.payload['plan'] = plan

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
