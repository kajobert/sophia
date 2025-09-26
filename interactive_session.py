import sys
import os
import asyncio

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import z finální, integrované architektury v 'core'
    from core.orchestrator import JulesOrchestrator
except ImportError as e:
    print(f"CHYBA: Nepodařilo se naimportovat JulesOrchestrator z 'core': {e}")
    sys.exit(1)

async def main():
    """
    Hlavní funkce pro spuštění interaktivní session s finální
    V2 architekturou.
    """
    print("--- Sophia V2 Interactive Session ---")

    orchestrator = JulesOrchestrator(project_root=project_root)
    try:
        await orchestrator.initialize()

        if not orchestrator.model:
            print("\nCHYBA: Agent je v offline režimu. Pro plnou funkčnost je vyžadován platný API klíč.")
            return

        loop = asyncio.get_running_loop()

        while True:
            prompt = await loop.run_in_executor(
                None, lambda: input("\nZadejte úkol pro Sophii > ")
            )

            if prompt.lower() in ["exit", "quit", "konec"]:
                break
            if not prompt:
                continue

            await orchestrator.run(prompt)

    except KeyboardInterrupt:
        print("\nUkončuji session...")
    finally:
        await orchestrator.shutdown()
        print("Na shledanou!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")