from crewai import Agent, Task, Crew
from core.context import SharedContext
from tools.ethical_reviewer import EthicalReviewTool

class PlannerAgent:
    """
    A wrapper class for the Planner agent.
    """
    def __init__(self, llm):
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
            llm=llm,
            tools=[EthicalReviewTool()],
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
        # Úprava popisu úkolu tak, aby zahrnoval použití Ethical Review Tool
        task_description = (
            f"Analyzuj tento požadavek: '{context.original_prompt}'.\n"
            "1. Vytvoř podrobný, krok-za-krokem plán pro splnění tohoto požadavku.\n"
            "2. Použij 'Ethical Review Tool' k analýze vytvořeného plánu a zhodnocení jeho etických dopadů.\n"
            "Výstup musí obsahovat jak plán, tak i výsledek etické revize."
        )

        planning_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output="Finální odpověď musí obsahovat podrobný plán a kompletní, nezkrácenou etickou revizi."
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[planning_task],
            verbose=True
        )

        result = crew.kickoff()

        # The result from kickoff() might be a complex object, we store the raw string
        output = result.raw if hasattr(result, 'raw') else str(result)

        # Rozparsování výstupu na plán a etickou revizi
        # Očekáváme, že revize začíná klíčovou frází "Ethical Review Feedback:"
        review_keyword = "Ethical Review Feedback:"
        if review_keyword in output:
            parts = output.split(review_keyword, 1)
            plan = parts[0].strip()
            ethical_review = review_keyword + parts[1].strip()
        else:
            # Fallback, pokud klíčové slovo není nalezeno
            plan = output
            ethical_review = "Ethical review not found in the output."

        context.payload['plan'] = plan
        context.payload['ethical_review'] = ethical_review

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
