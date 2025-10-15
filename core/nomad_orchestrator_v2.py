"""
Nomad Orchestrator V2 - Stavově řízený orchestrátor.

Integruje všech 5 komponent:
- StateManager: Stavový stroj
- RecoveryManager: Crash recovery
- PlanManager: Plánování
- ReflectionEngine: Adaptivní učení
- BudgetTracker: Token/time tracking
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import time
import json
import re

from core.state_manager import StateManager, State
from core.recovery_manager import RecoveryManager
from core.plan_manager import PlanManager
from core.reflection_engine import ReflectionEngine
from core.budget_tracker import BudgetTracker
from core.llm_manager import LLMManager
from core.mcp_client import MCPClient
from core.rich_printer import RichPrinter


class NomadOrchestratorV2:
    """
    Nový orchestrátor s explicitním stavovým strojem.
    
    ARCHITECTURE:
    - State machine driven (IDLE → PLANNING → EXECUTING → ... → COMPLETED)
    - Crash recovery via StateManager persistence
    - Adaptive learning via ReflectionEngine
    - Budget-aware execution via BudgetTracker
    - Proactive planning via PlanManager
    """
    
    def __init__(
        self,
        project_root: str = ".",
        session_id: Optional[str] = None,
        max_tokens: int = 100000,
        max_time_seconds: int = 3600,
        max_step_retries: int = 3
    ):
        """
        Inicializuje NomadOrchestratorV2.
        
        Args:
            project_root: Cesta k projektu
            session_id: ID session (None = nová session)
            max_tokens: Maximum tokenů pro misi
            max_time_seconds: Maximum času (sekundy)
            max_step_retries: Maximum pokusů per step
        """
        self.project_root = project_root
        self.max_step_retries = max_step_retries
        
        # Komponenty
        self.state_manager = StateManager(project_root, session_id)
        self.recovery_manager = RecoveryManager(project_root)
        self.llm_manager = LLMManager(project_root)
        self.plan_manager = PlanManager(self.llm_manager, project_root)
        self.reflection_engine = ReflectionEngine(self.llm_manager)
        self.budget_tracker = BudgetTracker(
            max_tokens=max_tokens,
            max_time_seconds=max_time_seconds
        )
        self.mcp_client = MCPClient(project_root)
    
    async def initialize(self) -> None:
        """Inicializace všech komponent."""
        await self.mcp_client.start_servers()
        RichPrinter.info("✅ NomadOrchestratorV2 inicializován")
    
    async def start_mission(
        self,
        mission_goal: str,
        recover_if_crashed: bool = True
    ) -> None:
        """
        Hlavní vstupní bod - zahájí misi.
        
        Args:
            mission_goal: Cíl mise
            recover_if_crashed: Pokud True, pokusí se recover crashed sessions
        """
        RichPrinter.info(f"🚀 Starting mission: {mission_goal}")
        
        # Krok 1: Zkontroluj crashed sessions
        if recover_if_crashed:
            crashed = self.recovery_manager.find_crashed_sessions()
            if crashed:
                RichPrinter.warning(f"🔧 Nalezena {len(crashed)} nedokončená sezení")
                # Pro jednoduchost vezmeme první (v reálu by se zeptal uživatele)
                recovered_sm = self.recovery_manager.recover_session(crashed[0])
                if recovered_sm:
                    self.state_manager = recovered_sm
                    RichPrinter.info(f"♻️  Pokračuji v session {crashed[0]}")
                    # Pokračuj v misi
                    await self._run_state_machine()
                    return
        
        # Krok 2: Nová mise
        self.state_manager.set_data("mission_goal", mission_goal)
        self.state_manager.set_data("mission_start_time", datetime.now().isoformat())
        self.state_manager.transition_to(State.PLANNING, "Nová mise")
        
        # Krok 3: Spusť stavový stroj
        await self._run_state_machine()
    
    async def _run_state_machine(self) -> None:
        """
        Hlavní smyčka stavového stroje.
        
        Loop:
        1. Získej current state
        2. Zavolej handler pro ten stav
        3. Handler provede transition do dalšího stavu
        4. Opakuj, dokud není COMPLETED nebo IDLE
        """
        RichPrinter.info("🚀 Spouštím stavový stroj...")
        
        iteration = 0
        max_iterations = 100  # Ochrana před infinite loop
        
        while self.state_manager.get_state() not in [State.COMPLETED, State.IDLE]:
            current_state = self.state_manager.get_state()
            
            RichPrinter.info(f"📍 Stav: {current_state.value} (iterace {iteration})")
            
            # Dispatch podle stavu
            state_handlers = {
                State.PLANNING: self._state_planning,
                State.EXECUTING_STEP: self._state_executing_step,
                State.AWAITING_TOOL_RESULT: self._state_awaiting_tool_result,
                State.REFLECTION: self._state_reflection,
                State.RESPONDING: self._state_responding,
                State.ERROR: self._state_error,
            }
            
            handler = state_handlers.get(current_state)
            if handler:
                try:
                    await handler()
                except Exception as e:
                    RichPrinter.error(f"💥 Exception v handleru {current_state.value}: {e}")
                    self.state_manager.set_data("error_message", str(e))
                    self.state_manager.transition_to(State.ERROR, f"Handler exception: {e}")
            else:
                RichPrinter.error(f"❌ Neznámý stav: {current_state}")
                self.state_manager.transition_to(State.ERROR, "Unknown state")
                break
            
            iteration += 1
            if iteration >= max_iterations:
                RichPrinter.error("❌ Překročen max počet iterací!")
                self.state_manager.transition_to(State.ERROR, "Max iterations")
                break
            
            # Krátká pauza mezi stavy (pro debugging a clean logs)
            await asyncio.sleep(0.1)
        
        final_state = self.state_manager.get_state()
        RichPrinter.info(f"🏁 Mise ukončena ve stavu: {final_state.value}")
        
        # Budget summary
        RichPrinter.info(self.budget_tracker.get_summary())
    
    # ==================== STATE HANDLERS ====================
    
    async def _state_planning(self) -> None:
        """
        STAV: PLANNING - Vytváření plánu mise.
        
        Actions:
        1. Získej mission_goal
        2. Vytvoř plán pomocí PlanManager
        3. Ulož plán do state
        4. Transition → EXECUTING_STEP
        """
        mission_goal = self.state_manager.get_data("mission_goal")
        RichPrinter.info(f"📋 Vytvářím plán pro: {mission_goal}")
        
        try:
            # Vytvoř plán
            plan = await self.plan_manager.create_plan(mission_goal)
            
            RichPrinter.info(f"✅ Plán vytvořen: {len(plan)} kroků")
            
            # Uložení plánu do state (pro crash recovery)
            self.state_manager.set_data("plan", self.plan_manager.serialize())
            
            # Přechod na exekuci
            self.state_manager.transition_to(State.EXECUTING_STEP, "Plán vytvořen")
            
        except Exception as e:
            RichPrinter.error(f"❌ Chyba při plánování: {e}")
            self.state_manager.set_data("error_message", f"Planning failed: {e}")
            self.state_manager.transition_to(State.ERROR, "Planning error")
    
    async def _state_executing_step(self) -> None:
        """
        STAV: EXECUTING_STEP - Provádění kroku plánu.
        
        Actions:
        1. Získej další pending step (s respektem k dependencies)
        2. Zkontroluj budget
        3. Vytvoř prompt pro LLM
        4. Zavolej LLM
        5. Parse tool_call z odpovědi
        6. Transition → AWAITING_TOOL_RESULT
        """
        start_time = time.time()
        
        # Získej další krok
        next_step = self.plan_manager.get_next_step()
        
        if not next_step:
            # Žádný další krok
            if self.plan_manager.is_plan_complete():
                # Plán dokončen → přejdi na odpověď
                RichPrinter.info("✅ Všechny kroky dokončeny!")
                self.state_manager.transition_to(State.RESPONDING, "Plán dokončen")
                return
            else:
                # Jsou kroky, ale všechny mají nesplněné závislosti → deadlock
                RichPrinter.error("❌ Deadlock v závislostech plánu")
                self.state_manager.set_data("error_message", "Deadlock v závislostech plánu")
                self.state_manager.transition_to(State.ERROR, "Deadlock")
                return
        
        RichPrinter.info(f"🔨 Krok {next_step.id}: {next_step.description}")
        
        # Zkontroluj budget
        budget_check = self.budget_tracker.check_budget(next_step.estimated_tokens)
        if not budget_check["can_proceed"]:
            RichPrinter.error("❌ Nedostatek rozpočtu!")
            warning = budget_check.get("warning")
            error_msg = warning.message if warning else "Budget exceeded"
            self.state_manager.set_data("error_message", error_msg)
            self.state_manager.transition_to(State.ERROR, "Budget exceeded")
            return
        
        # Budget warning (ale můžeme pokračovat)
        if budget_check.get("warning"):
            RichPrinter.warning(budget_check["warning"].message)
        
        # Označ krok jako probíhající
        self.plan_manager.mark_step_in_progress(next_step.id)
        
        # Vytvoř prompt pro LLM
        prompt = self._build_step_prompt(next_step)
        
        # Zavolaj LLM
        try:
            model = self.llm_manager.get_llm("powerful")
            response, usage = await model.generate_content_async(prompt)
            
            # Zaznamenej náklady
            tokens_used = usage.get("usage", {}).get("total_tokens", 0) if usage else 0
            elapsed = time.time() - start_time
            self.budget_tracker.record_step_cost(
                next_step.id,
                tokens_used,
                elapsed,
                next_step.description
            )
            
            # Parse odpověď LLM (očekáváme tool_call)
            tool_call = self._parse_tool_call(response)
            
            if not tool_call:
                # LLM nechtěl volat nástroj → možná to je odpověď
                RichPrinter.warning("⚠️  LLM nevygeneroval tool call, přecházím na reflexi")
                self.state_manager.set_data("error_message", "LLM nevygeneroval tool call")
                self.state_manager.set_data("current_step_id", next_step.id)
                self.state_manager.transition_to(State.REFLECTION, "Missing tool call")
                return
            
            # Ulož pending tool call do stavu (pro recovery)
            self.state_manager.set_data("pending_tool_call", tool_call)
            self.state_manager.set_data("current_step_id", next_step.id)
            
            RichPrinter.info(f"🔧 Tool call: {tool_call['tool_name']}")
            
            # Přechod na čekání na výsledek
            self.state_manager.transition_to(State.AWAITING_TOOL_RESULT, "Tool call prepared")
            
        except Exception as e:
            RichPrinter.error(f"❌ Chyba při volání LLM: {e}")
            self.state_manager.set_data("error_message", f"LLM error: {e}")
            self.state_manager.set_data("current_step_id", next_step.id)
            self.state_manager.transition_to(State.REFLECTION, "LLM error")
    
    async def _state_awaiting_tool_result(self) -> None:
        """
        STAV: AWAITING_TOOL_RESULT - Čekání na výsledek nástroje.
        
        Actions:
        1. Získej pending_tool_call ze state
        2. Proveď tool call přes MCP
        3. Pokud úspěch: mark_step_completed, reflect_on_success, → EXECUTING_STEP
        4. Pokud chyba: mark_step_failed, → REFLECTION
        """
        tool_call = self.state_manager.get_data("pending_tool_call")
        step_id = self.state_manager.get_data("current_step_id")
        
        if not tool_call:
            RichPrinter.error("❌ Chybí pending_tool_call!")
            self.state_manager.transition_to(State.ERROR, "Missing tool_call")
            return
        
        # Proveď tool call
        try:
            RichPrinter.info(f"⚙️  Provádím: {tool_call['tool_name']}...")
            
            result = await self.mcp_client.execute_tool(
                tool_call["tool_name"],
                tool_call.get("args", []),
                tool_call.get("kwargs", {}),
                verbose=True
            )
            
            # Úspěch
            RichPrinter.info(f"✅ Tool úspěšný: {tool_call['tool_name']}")
            self.plan_manager.mark_step_completed(step_id, str(result), tokens_used=0)
            
            # Reflexe úspěchu (pro učení)
            step = self.plan_manager._get_step_by_id(step_id)
            if step:
                await self.reflection_engine.reflect_on_success(step.to_dict())
            
            # Vyčisti pending data
            self.state_manager.set_data("pending_tool_call", None)
            self.state_manager.set_data("current_step_id", None)
            
            # Přechod zpět na exekuci dalšího kroku
            self.state_manager.transition_to(State.EXECUTING_STEP, "Tool succeeded")
            
        except Exception as e:
            # Selhání nástroje
            error_msg = str(e)
            RichPrinter.error(f"❌ Tool selhal: {error_msg}")
            
            self.plan_manager.mark_step_failed(step_id, error_msg)
            
            # Přechod na reflexi
            self.state_manager.set_data("error_message", error_msg)
            self.state_manager.transition_to(State.REFLECTION, "Tool failed")
    
    async def _state_reflection(self) -> None:
        """
        STAV: REFLECTION - Reflexe po chybě.
        
        Actions:
        1. Získej failed step a error
        2. Zavolej ReflectionEngine
        3. Rozhodnutí podle suggested_action:
           - retry → EXECUTING_STEP (reset step na pending)
           - replanning → PLANNING
           - ask_user → RESPONDING
           - skip_step → EXECUTING_STEP (mark jako skipped)
           - jinak → ERROR
        """
        error_msg = self.state_manager.get_data("error_message", "Unknown error")
        step_id = self.state_manager.get_data("current_step_id")
        
        if not step_id:
            # Chyba mimo kontext kroku
            RichPrinter.error("❌ Kritická chyba mimo kontext kroku")
            self.state_manager.transition_to(State.ERROR, "Unrecoverable")
            return
        
        failed_step = self.plan_manager._get_step_by_id(step_id)
        if not failed_step:
            RichPrinter.error(f"❌ Krok {step_id} nenalezen")
            self.state_manager.transition_to(State.ERROR, "Step not found")
            return
        
        # Kolikátý pokus?
        attempt = self.state_manager.get_data(f"step_{step_id}_attempts", 0) + 1
        self.state_manager.set_data(f"step_{step_id}_attempts", attempt)
        
        RichPrinter.warning(f"🤔 Reflexe selhání (pokus {attempt}/{self.max_step_retries})...")
        
        # Reflexe
        reflection = await self.reflection_engine.reflect_on_failure(
            failed_step=failed_step.to_dict(),
            error_message=error_msg,
            attempt_count=attempt,
            plan_context=str([s.to_dict() for s in self.plan_manager.steps])
        )
        
        RichPrinter.info(f"💡 Doporučení: {reflection.suggested_action}")
        RichPrinter.info(f"   Analýza: {reflection.analysis[:100]}...")
        
        # Rozhodnutí podle doporučení
        if reflection.suggested_action == "retry" and attempt < self.max_step_retries:
            RichPrinter.info("🔄 Zkouším krok znovu...")
            failed_step.status = "pending"  # Reset na pending
            failed_step.error = None
            # Vyčisti pending data
            self.state_manager.set_data("pending_tool_call", None)
            self.state_manager.set_data("error_message", None)
            self.state_manager.transition_to(State.EXECUTING_STEP, "Retrying step")
        
        elif reflection.suggested_action == "retry_modified" and attempt < self.max_step_retries:
            RichPrinter.info(f"🔄 Zkouším s modifikací: {reflection.modification_hint}")
            # TODO: Aplikovat modification_hint do step description
            failed_step.status = "pending"
            failed_step.error = None
            if reflection.modification_hint:
                failed_step.description += f"\n\nMODIFIKACE: {reflection.modification_hint}"
            self.state_manager.set_data("pending_tool_call", None)
            self.state_manager.set_data("error_message", None)
            self.state_manager.transition_to(State.EXECUTING_STEP, "Retrying modified")
        
        elif reflection.suggested_action == "replanning":
            RichPrinter.warning("📋 Přeplánovávám celou misi...")
            # Reset plánu
            self.plan_manager.steps.clear()
            self.state_manager.set_data("plan", None)
            self.state_manager.transition_to(State.PLANNING, "Replanning")
        
        elif reflection.suggested_action == "ask_user":
            RichPrinter.warning("❓ Potřebuji pomoc uživatele")
            self.state_manager.set_data("user_question", reflection.analysis)
            self.state_manager.transition_to(State.RESPONDING, "Asking user")
        
        elif reflection.suggested_action == "skip_step":
            RichPrinter.info("⏭️  Přeskakuji krok")
            failed_step.status = "skipped"
            self.state_manager.set_data("pending_tool_call", None)
            self.state_manager.set_data("current_step_id", None)
            self.state_manager.transition_to(State.EXECUTING_STEP, "Step skipped")
        
        else:
            # Vyčerpány pokusy nebo unknown action → ERROR
            RichPrinter.error(f"❌ Krok selhal po {attempt} pokusech")
            self.state_manager.transition_to(State.ERROR, "Max retries exceeded")
    
    async def _state_responding(self) -> None:
        """
        STAV: RESPONDING - Generování finální odpovědi uživateli.
        
        Actions:
        1. Získej progress z PlanManager
        2. Vygeneruj shrnutí pomocí LLM
        3. Zobraz uživateli
        4. Transition → COMPLETED
        """
        progress = self.plan_manager.get_progress()
        
        RichPrinter.info(f"📊 Pokrok: {progress['progress_percent']:.0f}% dokončeno")
        
        # Check zda se ptáme uživatele
        user_question = self.state_manager.get_data("user_question")
        if user_question:
            RichPrinter.warning(f"❓ Otázka pro uživatele:\n{user_question}")
            # V reálu by zde byl interaktivní input
            # Pro testy jen přejdeme do COMPLETED
        
        # Vygeneruj shrnutí
        mission_goal = self.state_manager.get_data("mission_goal")
        summary_prompt = f"""Úkol: {mission_goal}

Plán byl dokončen. Shrň výsledky.

STATISTIKY:
- Dokončeno kroků: {progress['completed']}/{progress['total_steps']}
- Selhalo: {progress['failed']}
- Přeskočeno: {progress.get('skipped', 0)}

Vytvoř stručné shrnutí pro uživatele (max 3 věty).
"""
        
        try:
            model = self.llm_manager.get_llm("economical")
            summary, _ = await model.generate_content_async(summary_prompt)
            
            RichPrinter.show_task_complete(summary)
        except Exception as e:
            RichPrinter.warning(f"⚠️  Chyba při generování shrnutí: {e}")
            RichPrinter.show_task_complete(f"Mise dokončena s {progress['completed']} úspěšnými kroky.")
        
        # Přechod na COMPLETED
        self.state_manager.transition_to(State.COMPLETED, "Mission accomplished")
    
    async def _state_error(self) -> None:
        """
        STAV: ERROR - Kritická chyba.
        
        Actions:
        1. Zobraz error message
        2. Transition → IDLE (mise ukončena)
        """
        error_msg = self.state_manager.get_data("error_message", "Unknown error")
        RichPrinter.error(f"💥 Kritická chyba: {error_msg}")
        
        # Budget summary i při chybě
        RichPrinter.info(self.budget_tracker.get_summary())
        
        # Přechod do IDLE (mise ukončena)
        self.state_manager.transition_to(State.IDLE, "Error recovery")
    
    # ==================== HELPER METHODS ====================
    
    def _build_step_prompt(self, step) -> str:
        """
        Sestaví prompt pro provedení kroku.
        
        Args:
            step: PlanStep objekt
        
        Returns:
            Prompt string pro LLM
        """
        return f"""Jsi Nomád - autonomní AI agent.

AKTUÁLNÍ KROK:
{step.description}

INSTRUKCE:
1. Analyzuj, jaký nástroj potřebuješ použít
2. Zavolej příslušný nástroj
3. Použij formát:

TOOL_CALL:
{{
  "tool_name": "název_nástroje",
  "args": [],
  "kwargs": {{"param": "value"}}
}}

DOSTUPNÉ NÁSTROJE:
- read_file(filepath: str)
- create_file_with_block(filepath: str, content: str)
- list_files(path: str)
- run_in_bash_session(command: str)

Zavolej nástroj pro splnění tohoto kroku."""
    
    def _parse_tool_call(self, llm_response: str) -> Optional[Dict[str, Any]]:
        """
        Parsuje tool call z LLM odpovědi.
        
        Args:
            llm_response: Odpověď z LLM
        
        Returns:
            Dict s tool_name, args, kwargs nebo None
        """
        try:
            # Pomocná funkce pro extractování kompletního JSON objektu
            def extract_json_object(text: str, start_pos: int = 0) -> Optional[str]:
                """Extrahuje kompletní JSON object včetně nested objektů."""
                brace_start = text.find('{', start_pos)
                if brace_start == -1:
                    return None
                
                brace_count = 0
                for i in range(brace_start, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return text[brace_start:i+1]
                return None
            
            # Pattern 1: Explicit TOOL_CALL: {...}
            if 'TOOL_CALL:' in llm_response:
                pos = llm_response.find('TOOL_CALL:')
                json_str = extract_json_object(llm_response, pos)
                if json_str:
                    data = json.loads(json_str)
                    if "tool_name" in data:
                        return data
            
            # Pattern 2: Markdown code block
            match = re.search(r'```(?:json)?\s*\n(.*?)\n```', llm_response, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                data = json.loads(json_str)
                if "tool_name" in data:
                    return data
            
            # Pattern 3: Any JSON with tool_name
            json_str = extract_json_object(llm_response)
            if json_str:
                data = json.loads(json_str)
                if "tool_name" in data:
                    return data
            
            return None
            
        except (json.JSONDecodeError, ValueError) as e:
            RichPrinter.warning(f"⚠️  Nepodařilo se zparsovat tool call: {e}")
            return None
            match = re.search(r'```(?:json)?\s*(\{[\s\S]*?"tool_name"[\s\S]*?\})\s*```', llm_response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            return None
            
        except (json.JSONDecodeError, AttributeError) as e:
            RichPrinter.warning(f"⚠️  Chyba při parsování tool call: {e}")
            return None
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.mcp_client.shutdown()
        RichPrinter.info("👋 NomadOrchestratorV2 ukončen")
