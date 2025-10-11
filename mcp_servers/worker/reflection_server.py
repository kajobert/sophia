import os
import sys
from typing import List, Dict, Any

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.llm_manager import LLMManager
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter

class ReflectionServer:
    """
    Tento server poskytuje nástroje pro sebereflexi agenta.
    Umožňuje agentovi analyzovat svou nedávnou historii akcí a poučit se z ní.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.reflection_prompt_path = os.path.join(self.project_root, "prompts", "reflection_prompt.txt")

    async def reflect_on_recent_steps(self, history: List[Dict[str, Any]], last_user_input: str) -> str:
        """
        Analyzuje nedávné kroky, identifikuje klíčové poznatky a navrhne ponaučení pro budoucnost.

        Args:
            history: Historie konverzace a akcí agenta.
            last_user_input: Poslední vstup od uživatele, který vedl k dané sekvenci akcí.

        Returns:
            Stručné ponaučení nebo klíčový poznatek.
        """
        try:
            with open(self.reflection_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            return "Chyba: Soubor s promptem pro reflexi nebyl nalezen."

        # Formátování historie pro lepší čitelnost v promptu
        formatted_history = ""
        for i, (request, response) in enumerate(history):
            formatted_history += f"KROK {i+1}:\n"
            formatted_history += f"  MYŠLENKA/AKCE:\n{request}\n"
            formatted_history += f"  VÝSLEDEK:\n{response}\n\n"

        prompt = system_prompt.format(
            last_user_input=last_user_input,
            history=formatted_history
        )

        model = self.llm_manager.get_llm(self.llm_manager.default_model_name)

        try:
            RichPrinter.info("Zahajuji sebereflexi...")
            reflection, _ = await model.generate_content_async(prompt)
            RichPrinter.log_communication("Výsledek sebereflexe", reflection, style="magenta")
            return reflection.strip()
        except Exception as e:
            RichPrinter.log_error_panel("Chyba při generování reflexe", str(e), exception=e)
            return f"Chyba při komunikaci s LLM během reflexe: {e}"

if __name__ == '__main__':
    # Příklad použití pro manuální testování
    async def main():
        # Příklad historie
        example_history = [
            (
                '{\n  "thought": "Nejprve musím zjistit, jaké soubory jsou v kořenovém adresáři, abych se zorientoval.",\n  "tool_call": {\n    "tool_name": "list_files",\n    "args": [],\n    "kwargs": {}\n  }\n}',
                '["main.py", "requirements.txt", "tests/"]'
            ),
            (
                '{\n  "thought": "Dobře, vidím `main.py`. Chci se podívat na jeho obsah, abych pochopil, co program dělá.",\n  "tool_call": {\n    "tool_name": "read_file",\n    "args": ["main.py"],\n    "kwargs": {}\n  }\n}',
                'def hello():\n    print("Hello, world!")\n\nhello()'
            ),
            (
                '{\n  "thought": "Program je velmi jednoduchý. Úkolem je přidat funkci pro sčítání. Vytvořím novou funkci `add` a upravím volání.",\n  "tool_call": {\n    "tool_name": "replace_with_git_merge_diff",\n    "args": ["main.py"],\n    "kwargs": {\n      "search_block": "def hello():\\n    print(\\"Hello, world!\\")\\n\\nhello()",\n      "replace_block": "def add(a, b):\\n    return a + b\\n\\ndef hello():\\n    print(\\"Hello, world!\\")\\n\\nprint(f\\"2+3={add(2,3)}\\")"\n    }\n  }\n}',
                'File `main.py` updated successfully.'
            ),
            (
                '{\n  "thought": "Udělal jsem chybu. Měl jsem zavolat `hello()` a ne jen `add`. A navíc jsem nevolal `hello`. Musím to opravit.",\n  "tool_call": {\n    "tool_name": "replace_with_git_merge_diff",\n    "args": ["main.py"],\n    "kwargs": {\n      "search_block": "print(f\\\\"2+3={add(2,3)}\\\\")",\n      "replace_block": "hello()\\nprint(f\\\\"2+3={add(2,3)}\\\\")"\n    }\n  }\n}',
                'Tool execution failed: Search block not found in file.'
            )
        ]
        last_user_input = "Přidej do `main.py` funkci, která sečte dvě čísla a zavolej ji."

        server = ReflectionServer(project_root=".")
        reflection = await server.reflect_on_recent_steps(example_history, last_user_input)
        print("\n--- VÝSLEDNÉ PONAUČENÍ ---")
        print(reflection)

    import asyncio
    asyncio.run(main())