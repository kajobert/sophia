import os
from core.long_term_memory import LongTermMemory
from core.rich_printer import RichPrinter

class PromptBuilder:
    """
    Třída zodpovědná za sestavování finálního promptu pro LLM s využitím
    hybridní paměti a techniky Retrieval-Augmented Generation (RAG).
    """
    def __init__(self, system_prompt_path: str, ltm: LongTermMemory, short_term_limit: int, long_term_retrieval_limit: int):
        """
        Inicializuje PromptBuilder s přístupem k LTM a paměťovým limitům.
        """
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        self.ltm = ltm
        self.short_term_limit = short_term_limit
        self.long_term_retrieval_limit = long_term_retrieval_limit

    def _load_system_prompt(self, path: str) -> str:
        """Načte systémový prompt ze souboru."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            RichPrinter.error(f"Systémový prompt na cestě '{path}' nebyl nalezen!")
            return "You are a helpful assistant. Please respond to the user's request."

    def build_prompt(self, tool_descriptions: str, history: list, main_goal: str | None = None) -> str:
        """
        Sestaví kompletní prompt pro LLM s využitím RAG a volitelného hlavního cíle.
        """
        prompt_parts = [
            self.system_prompt,
        ]

        # Přidání hlavního cíle mise, pokud je k dispozici
        if main_goal:
            prompt_parts.append("\n# **HLAVNÍ CÍL MISE**\n")
            prompt_parts.append(f"Toto je hlavní cíl, na kterém pracuješ: **{main_goal}**\n")
            prompt_parts.append("Udržuj tento cíl na paměti při plnění dílčích kroků.\n")

        prompt_parts.extend([
            "\n# **DOSTUPNÉ NÁSTROJE**\n",
            tool_descriptions
        ])

        short_term_history = history[-self.short_term_limit:]

        if self.ltm and self.long_term_retrieval_limit > 0:
            query_text = self._create_ltm_query(short_term_history)
            if query_text:
                RichPrinter.info(f"Prohledávám LTM s dotazem: '{query_text[:150]}...'")
                relevant_memories = self.ltm.search_memory(query_text, n_results=self.long_term_retrieval_limit)
                documents = relevant_memories.get('documents', [[]])[0]
                if documents:
                    prompt_parts.append("\n# **RELEVANTNÍ KONTEXT Z ARCHIVU**\n")
                    prompt_parts.append("Toto jsou úryvky z tvé dlouhodobé paměti, které by mohly být relevantní:\n")
                    for i, memory in enumerate(documents):
                        prompt_parts.append(f"--- Archivní záznam {i+1} ---\n{memory}\n--------------------------\n")
                    prompt_parts.append("\n")

        prompt_parts.append("\n# **NEDÁVNÁ HISTORIE (PRACOVNÍ PAMĚŤ)**\n")
        if not short_term_history:
            prompt_parts.append("Zatím nebyla provedena žádná akce. Toto je první krok.\n")
        else:
            for action, result in short_term_history:
                prompt_parts.append(f"## Akce:\n<TOOL_CODE_START>\n{action}\n</TOOL_CODE_END>\n")
                prompt_parts.append(f"## Výsledek:\n<TOOL_OUTPUT>\n{result}\n</TOOL_OUTPUT>\n")

        prompt_parts.append("\n# **FINÁLNÍ INSTRUKCE**\n")
        prompt_parts.append("Analyzuj HLAVNÍ CÍL MISE, KONTEXT Z ARCHIVU a NEDÁVNOU HISTORII a navrhni další krok jako JEDNO volání nástroje v požadovaném formátu JSON.")

        return "".join(prompt_parts)

    def _create_ltm_query(self, history_slice: list) -> str:
        """
        Vytvoří textový dotaz pro LTM z posledních několika interakcí.
        """
        if not history_slice:
            return ""

        # Pro LTM dotaz použijeme pouze poslední uživatelský vstup pro nejvyšší relevanci
        for action, result in reversed(history_slice):
            if "UŽIVATELSKÝ VSTUP" in result:
                return result.replace("UŽIVATELSKÝ VSTUP:", "").strip()

        # Fallback, pokud v krátkodobé historii není uživatelský vstup
        return "\n".join(f"{a}\n{r}" for a, r in history_slice)

    def build_prompt_for_simple_query(self, user_input: str, history: list) -> str:
        """
        Sestaví zjednodušený prompt pro přímou konverzační odpověď.
        """
        simple_system_prompt = (
            "Jsi přátelský a nápomocný AI asistent jménem Jules. "
            "Tvojí úlohou je vést konverzaci a odpovídat na dotazy uživatele. Odpověz stručně a přímo."
        )

        prompt_parts = [simple_system_prompt, "\n\n## Konverzace:\n"]

        short_term_history = history[-self.short_term_limit:]

        history_text = ""
        # Procházíme historii a snažíme se z ní extrahovat dialog
        for action, result in short_term_history:
            if "UŽIVATELSKÝ VSTUP" in result and not action:
                history_text += f"Uživatel: {result.replace('UŽIVATELSKÝ VSTUP:', '').strip()}\n"
            elif "UŽIVATELSKÝ VSTUP" in action:
                history_text += f"Uživatel: {action.replace('UŽIVATELSKÝ VSTUP:', '').strip()}\n"
                # Pokud výsledek nevypadá jako JSON nebo dlouhý výstup, považujeme ho za odpověď
                if len(result) < 500 and not result.strip().startswith('{'):
                    history_text += f"Jules: {result}\n"

        if not history_text.strip():
            prompt_parts.append("Toto je začátek konverzace.\n")
        else:
            prompt_parts.append(history_text)

        prompt_parts.append(f"\nUživatel: {user_input}\nJules:")

        return "".join(prompt_parts)