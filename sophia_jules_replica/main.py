import argparse
import os
import sys

def main():
    """
    Hlavní funkce pro spuštění AI agenta Julese.
    """
    # Zajištění, že kořenový adresář projektu je v sys.path
    # To umožňuje spouštění skriptu z různých míst
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from core.orchestrator import JulesOrchestrator
    except ImportError:
        print("CHYBA: Nepodařilo se naimportovat JulesOrchestrator.")
        print("Ujistěte se, že spouštíte skript z kořenového adresáře 'sophia_jules_replica' nebo že je tento adresář v PYTHONPATH.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="AI Agent Jules - Sophia Replica")
    parser.add_argument("task", type=str, help="Počáteční úkol pro agenta.")

    args = parser.parse_args()

    config_path = "config/config.yaml"

    print("--- Spouštím AI Agenta Julese ---")

    # Inicializace orchestrátoru
    # project_root je nyní předáván, aby se zajistily správné cesty
    orchestrator = JulesOrchestrator(config_path=config_path, project_root=project_root)

    # Detekce a reportování provozního režimu
    if orchestrator.model:
        print("PROVOZNÍ REŽIM: ONLINE (API klíč je platný)")
    else:
        print("PROVOZNÍ REŽIM: OFFLINE (API klíč chybí nebo je neplatný)")

    # Spuštění hlavní smyčky agenta
    orchestrator.run(initial_task=args.task)

if __name__ == "__main__":
    main()