import yaml
import os
import re
import textwrap
import google.generativeai as genai
from dotenv import load_dotenv

from .system_prompt import SYSTEM_PROMPT
from .tool_executor import ToolExecutor

class JulesOrchestrator:
    """
    Hlavní třída pro orchestraci AI agenta Julese.
    Spravuje jeho životní cyklus, komunikaci s LLM a vykonávání nástrojů.
    """

    def __init__(self, config_path: str, project_root: str = "."):
        """
        Inicializuje orchestrátor.
        Načte konfiguraci, paměťové soubory a připraví prostředí.
        """
        self.project_root = project_root
        self.model = None
        self.history = []
        self.system_prompt = SYSTEM_PROMPT

        # Inicializace ToolExecutoru
        print("INFO: Inicializuji ToolExecutor...")
        self.tool_executor = ToolExecutor(project_root=self.project_root)

        # Načtení konfigurace
        with open(os.path.join(self.project_root, config_path), 'r') as f:
            self.config = yaml.safe_load(f)

        # Načtení paměťových souborů
        jules_md_path = os.path.join(self.project_root, self.config['paths']['jules_md'])
        agents_md_path = os.path.join(self.project_root, self.config['paths']['agents_md'])

        with open(jules_md_path, 'r') as f:
            self.jules_md = f.read()

        with open(agents_md_path, 'r') as f:
            self.agents_md = f.read()

        # Konfigurace Gemini API
        dotenv_path = os.path.join(self.project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)

        api_key = os.getenv("GOOGLE_API_KEY")
        # Ověření, že klíč existuje a není to placeholder
        if api_key and api_key != "VASE_GOOGLE_API_KLIC_ZDE":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.config['model']['name'])
            print("INFO: Klient Gemini API byl úspěšně nakonfigurován.")
        else:
            print("VAROVÁNÍ: API klíč nebyl nalezen nebo je neplatný. Orchestrátor poběží v offline režimu.")

        print("Orchestrator byl úspěšně inicializován.")
        print(f"Model: {self.config['model']['name']}")


    def run(self, initial_task: str):
        """
        Spustí hlavní smyčku agenta s počátečním úkolem.
        """
        print(f"\n--- Zahájení nového úkolu: {initial_task} ---")

        # Přidání úkolu do historie jako první "výsledek" od uživatele
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

        max_iterations = 5  # Pojistka proti nekonečné smyčce
        for i in range(max_iterations):
            print(f"\n--- Iterace č. {i+1} ---")

            # 1. Sestavení promptu
            prompt = self._build_prompt()

            # 2. Volání modelu (pokud je online)
            if not self.model:
                print("CHYBA: Model není k dispozici (offline režim). Ukončuji běh.")
                break

            print("INFO: Odesílám prompt do Gemini API...")
            response = self.model.generate_content(prompt)
            response_text = response.text
            print(f"INFO: Přijata odpověď od modelu.")

            # 3. Parsování volání nástroje
            tool_call = self._parse_tool_call(response_text)
            if not tool_call:
                print("CHYBA: Nepodařilo se zparsovat volání nástroje. Ukončuji běh.")
                break

            print(f"INFO: Zparsováno volání nástroje:\n---\n{tool_call}\n---")

            # 4. Vykonání nástroje pomocí ToolExecutoru
            tool_result = self.tool_executor.execute_tool(tool_call)
            print(f"INFO: Výsledek nástroje:\n---\n{tool_result}\n---")

            # 5. Uložení do historie
            self.history.append((tool_call, tool_result))

            # Prozatímní ukončení po jedné iteraci
            print("\nINFO: Prozatím končím po jedné iteraci pro testovací účely.")
            break

        print("\n--- Úkol dokončen ---")

    def _build_prompt(self) -> str:
        """
        Sestaví kompletní prompt pro LLM z historie a systémových informací.
        Dodržuje strukturu definovanou v Příloze A technického plánu.
        """
        prompt_parts = [self.system_prompt]

        # Sekce 3: Popis Dostupných Nástrojů
        prompt_parts.append("\n# **DOSTUPNÉ NÁSTROJE**\n")
        tool_descriptions = self.tool_executor.get_tool_descriptions()
        prompt_parts.append(tool_descriptions)

        # Sekce 4: Paměťové Soubory
        prompt_parts.append("\n# **DLOUHODOBÁ PAMĚŤ (PRAVIDLA A IDENTITA)**\n")
        prompt_parts.append(f"--- OBSAH souboru: {self.config['paths']['jules_md']} ---\n{self.jules_md}\n")
        prompt_parts.append(f"--- OBSAH souboru: {self.config['paths']['agents_md']} ---\n{self.agents_md}\n")

        # Sekce 5: Historie Aktuálního Úkolu
        prompt_parts.append("# **HISTORIE AKTUÁLNÍHO ÚKOLU**\n")
        if not self.history:
            prompt_parts.append("Zatím nebyla provedena žádná akce. Toto je první krok.\n")
        else:
            for i, (action, result) in enumerate(self.history):
                prompt_parts.append(f"## Akce č. {i+1}:\n<TOOL_CODE_START>\n{action}\n</TOOL_CODE_END>\n")
                prompt_parts.append(f"## Výsledek akce č. {i+1}:\n<TOOL_OUTPUT>\n{result}\n</TOOL_OUTPUT>\n")

        # Sekce 6: Finální Instrukce
        prompt_parts.append("\n# **FINÁLNÍ INSTRUKCE**\n")
        prompt_parts.append("Analyzuj historii a navrhni další krok jako JEDNO volání nástroje v požadovaném formátu.")

        return "\n".join(prompt_parts)

    def _parse_tool_call(self, response: str) -> str:
        """
        Zparsuje odpověď od LLM a extrahuje volání nástroje.
        Očekává kód uzavřený v <TOOL_CODE_START> a <TOOL_CODE_END>.
        Tato metoda také odstraňuje společné odsazení z víceřádkových bloků.
        """
        match = re.search(r"<TOOL_CODE_START>(.*?)</TOOL_CODE_END>", response, re.DOTALL)
        if match:
            code_block = match.group(1)
            # Odstraní společné odsazení, které je běžné u víceřádkových stringů v Pythonu
            dedented_block = textwrap.dedent(code_block)
            # Odstraní přebytečné bílé znaky na začátku a konci celého bloku
            return dedented_block.strip()

        print("VAROVÁNÍ: V odpovědi nebyly nalezeny značky pro volání nástroje.")
        return ""