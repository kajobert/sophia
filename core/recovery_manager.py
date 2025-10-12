"""
Recovery Manager - Automatické obnovení po pádu Nomáda.

Tento modul detekuje nedokončená sezení a pokouší se je obnovit
s použitím inteligentních recovery strategií.

ARCHITEKTURA:
- Detekce crashed sessions (jakýkoli stav != IDLE, COMPLETED)
- Recovery strategie pro každý stav
- Bezpečné obnovení s validací

POUŽITÍ:
    rm = RecoveryManager(project_root=".")
    
    # Najdi crashed sessions
    crashed = rm.find_crashed_sessions()
    
    # Obnov první
    if crashed:
        sm = rm.recover_session(crashed[0])
        # sm je nyní obnovený StateManager, připravený pokračovat

RECOVERY STRATEGIE:
- PLANNING: Restart plánování od začátku
- EXECUTING_STEP: Zkus krok znovu nebo přejdi na reflexi
- AWAITING_TOOL: Předpokládej selhání nástroje → reflexe
- REFLECTION: Pokračuj v reflexi (bezpečný stav)
- ERROR: Přejdi do reflexe k analýze chyby
"""

import os
from typing import Optional, List
from core.state_manager import StateManager, State
from core.rich_printer import RichPrinter


class RecoveryManager:
    """
    Spravuje obnovu po pádu orchestrátoru.
    
    BEZPEČNOSTNÍ POZNÁMKY:
    - Recovery NIKDY nesmaže session data
    - Pokud recovery selže, session zůstává nedotčená
    - Všechny recovery akce jsou logovány
    """
    
    def __init__(self, project_root: str = "."):
        """
        Inicializace RecoveryManager.
        
        Args:
            project_root: Kořenový adresář projektu
        """
        self.project_root = project_root
        self.memory_dir = os.path.join(project_root, "memory")
    
    def find_crashed_sessions(self) -> List[str]:
        """
        Najde session soubory, které nebyly dokončeny.
        
        Crashed session = jakýkoli stav kromě IDLE nebo COMPLETED
        
        Returns:
            Seznam session_id, které jsou v mid-flight
        """
        crashed = []
        
        # Zkontroluj zda memory adresář existuje
        if not os.path.exists(self.memory_dir):
            return crashed
        
        # Projdi všechny session soubory
        for filename in os.listdir(self.memory_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                # Extrahuj session_id z názvu souboru
                # Formát: session_20251012_143022.json → 20251012_143022
                session_id = filename.replace("session_", "").replace(".json", "")
                
                # Načti state
                sm = StateManager(self.project_root, session_id)
                
                if sm.restore():
                    state = sm.get_state()
                    
                    # Jakýkoli stav kromě IDLE, COMPLETED je považován za crashed
                    if state not in [State.IDLE, State.COMPLETED]:
                        crashed.append(session_id)
                        RichPrinter.warning(
                            f"🔧 Nalezena crashed session: {session_id} "
                            f"(stav: {state.value})"
                        )
        
        return crashed
    
    def recover_session(self, session_id: str) -> Optional[StateManager]:
        """
        Pokusí se obnovit spadnuté sezení.
        
        Args:
            session_id: ID sezení k obnovení
        
        Returns:
            StateManager s obnoveným stavem, nebo None pokud recovery nelze
        """
        RichPrinter.info(f"🔧 Zahajuji recovery session: {session_id}")
        
        # Načti state manager
        sm = StateManager(self.project_root, session_id)
        
        if not sm.restore():
            RichPrinter.error(
                f"❌ Nelze obnovit session {session_id} - soubor nenalezen"
            )
            return None
        
        current_state = sm.get_state()
        
        # Zobraz info o crashed session
        RichPrinter.warning(f"   Poslední stav: {current_state.value}")
        RichPrinter.info(f"   Historie přechodů: {len(sm.state_history)}")
        
        # Zobraz poslední 3 přechody pro kontext
        recent_transitions = sm.get_transition_history(limit=3)
        if recent_transitions:
            RichPrinter.info("   Poslední přechody:")
            for t in recent_transitions:
                RichPrinter.info(
                    f"      {t['from']} → {t['to']} ({t['reason']})"
                )
        
        # Strategie recovery podle stavu
        recovery_strategies = {
            State.PLANNING: self._recover_from_planning,
            State.EXECUTING_STEP: self._recover_from_executing,
            State.AWAITING_TOOL_RESULT: self._recover_from_awaiting_tool,
            State.REFLECTION: self._recover_from_reflection,
            State.ERROR: self._recover_from_error,
            State.RESPONDING: self._recover_from_responding,
        }
        
        strategy = recovery_strategies.get(current_state)
        if strategy:
            try:
                strategy(sm)
                RichPrinter.info(f"✅ Recovery úspěšný - stav: {sm.get_state().value}")
            except Exception as e:
                RichPrinter.error(f"❌ Recovery selhal: {e}")
                return None
        else:
            RichPrinter.warning(
                f"⚠️  Žádná recovery strategie pro stav: {current_state.value}"
            )
        
        return sm
    
    def _recover_from_planning(self, sm: StateManager):
        """
        Recovery když spadl během plánování.
        
        Strategie: Restart plánování od začátku (plán může být nekonzistentní)
        """
        RichPrinter.info("♻️  Recovery strategie: Restart plánování")
        
        # Smaž částečný plán (pokud existuje)
        sm.set_data("plan", None)
        
        # NELZE přejít přímo z PLANNING do IDLE (není v VALID_TRANSITIONS)
        # Místo toho přejdeme přes ERROR
        sm.current_state = State.ERROR  # Force set (recovery exception)
        sm.transition_to(State.IDLE, "Recovery: reset after planning crash")
        sm.transition_to(State.PLANNING, "Recovery: restarting planning")
    
    def _recover_from_executing(self, sm: StateManager):
        """
        Recovery když spadl během provádění kroku.
        
        Strategie:
        1. Pokud byl uložen pending_tool_call → zkus znovu
        2. Jinak → přejdi na reflexi (něco se pokazilo)
        """
        RichPrinter.info("♻️  Recovery strategie: Analýza executing step")
        
        # Zkontroluj zda byl uložen pending tool call
        pending_tool = sm.get_data("pending_tool_call")
        
        if pending_tool:
            RichPrinter.info(
                f"   Nalezen nedokončený tool call: {pending_tool.get('tool_name', 'unknown')}"
            )
            # Orchestrátor se pokusí krok opakovat
            # (pending_tool_call zůstane v state_data)
            RichPrinter.info("   ℹ️  Orchestrátor může zkusit krok znovu")
        else:
            # Žádný pending tool call → něco se pokazilo před voláním
            RichPrinter.warning("   Žádný pending tool call → přecházím na reflexi")
            
            # Přejdi na AWAITING (validní transition) a pak na REFLECTION
            sm.transition_to(
                State.AWAITING_TOOL_RESULT,
                "Recovery: forcing awaiting state"
            )
            sm.transition_to(
                State.REFLECTION,
                "Recovery: analyzing execution crash"
            )
    
    def _recover_from_awaiting_tool(self, sm: StateManager):
        """
        Recovery když spadl při čekání na výsledek nástroje.
        
        Strategie: Tool pravděpodobně selhal → reflexe
        """
        RichPrinter.warning("⚠️  Recovery strategie: Tool execution interrupted")
        
        # Ulož error message
        sm.set_data(
            "error_message",
            "Tool execution was interrupted (process crashed or timeout)"
        )
        
        # Přejdi na reflexi
        sm.transition_to(
            State.REFLECTION,
            "Recovery: tool execution interrupted"
        )
    
    def _recover_from_reflection(self, sm: StateManager):
        """
        Recovery během reflexe.
        
        Strategie: Reflexe je bezpečná - můžeme pokračovat kde jsme skončili
        """
        RichPrinter.info("♻️  Recovery strategie: Pokračuj v reflexi")
        
        # Reflexe je idempotentní - není třeba nic měnit
        # Orchestrátor prostě pokračuje v reflexi
        pass
    
    def _recover_from_error(self, sm: StateManager):
        """
        Recovery z chybového stavu.
        
        Strategie: Přejdi do reflexe k analýze chyby
        """
        RichPrinter.error("❌ Recovery strategie: Analýza error state")
        
        # Zjisti error message (pokud byl uložen)
        error_msg = sm.get_data("error_message", "Unknown error (crashed)")
        RichPrinter.error(f"   Error: {error_msg}")
        
        # Přejdi na reflexi
        sm.transition_to(
            State.REFLECTION,
            "Recovery: analyzing error state"
        )
    
    def _recover_from_responding(self, sm: StateManager):
        """
        Recovery během generování odpovědi.
        
        Strategie: Zkus vygenerovat odpověď znovu
        """
        RichPrinter.info("♻️  Recovery strategie: Retry response generation")
        
        # Responding je relativně bezpečný - můžeme zkusit znovu
        # Žádná změna stavu nutná, orchestrátor prostě znovu vygeneruje odpověď
        pass
    
    def cleanup_old_sessions(self, max_age_days: int = 7):
        """
        Smaže staré session soubory.
        
        Args:
            max_age_days: Maximální stáří v dnech (default 7)
        
        BEZPEČNOST: Smazány jsou JEN dokončené sessions (IDLE, COMPLETED)
        """
        import time
        from datetime import datetime, timedelta
        
        if not os.path.exists(self.memory_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        for filename in os.listdir(self.memory_dir):
            if not filename.startswith("session_") or not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(self.memory_dir, filename)
            
            # Zkontroluj stáří souboru
            file_mtime = os.path.getmtime(filepath)
            file_date = datetime.fromtimestamp(file_mtime)
            
            if file_date < cutoff_date:
                # Načti session a zkontroluj že je dokončená
                session_id = filename.replace("session_", "").replace(".json", "")
                sm = StateManager(self.project_root, session_id)
                
                if sm.restore():
                    if sm.get_state() in [State.IDLE, State.COMPLETED]:
                        os.remove(filepath)
                        deleted_count += 1
                        RichPrinter.info(
                            f"🗑️  Smazána stará session: {session_id} "
                            f"(stáří: {(datetime.now() - file_date).days} dní)"
                        )
        
        if deleted_count > 0:
            RichPrinter.info(f"✅ Cleanup: Smazáno {deleted_count} starých sessions")
    
    def get_recovery_statistics(self) -> dict:
        """
        Vrátí statistiky o crashed sessions.
        
        Returns:
            {
                "total_sessions": int,
                "crashed_sessions": int,
                "states": {state: count}
            }
        """
        if not os.path.exists(self.memory_dir):
            return {
                "total_sessions": 0,
                "crashed_sessions": 0,
                "states": {}
            }
        
        total = 0
        crashed = 0
        state_counts = {}
        
        for filename in os.listdir(self.memory_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                total += 1
                session_id = filename.replace("session_", "").replace(".json", "")
                sm = StateManager(self.project_root, session_id)
                
                if sm.restore():
                    state = sm.get_state()
                    state_counts[state.value] = state_counts.get(state.value, 0) + 1
                    
                    if state not in [State.IDLE, State.COMPLETED]:
                        crashed += 1
        
        return {
            "total_sessions": total,
            "crashed_sessions": crashed,
            "states": state_counts
        }
