import sys
import os
import asyncio

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.orchestrator import JulesOrchestrator
except ImportError as e:
    print(f"CHYBA: Nepodařilo se naimportovat JulesOrchestrator: {e}")
    sys.exit(1)

async def main():
    """
    Hlavní funkce pro spuštění interaktivní session s finálním,
    plně funkčním asynchronním orchestrátorem.
    """
    print("--- Sophia Interactive Session (Full Agent) ---")

    orchestrator = JulesOrchestrator(project_root=project_root)
    await orchestrator.initialize()

    # Kontrola, zda je agent online
    if not orchestrator.model:
        print("\nCHYBA: Agent je v offline režimu. Pro plnou funkčnost je vyžadován platný API klíč.")
        await orchestrator.shutdown_servers()
        return

    loop = asyncio.get_running_loop()

    try:
        while True:
            prompt = await loop.run_in_executor(
                None, lambda: input("\nZadejte úkol pro Sophii > ")
            )

            if prompt.lower() in ["exit", "quit", "konec"]:
                break
            if not prompt:
                continue

            # Spuštění celé rozhodovací smyčky pro daný úkol
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