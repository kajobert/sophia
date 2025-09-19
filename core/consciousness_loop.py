"""
Orchestrátor tvorby: Planner -> Engineer -> Tester -> zpětná vazba
"""

from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent


def orchestrate_task(task_description):
    # 1. Plánování
    plan = PlannerAgent.llm(task_description)
    print(f"[PLANNER] Plán: {plan}")

    # 2. Implementace
    code_result = EngineerAgent.llm(plan)
    print(f"[ENGINEER] Výsledek implementace: {code_result}")

    # 3. Testování
    test_result = TesterAgent.llm(plan)
    print(f"[TESTER] Výsledek testů: {test_result}")

    # 4. Zpětná vazba a případná revize
    if "fail" in str(test_result).lower() or "error" in str(test_result).lower():
        print("[LOOP] Testy selhaly, vracím úkol inženýrovi k revizi.")
        # V reálné implementaci by zde byl cyklus revize
    else:
        print("[LOOP] Úkol úspěšně dokončen.")


if __name__ == "__main__":
    orchestrate_task("Vytvoř funkci pro součet dvou čísel a napiš k ní unit test.")
