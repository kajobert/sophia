"""
State Manager - Jádro stavového stroje Nomáda.

Tento modul implementuje explicitní stavový stroj s validací přechodů
a automatickou persistence do souboru.

ARCHITEKTURA:
- 8 stavů (IDLE, PLANNING, EXECUTING_STEP, atd.)
- Validace každého přechodu podle VALID_TRANSITIONS
- Automatické ukládání po každé změně
- Historie všech přechodů pro debugging

POUŽITÍ:
    sm = StateManager(project_root=".", session_id="my_session")
    sm.transition_to(State.PLANNING, "Starting new mission")
    sm.set_data("mission_goal", "Fix bug in orchestrator")
    sm.persist()

THREAD SAFETY: Není thread-safe! Pro multi-threaded použití přidej Lock.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime


class State(Enum):
    """
    Všechny možné stavy orchestrátora.
    
    POZOR: Při přidávání nového stavu MUSÍŠ aktualizovat VALID_TRANSITIONS!
    """
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING_STEP = "executing_step"
    AWAITING_TOOL_RESULT = "awaiting_tool"
    REFLECTION = "reflection"
    RESPONDING = "responding"
    COMPLETED = "completed"
    ERROR = "error"


class StateTransitionError(Exception):
    """
    Vyhozena při pokusu o neplatný přechod mezi stavy.
    
    Toto je CRITICAL exception - pokud se vyhodí, znamená to BUG v orchestrátoru!
    """
    pass


class StateManager:
    """
    Spravuje stav orchestrátora s validací přechodů a persistence.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Každý přechod je validován proti VALID_TRANSITIONS
    - Stav je automaticky persistován po každém přechodu
    - Session ID je buď zadané nebo auto-generované
    
    THREAD SAFETY: Tato třída NENÍ thread-safe!
    """
    
    # Povolené přechody mezi stavy
    # Formát: {current_state: [allowed_next_states]}
    VALID_TRANSITIONS: Dict[State, List[State]] = {
        State.IDLE: [State.PLANNING],
        State.PLANNING: [State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.EXECUTING_STEP: [State.AWAITING_TOOL_RESULT, State.REFLECTION, State.RESPONDING, State.ERROR],
        State.AWAITING_TOOL_RESULT: [State.REFLECTION, State.EXECUTING_STEP, State.ERROR],
        State.REFLECTION: [State.PLANNING, State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.RESPONDING: [State.COMPLETED, State.EXECUTING_STEP, State.PLANNING],
        State.COMPLETED: [State.IDLE],
        State.ERROR: [State.IDLE, State.REFLECTION],
    }
    
    def __init__(self, project_root: str = ".", session_id: Optional[str] = None):
        """
        Inicializace StateManager.
        
        Args:
            project_root: Kořenový adresář projektu
            session_id: ID sezení (pokud None, vygeneruje se automaticky)
        """
        self.project_root = project_root
        self.session_id = session_id or self._generate_session_id()
        self.current_state = State.IDLE
        self.state_data: Dict[str, Any] = {}
        self.state_history: List[Dict[str, Any]] = []
        
        # Cesta k session souboru
        self.session_file = os.path.join(
            project_root, "memory", f"session_{self.session_id}.json"
        )
    
    def _generate_session_id(self) -> str:
        """
        Generuje unikátní ID sezení.
        
        Formát: YYYYMMDD_HHMMSS (např. 20251012_143022)
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def transition_to(self, new_state: State, reason: str = "") -> bool:
        """
        Pokusí se přejít do nového stavu.
        
        Args:
            new_state: Cílový stav
            reason: Důvod přechodu (pro debugging)
        
        Returns:
            True pokud přechod úspěšný
        
        Raises:
            StateTransitionError: Pokud přechod není povolen
        """
        # Validace přechodu
        allowed_states = self.VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed_states:
            raise StateTransitionError(
                f"Nelze přejít z {self.current_state.value} do {new_state.value}. "
                f"Povolené přechody: {[s.value for s in allowed_states]}"
            )
        
        # Zaznamenej přechod do historie
        transition_record = {
            "from": self.current_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.state_history.append(transition_record)
        
        # Provedení přechodu
        old_state = self.current_state
        self.current_state = new_state
        
        # Automatická persistence
        self.persist()
        
        # Debug výstup
        print(f"🔄 State: {old_state.value} → {new_state.value} ({reason})")
        
        return True
    
    def get_state(self) -> State:
        """Vrátí aktuální stav."""
        return self.current_state
    
    def set_data(self, key: str, value: Any):
        """
        Uloží data asociovaná se stavem.
        
        Args:
            key: Klíč pro uložení dat
            value: Hodnota (musí být JSON serializable)
        """
        self.state_data[key] = value
        self.persist()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Načte data asociovaná se stavem.
        
        Args:
            key: Klíč dat
            default: Výchozí hodnota pokud klíč neexistuje
        
        Returns:
            Uložená data nebo default
        """
        return self.state_data.get(key, default)
    
    def persist(self):
        """
        Uloží kompletní stav do JSON souboru.
        
        Soubor: memory/session_{session_id}.json
        
        Formát:
        {
            "session_id": "20251012_143022",
            "current_state": "executing_step",
            "state_data": {...},
            "state_history": [...],
            "last_updated": "2025-10-12T14:30:22.123456"
        }
        """
        # Vytvoř memory adresář pokud neexistuje
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        
        # Sestavení snapshot
        state_snapshot = {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "state_data": self.state_data,
            "state_history": self.state_history,
            "last_updated": datetime.now().isoformat()
        }
        
        # Zápis do souboru
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(state_snapshot, f, indent=2, ensure_ascii=False)
    
    def restore(self) -> bool:
        """
        Obnoví stav ze souboru.
        
        Returns:
            True pokud úspěšné, False pokud soubor neexistuje
        """
        if not os.path.exists(self.session_file):
            return False
        
        # Načti snapshot
        with open(self.session_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Obnov data
        self.session_id = snapshot["session_id"]
        self.current_state = State(snapshot["current_state"])
        self.state_data = snapshot["state_data"]
        self.state_history = snapshot["state_history"]
        
        print(f"✅ Stav obnoven: {self.current_state.value} (session: {self.session_id})")
        return True
    
    def reset(self):
        """
        Resetuje stav na IDLE (pro novou misi).
        
        POZOR: Toto NESMAŽE session file! Jen resetuje in-memory stav.
        """
        self.current_state = State.IDLE
        self.state_data = {}
        self.state_history = []
        self.persist()
    
    def get_transition_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vrátí posledních N přechodů.
        
        Args:
            limit: Počet přechodů k vrácení
        
        Returns:
            Seznam transition records
        """
        return self.state_history[-limit:]
    
    def __repr__(self) -> str:
        """String reprezentace pro debugging."""
        return (
            f"StateManager(session={self.session_id}, "
            f"state={self.current_state.value}, "
            f"transitions={len(self.state_history)})"
        )
