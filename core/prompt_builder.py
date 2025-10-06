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

        Args:
            system_prompt_path (str): Cesta k souboru se systémovým promptem.
            ltm (LongTermMemory): Instance správce dlouhodobé paměti.
            short_term_limit (int): Počet posledních interakcí pro krátkodobou paměť.
            long_term_retrieval_limit (int): Počet záznamů k načtení z dlouhodobé paměti.
        """
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        self.ltm = ltm
        self.short_term_limit = short_term_limit
        self.long_term_retrieval_limit = long_term_retrieval_limit

    def _load_system_prompt(self, path: str) -> str:
        """Načte systémový prompt ze souboru."""
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            RichPrinter.error(f"Systémový prompt na cestě '{path}' nebyl nalezen!")
            return "You are a helpful assistant. Please respond to the user's request."

    def build_prompt(self, tool_descriptions: str, history: list) -> str:
        """
        Sestaví kompletní prompt pro LLM s využitím RAG.
        """
        prompt_parts = [
            self.system_prompt,
            "\n# **DOSTUPNÉ NÁSTROJE**\n",
            tool_descriptions
        ]

        # 1. Správa krátkodobé paměti (pracovní paměť)
        short_term_history = history[-self.short_term_limit:]

        # 2. RAG: Vyhledání relevantních záznamů v dlouhodobé paměti
        if self.ltm and self.long_term_retrieval_limit > 0:
            # Vytvoření dotazu z nejnovějšího dění
            query_text = self._create_ltm_query(short_term_history)

            if query_text:
                RichPrinter.info(f"Prohledávám LTM s dotazem: '{query_text[:150]}...'")
                relevant_memories = self.ltm.search_memory(query_text, n_results=self.long_term_retrieval_limit)

                documents = relevant_memories.get('documents', [[]])[0]
                if documents:
                    prompt_parts.append("\n# **RELEVANTNÍ KONTEXT Z ARCHIVU**\n")
                    prompt_parts.append("Toto jsou úryvky z tvé dlouhodobé paměti, které by mohly být relevantní pro aktuální úkol:\n")
                    for i, memory in enumerate(documents):
                        prompt_parts.append(f"--- Archivní záznam {i+1} ---\n{memory}\n--------------------------\n")
                    prompt_parts.append("\n")

        # 3. Přidání krátkodobé historie do promptu
        prompt_parts.append("\n# **NEDÁVNÁ HISTORIE (PRACOVNÍ PAMĚŤ)**\n")
        if not short_term_history:
            prompt_parts.append("Zatím nebyla provedena žádná akce. Toto je první krok.\n")
        else:
            for action, result in short_term_history:
                prompt_parts.append(f"## Akce:\n<TOOL_CODE_START>\n{action}\n</TOOL_CODE_END>\n")
                prompt_parts.append(f"## Výsledek:\n<TOOL_OUTPUT>\n{result}\n</TOOL_OUTPUT>\n")

        prompt_parts.append("\n# **FINÁLNÍ INSTRUKCE**\n")
        prompt_parts.append("Analyzuj KONTEXT Z ARCHIVU a NEDÁVNOU HISTORII a navrhni další krok jako JEDNO volání nástroje v požadovaném formátu JSON.")

        return "".join(prompt_parts)

    def _create_ltm_query(self, history_slice: list) -> str:
        """
        Vytvoří textový dotaz pro LTM z posledních několika interakcí.
        """
        if not history_slice:
            return ""

        # Spojíme posledních pár interakcí do jednoho textu
        query_parts = []
        for action, result in history_slice:
            if "UŽIVATELSKÝ VSTUP" in result:
                 # Pokud je to první vstup, použijeme ho jako hlavní dotaz
                return result.replace("UŽIVATELSKÝ VSTUP:", "").strip()
            query_parts.append(action)
            query_parts.append(result)

        return "\n".join(query_parts)