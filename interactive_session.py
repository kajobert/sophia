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
    Hlavní funkce pro spuštění interaktivní REPL session s finální
    asynchronní MCP architekturou.
    """
    print("--- Sophia Interactive Session (Async MCP Architecture) ---")

    orchestrator = JulesOrchestrator()
    await orchestrator.start_servers()

    loop = asyncio.get_running_loop()

    try:
        while True:
            # Použití executoru pro neblokující input()
            prompt = await loop.run_in_executor(
                None, lambda: input("\n> ")
            )

            if prompt.lower() in ["exit", "quit", "konec"]:
                break
            if not prompt:
                continue

            await orchestrator.run_task(prompt)

    except KeyboardInterrupt:
        print("\nUkončuji session...")
    finally:
        await orchestrator.shutdown_servers()
        print("Na shledanou!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")