import sys
import os
from crewai.tools import BaseTool

# Přidání cesty k `core` modulu, aby fungoval import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Nyní můžeme importovat, ale uděláme to uvnitř metody, abychom se vyhnuli cyklickým závislostem při startu
# from core.ethos_module import run_ethical_review

class EthicalReviewTool(BaseTool):
    """
    Nástroj pro etickou revizi, který analyzuje plán proti DNA projektu.
    """
    name: str = "Ethical Review Tool"
    description: str = "Analyzes a plan for ethical alignment based on the project's DNA."

    def _run(self, plan: str) -> str:
        """
        Spustí etickou analýzu na daném plánu.

        Args:
            plan (str): Plán, který má být analyzován.

        Returns:
            str: Výsledek etické revize.
        """
        # Dynamický import, abychom se vyhnuli problémům s importy při inicializaci
        from core.ethos_module import EthosModule

        # Vytvoření instance EthosModule a spuštění hodnocení
        ethos = EthosModule()
        review_result = ethos.evaluate(plan=plan)

        # Formátování výstupu pro agenta
        return f"Ethical Review Feedback: {review_result['feedback']} (Decision: {review_result['decision']})"
