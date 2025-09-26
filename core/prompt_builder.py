import os

class PromptBuilder:
    """
    Třída zodpovědná za sestavování finálního promptu pro LLM.
    """
    def __init__(self, system_prompt_path: str):
        self.system_prompt = self._load_system_prompt(system_prompt_path)

    def _load_system_prompt(self, path: str) -> str:
        """Načte systémový prompt ze souboru."""
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            print(f"VAROVÁNÍ: Soubor se systémovým promptem nebyl nalezen na '{path}'. Používám výchozí.")
            return "Jsi nápomocný asistent."

    def build_prompt(self, tool_descriptions: str, history: list) -> str:
        """
        Sestaví kompletní prompt pro LLM z historie a systémových informací.
        """
        prompt_parts = [
            self.system_prompt,
            "\n# **DOSTUPNÉ NÁSTROJE**\n",
            tool_descriptions,
            "\n# **HISTORIE AKTUÁLNÍHO ÚKOLU**\n"
        ]
        if not history:
            prompt_parts.append("Zatím nebyla provedena žádná akce. Toto je první krok.\n")
        else:
            for action, result in history:
                prompt_parts.append(f"## Akce:\n<TOOL_CODE_START>\n{action}\n</TOOL_CODE_END>\n")
                prompt_parts.append(f"## Výsledek:\n<TOOL_OUTPUT>\n{result}\n</TOOL_OUTPUT>\n")

        prompt_parts.append("\n# **FINÁLNÍ INSTRUKCE**\n")
        prompt_parts.append("Analyzuj historii a navrhni další krok jako JEDNO volání nástroje v požadovaném formátu.")
        return "".join(prompt_parts)