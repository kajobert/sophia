from crewai import Agent, Task, Crew
from core.context import SharedContext


class PlannerAgent:
    """
    A wrapper class for the Planner agent.
    """

    def __init__(self, llm):
        self.agent = Agent(
            role="Master Planner",
            goal="Vytvářet komplexní, podrobné a proveditelné plány pro zadané úkoly a cíle. "
            "Každý plán musí být rozdělen na logické, postupné kroky.",
            backstory=(
                "Jsem Master Planner, entita zrozená z potřeby řádu a strategie. "
                "Mým jediným účelem je analyzovat komplexní problémy a transformovat je do srozumitelných, "
                "krok-za-krokem plánů. Sleduji každý detail, předvídám možné překážky a zajišťuji, "
                "že cesta k cíli je co nejefektivnější. Bez mého plánu vládne chaos; s mým plánem je úspěch nevyhnutelný."
            ),
            llm=llm,
            tools=[],  # EthicalReviewTool was removed as it's deprecated
            verbose=True,
            allow_delegation=False,
            max_iter=5,
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Runs the planning task using the provided context.
        """
        task_description = (
            "Analyze the following user request and create a detailed, step-by-step plan to accomplish it. "
            "The plan should be clear, logical, and easy for another AI agent to follow. "
            f"User Request: {context.original_prompt}"
        )

        expected_output = (
            "A markdown-formatted, step-by-step plan. Each step should be a clear, actionable instruction. "
            "Do not add any conversational fluff or explanations outside of the plan itself."
        )

        planning_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=expected_output,
        )

        crew = Crew(agents=[self.agent], tasks=[planning_task], verbose=True)

        result = crew.kickoff()

        plan = result.raw if hasattr(result, "raw") else str(result)

        context.payload["plan"] = plan.strip()

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
