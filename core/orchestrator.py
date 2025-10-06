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

from tui.messages import ChatMessage
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
        RichPrinter._post(ChatMessage(f"{initial_task}", owner='user', msg_type='user_input'))
        RichPrinter.log_communication("Vstup od uživatele", initial_task, style="green")
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
                error_title = "Selhání načtení LLM modelu"
                error_content = (
                    f"Nepodařilo se načíst nebo inicializovat požadovaný model '{selected_model_name}'. "
                    "To může být způsobeno chybějící konfigurací, neplatným API klíčem nebo nedostupností služby."
                )
                RichPrinter.log_error_panel(error_title, error_content, exception=e)
                # Po kritické chybě, která brání pokračování, ukončíme smyčku.
                break

            # Fáze 2: Volání LLM s vynuceným JSON formátem
            RichPrinter.info(f"### Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}")
            RichPrinter.info(f"Přemýšlím... (model: {model.model_name})")

            if self.verbose:
                RichPrinter._post(ChatMessage(f"**Prompt odeslaný do LLM:**\n\n```\n{prompt}\n```", owner='agent', msg_type='verbose'))

            # --- Finální, robustní logika pro streamování a parsování ---
            full_response_text = ""

            # 1. Callback pouze sbírá data a posílá je do TUI.
            async def stream_callback(chunk: str):
                nonlocal full_response_text
                full_response_text += chunk
                RichPrinter._post(ChatMessage(chunk, owner='agent', msg_type='explanation_chunk'))

            # 2. Zavoláme LLM se streamováním a vynuceným JSON výstupem.
            response_text, usage_data = await model.generate_content_async(
                prompt,
                stream_callback=stream_callback,
                response_format={"type": "json_object"} # Správný způsob, jak vynutit JSON
            )

            # Ukončíme "načítací" animaci v TUI
            RichPrinter._post(ChatMessage("", owner='agent', msg_type='explanation_end'))

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

            if explanation:
                RichPrinter.log_communication("Myšlenkový pochod", explanation, style="dim blue")

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.warning("LLM se rozhodl nepoužít nástroj v tomto kroku nebo se JSON nepodařilo zparsovat. Pokračuji v přemýšlení.")
                RichPrinter.log_communication("Rozhodnutí agenta", "Žádná akce v tomto kroku.", style="yellow")
                if explanation:
                    self.history.append((explanation, "Žádná akce."))
                    self.memory_manager.save_history(session_id, self.history)
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.info(">>> AKCE")
            # RichPrinter._post(ChatMessage(json.dumps(tool_call_data, indent=2, ensure_ascii=False), owner='agent', msg_type='tool_code')) # Nahrazeno log_communication
            RichPrinter.log_communication("Volání nástroje", tool_call_data, style="yellow")

            history_entry_request = f"Myšlenkový pochod:\n{explanation}\n\nVolání nástroje:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"

            if tool_name == "task_complete":
                RichPrinter.info("Agent signalizoval dokončení úkolu. Ukládám vzpomínku...")
                summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")
                RichPrinter._post(ChatMessage(summary, owner='agent', msg_type='task_complete'))
                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter.info(f"Vzpomínka pro session {session_id} byla úspěšně uložena.")
                task_was_completed_by_agent = True
                break

            if tool_name == "show_last_output":
                RichPrinter.info("<<< VÝSLEDEK (Z paměti)")
                output = "V paměti není žádný předchozí dlouhý výstup."
                if self.last_full_output:
                    output = self.last_full_output
                    RichPrinter._post(ChatMessage(output, owner='agent', msg_type='tool_output'))
                else:
                    RichPrinter.warning(output)
                self.history.append((history_entry_request, output))
                self.memory_manager.save_history(session_id, self.history)
                continue

            if tool_name == "reload_tools":
                RichPrinter.info("Přijat příkaz k restartování dynamického serveru nástrojů...")
                await self.mcp_client.restart_server('dynamic_tool_server.py')
                result = "Server s dynamickými nástroji byl restartován. Nové nástroje by nyní měly být k dispozici."
            else:
                result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            # --- Nová logika pro zpracování TUI nástrojů ---
            try:
                data = json.loads(result)
                if isinstance(data, dict) and 'display' in data:
                    content = data.get('content')
                    display_type = data['display']
                    # Orchestrator přímo posílá ChatMessage, RichPrinter se už nepoužívá pro zobrazování.
                    RichPrinter._post(ChatMessage(content, owner='agent', msg_type=display_type))
                    result = "OK. Zpráva zobrazena uživateli."
            except (json.JSONDecodeError, TypeError):
                # Není to JSON pro TUI, zpracuje se jako normální výstup
                pass
            # --- Konec nové logiky ---

            if tool_name in TERMINAL_TOOLS:
                RichPrinter.info(f"Terminální nástroj '{tool_name}' byl použit. Úkol se automaticky ukončuje.")
                task_was_completed_by_agent = True

            output_for_display, output_for_history = self._handle_long_output(result)

            RichPrinter.info("<<< VÝSLEDEK")
            RichPrinter.log_communication("Výsledek nástroje", output_for_history, style="cyan")
            RichPrinter._post(ChatMessage(output_for_display, owner='agent', msg_type='tool_output'))

            self.history.append((history_entry_request, output_for_history))
            self.memory_manager.save_history(session_id, self.history)
            ltm_entry = f"Krok {i+1}:\nMyšlenkový pochod a akce:\n{history_entry_request}\n\nVýsledek:\n{output_for_history}"
            self.ltm.add_memory(ltm_entry, metadata={"session_id": session_id, "iteration": i + 1})

            if task_was_completed_by_agent:
                break

        if not task_was_completed_by_agent:
            final_message = f"Agent dosáhl maximálního počtu iterací ({self.max_iterations}). Úkol byl ukončen."
            RichPrinter.warning(final_message)
            summary = f"Úkol byl automaticky ukončen po dosažení limitu {self.max_iterations} iterací."
            self.memory_manager.save_session(session_id, initial_task, summary)
            RichPrinter.info(f"Vzpomínka pro session {session_id} byla uložena s poznámkou o přerušení.")
        else:
            final_message = "Agent dokončil úkol."

        RichPrinter.info(f"### {final_message} (Celkem spotřebováno: {self.total_tokens} tokenů)")

    def _parse_llm_response(self, response_text: str) -> tuple[str, dict | None]:
        """
        Parsuje JSON odpověď od LLM.
        Očekává, že odpověď je validní JSON díky vynucenému režimu.
        Zvládá i případy, kdy je JSON zabalen v Markdown bloku.
        Vrací (explanation, tool_call_data).
        """
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()

        try:
            parsed_response = json.loads(cleaned_text)
            explanation = parsed_response.get("explanation", "").strip()
            tool_call_data = parsed_response.get("tool_call")
            return explanation, tool_call_data
        except json.JSONDecodeError as e:
            error_title = "Selhání parsování JSON odpovědi"
            error_content = (
                "Odpověď od LLM se nepodařilo zpracovat jako validní JSON, "
                "i když byl vynucen JSON režim. To může indikovat problém s modelem nebo s promptem.\n\n"
                f"**Přijatá odpověď (po čištění, prvních 500 znaků):**\n"
                f"```\n{cleaned_text[:500]}\n```"
            )
            RichPrinter.log_error_panel(error_title, error_content, exception=e)

            # Vytvoříme vysvětlení pro historii, aby bylo jasné, co se stalo
            explanation = f"[SYSTÉM]: CHYBA PARSOVÁNÍ JSON. Podrobnosti byly zaznamenány do chybových logů."
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
