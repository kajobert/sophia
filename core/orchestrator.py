import sys
import os
import json
import asyncio
import re
import textwrap
import uuid
from dotenv import load_dotenv
import yaml

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.mcp_client import MCPClient
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter
from core.memory_manager import MemoryManager
from core.llm_manager import LLMManager
from core.cost_manager import CostManager
from core.long_term_memory import LongTermMemory

class JulesOrchestrator:
    """
    Finální, asynchronní orchestrátor, který řídí agenta, komunikuje s LLM
    a ukládá své zkušenosti do perzistentní paměti.
    """

    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.verbose = False
        self.last_full_output = None
        self.total_tokens = 0
        self.mcp_client = MCPClient(project_root=self.project_root)
        self.memory_manager = MemoryManager()
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.cost_manager = CostManager(project_root=self.project_root)
        self.ltm = LongTermMemory(project_root=self.project_root)
        self.status_widget = status_widget

        # Načtení specifické konfigurace pro orchestrátor
        orchestrator_config = self.llm_manager.config.get("orchestrator", {})
        self.max_iterations = orchestrator_config.get("max_iterations", 15)

        # Načtení konfigurace pro paměťový systém
        memory_config = self.llm_manager.config.get("memory", {})
        self.short_term_limit = memory_config.get("short_term_limit", 4)
        self.long_term_retrieval_limit = memory_config.get("long_term_retrieval_limit", 5)

        # Inicializace PromptBuilderu s přístupem k LTM a konfiguraci
        self.prompt_builder = PromptBuilder(
            system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"),
            ltm=self.ltm,
            short_term_limit=self.short_term_limit,
            long_term_retrieval_limit=self.long_term_retrieval_limit
        )

        RichPrinter.info("V2 Orchestrator initialized with LLMManager and CostManager.")

    async def initialize(self):
        """Provede kompletní inicializaci."""
        # _load_config se volá v LLMManager, není třeba ho volat zde znovu
        await self.mcp_client.start_servers()

    async def shutdown(self):
        """Bezpečně ukončí všechny spuštěné služby."""
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.info("Všechny služby byly bezpečně ukončeny.")

    def _triage_task_and_select_llm(self, prompt: str) -> str:
        """
        Inteligentně analyzuje prompt a vybere nejvhodnější LLM model.
        Zohledňuje složitost úkolu, odhad tokenů a historickou efektivitu.
        """
        prompt_lower = prompt.lower()
        
        # Rozšířená sada klíčových slov pro lepší klasifikaci
        complex_keywords = [
            "analyzuj", "refaktoruj", "navrhni", "implementuj", "vytvoř kód",
            "optimalizuj", "debuguj", "architektura", "návrh", "složitý",
            "komplexní", "algoritmus", "datová struktura", "design pattern"
        ]
        
        simple_keywords = [
            "vypiš", "přečti", "zkontroluj", "potvrď", "zobraz",
            "seznam", "informace", "stav", "status", "pomoc"
        ]
        
        # Analýza složitosti na základě délky a struktury
        word_count = len(prompt.split())
        line_count = len(prompt.split('\n'))
        has_code_blocks = '```' in prompt
        
        # Skóre složitosti (0-100)
        complexity_score = 0
        
        # Klíčová slova (váha 40%)
        keyword_weight = 0
        if any(keyword in prompt_lower for keyword in complex_keywords):
            keyword_weight += 70
        if any(keyword in prompt_lower for keyword in simple_keywords):
            keyword_weight -= 30
        complexity_score += max(0, min(100, keyword_weight)) * 0.4
        
        # Délka promptu (váha 30%)
        length_weight = min(100, word_count * 0.5)  # 200 slov = 100 bodů
        complexity_score += length_weight * 0.3
        
        # Struktura (váha 30%)
        structure_weight = 0
        if line_count > 5:
            structure_weight += 30
        if has_code_blocks:
            structure_weight += 40
        if 'def ' in prompt_lower or 'class ' in prompt_lower:
            structure_weight += 30
        complexity_score += structure_weight * 0.3
        
        # Rozhodnutí na základě skóre složitosti
        if complexity_score >= 60:
            return "powerful"
        elif complexity_score <= 20:
            return "economical"
        else:
            return self.llm_manager.default_llm_name

    async def run(self, initial_task: str, session_id: str | None = None):
        """Hlavní rozhodovací smyčka agenta."""
        TERMINAL_TOOLS = [
            "inform_user",
            "warn_user",
            "error_user",
            "display_code",
            "display_table",
            "ask_user"
        ]

        if session_id:
            RichPrinter.info(f"### Obnovuji sezení: {session_id}")
            loaded_history = self.memory_manager.load_history(session_id)
            if loaded_history:
                self.history = loaded_history
                RichPrinter.info(f"Historie pro sezení '{session_id}' byla úspěšně načtena ({len(self.history)} kroků).")
            else:
                RichPrinter.warning(f"Pro sezení '{session_id}' nebyla nalezena žádná historie. Vytvářím nové sezení.")
                session_id = str(uuid.uuid4()) # Vytvoříme nové ID, pokud staré nebylo nalezeno
        else:
            session_id = str(uuid.uuid4())
            RichPrinter.info(f"### Zahájení nového sezení (ID: {session_id})")

        RichPrinter.info(f"Úkol: {initial_task}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))
        self.memory_manager.save_history(session_id, self.history)


        task_was_completed_by_agent = False
        for i in range(len(self.history), self.max_iterations):
            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            # Fáze 1: Výběr modelu
            selected_model_name = self._triage_task_and_select_llm(prompt)

            try:
                model = self.llm_manager.get_llm(selected_model_name)
                RichPrinter.info(f"Vybrán model: [bold cyan]{model.model_name}[/bold cyan] (alias: {selected_model_name})")
            except (ValueError, FileNotFoundError) as e:
                RichPrinter.error(f"Nepodařilo se načíst model '{selected_model_name}': {e}")
                break

            # Fáze 2: Volání LLM s vynuceným JSON formátem
            RichPrinter.info(f"### Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}")
            RichPrinter.info(f"Přemýšlím... (model: {model.model_name})")

            if self.verbose:
                RichPrinter.agent_markdown(f"**Prompt odeslaný do LLM:**\n\n```\n{prompt}\n```")

            # --- Finální, robustní logika pro streamování a parsování ---
            full_response_text = ""

            # 1. Callback pouze sbírá data, nic nezobrazuje.
            async def stream_callback(chunk: str):
                nonlocal full_response_text
                full_response_text += chunk
                # V TUI se bude zobrazovat tečka nebo spinner, ne surový JSON
                RichPrinter.stream_explanation(".")

            # 2. Zavoláme LLM se streamováním a vynuceným JSON výstupem.
            response_text, usage_data = await model.generate_content_async(
                prompt,
                stream_callback=stream_callback,
                response_format={"type": "json_object"} # Správný způsob, jak vynutit JSON
            )

            # Ukončíme "načítací" animaci v TUI
            RichPrinter.finish_explanation_stream()

            # 3. Zpracujeme náklady a tokeny
            if usage_data:
                generation_id = usage_data.get("id")
                if generation_id:
                    cost = await self.cost_manager.get_generation_cost(generation_id)
                    self.cost_manager.add_cost(cost)
                    RichPrinter.info(f"Náklady na tento krok: ${cost:.6f} | Celkové náklady: {self.cost_manager.get_total_cost_str()}")

                if usage_data.get("usage"):
                    token_count = usage_data["usage"].get("total_tokens", 0)
                    self.total_tokens += token_count
                    RichPrinter.info(f"Počet spotřebovaných tokenů v tomto kroku: {token_count}")

            # 4. Až zde, s kompletní odpovědí, parsujeme a zobrazujeme.
            explanation, tool_call_data = self._parse_llm_response(response_text)

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.warning("LLM se rozhodl nepoužít nástroj v tomto kroku nebo se JSON nepodařilo zparsovat. Pokračuji v přemýšlení.")
                # I když se streamovalo, finální vysvětlení uložíme do historie
                if explanation:
                    self.history.append((explanation, "Žádná akce."))
                    self.memory_manager.save_history(session_id, self.history)
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.info(">>> AKCE")
            RichPrinter.agent_tool_code(json.dumps(tool_call_data, indent=2, ensure_ascii=False))

            # Sestavení záznamu do historie (myšlenkový pochod + volání nástroje)
            history_entry_request = f"Myšlenkový pochod:\n{explanation}\n\nVolání nástroje:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"

            if tool_name == "task_complete":
                RichPrinter.info("Agent signalizoval dokončení úkolu. Ukládám vzpomínku...")
                summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")

                # Zobrazíme finální shrnutí ve speciálním panelu v TUI
                RichPrinter.show_task_complete(summary)

                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter.info(f"Vzpomínka pro session {session_id} byla úspěšně uložena.")
                task_was_completed_by_agent = True # Nastavíme příznak
                break

            if tool_name == "show_last_output":
                RichPrinter.info("<<< VÝSLEDEK (Z paměti)")
                output = "V paměti není žádný předchozí dlouhý výstup."
                if self.last_full_output:
                    output = self.last_full_output
                    RichPrinter.agent_tool_output(output)
                else:
                    RichPrinter.warning(output)

                # Klíčová oprava: Přidáme plný výstup do historie, aby se přerušila smyčka
                self.history.append((history_entry_request, output))
                self.memory_manager.save_history(session_id, self.history)
                continue

            if tool_name == "reload_tools":
                RichPrinter.info("Přijat příkaz k restartování dynamického serveru nástrojů...")
                await self.mcp_client.restart_server('dynamic_tool_server.py')
                result = "Server s dynamickými nástroji byl restartován. Nové nástroje by nyní měly být k dispozici."
            else:
                result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            # --- Inteligentní ukončení úkolu ---
            # Pokud byl použit "terminální" nástroj, považujeme úkol za dokončený.
            if tool_name in TERMINAL_TOOLS:
                RichPrinter.info(f"Terminální nástroj '{tool_name}' byl použit. Úkol se automaticky ukončuje.")
                task_was_completed_by_agent = True
                # Výstup nástroje se ještě zpracuje a uloží, ale smyčka se poté ukončí.

            output_for_display, output_for_history = self._handle_long_output(result)

            RichPrinter.info("<<< VÝSLEDEK")
            RichPrinter.agent_tool_output(output_for_display)

            # Uložení do krátkodobé paměti (historie)
            self.history.append((history_entry_request, output_for_history))
            self.memory_manager.save_history(session_id, self.history)

            # Uložení kompletní interakce do dlouhodobé paměti (LTM)
            ltm_entry = f"Krok {i+1}:\nMyšlenkový pochod a akce:\n{history_entry_request}\n\nVýsledek:\n{output_for_history}"
            self.ltm.add_memory(ltm_entry, metadata={"session_id": session_id, "iteration": i + 1})

            # Pokud byl použit terminální nástroj, ukončíme smyčku zde.
            if task_was_completed_by_agent:
                break

        if not task_was_completed_by_agent:
            final_message = f"Agent dosáhl maximálního počtu iterací ({self.max_iterations}). Úkol byl ukončen."
            RichPrinter.warning(final_message)
            # Uložíme session i v tomto případě, ale s jiným shrnutím
            summary = f"Úkol byl automaticky ukončen po dosažení limitu {self.max_iterations} iterací."
            self.memory_manager.save_session(session_id, initial_task, summary)
            RichPrinter.info(f"Vzpomínka pro session {session_id} byla uložena s poznámkou o přerušení.")
        else:
            final_message = "Agent dokončil úkol."

        RichPrinter.info(f"### {final_message} (Celkem spotřebováno: {self.total_tokens} tokenů)")

    def _parse_llm_response(self, response_text: str) -> tuple[str, dict | None]:
        """
        Paruje JSON odpověď od LLM.
        Očekává, že odpověď je validní JSON díky vynucenému režimu.
        Zvládá i případy, kdy je JSON zabalen v Markdown bloku.
        Vrací (explanation, tool_call_data).
        """
        # Odstranění případného Markdown obalu
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()

        try:
            parsed_response = json.loads(cleaned_text)
            explanation = parsed_response.get("explanation", "").strip()
            tool_call_data = parsed_response.get("tool_call")

            # Zobrazíme myšlenkový pochod, který jsme dostali v JSONu
            RichPrinter.stream_explanation(explanation)
            return explanation, tool_call_data

        except json.JSONDecodeError:
            RichPrinter.error("Kritické selhání: Odpověď LLM nebyla validní JSON, přestože byl vynucen JSON režim.")
            RichPrinter.error(f"Přijatá odpověď (po čištění, prvních 500 znaků): {cleaned_text[:500]}")
            explanation = f"[SYSTÉM]: CHYBA PARSOVÁNÍ JSON. {cleaned_text}"
            return explanation, None

    def _handle_long_output(self, result: str) -> tuple[str, str]:
        """Zpracuje dlouhé výstupy, uloží je a vrátí shrnutí."""
        line_limit = 20
        if isinstance(result, str) and len(result.splitlines()) > line_limit:
            self.last_full_output = result
            summary = f"Výstup je příliš dlouhý ({len(result.splitlines())} řádků). Prvních {line_limit-2} řádků:\n"
            summary += "\n".join(result.splitlines()[:line_limit-2])
            summary += "\n[...]"
            summary += "\n\n(Pro zobrazení celého výstupu použijte nástroj 'show_last_output'.)"
            return summary, summary
        return result, result
