import sys
import os
import asyncio
import argparse

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.orchestrator import JulesOrchestrator
except ImportError as e:
    print(f"CHYBA: Nepodařilo se naimportovat JulesOrchestrator z 'core': {e}")
    sys.exit(1)

async def main():
    """
    Hlavní funkce pro jednorázové spuštění agenta s konkrétním úkolem.
    """
    parser = argparse.ArgumentParser(description="Sophia V2 - Task Runner")
    parser.add_argument("task", type=str, help="Úkol, který má agent provést.")
    args = parser.parse_args()

    orchestrator = JulesOrchestrator(project_root=project_root)
    try:
        await orchestrator.initialize()

        if not orchestrator.model:
            print("\nCHYBA: Agent je v offline režimu. Pro spuštění úkolu je vyžadován platný API klíč.")
            return

        await orchestrator.run(args.task)

    except Exception as e:
        import traceback
        print(f"\nDošlo k neočekávané kritické chybě: {e}")
        traceback.print_exc()
    finally:
        await orchestrator.shutdown()
        print("\nBěh agenta byl ukončen.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")