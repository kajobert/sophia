# 🛠️ Refaktoringová Roadmapa Nomáda - Verze 2.0 (FINÁLNÍ)

**Datum:** 12. října 2025  
**Autor:** Jules (Nomad) + Uživatel  
**Kontext:** Kompletní refaktoring současného JulesOrchestrator na robustní, stavově řízený systém

---

## 🎯 Executive Summary

Tato roadmapa definuje **6 kritických komponent**, které transformují současný reaktivní loop v **robustní, autonomní systém**:

1. ✅ **StateManager** - Explicitní stavový stroj s persistence
2. ✅ **PlanManager** - Proaktivní plánování místo reaktivního loopu
3. ✅ **ReflectionEngine** - Učení z chyb a adaptace strategie
4. ✅ **BudgetTracker** - Prevence vyčerpání tokenů/času
5. ✅ **RecoveryManager** - Crash-resilience a checkpoint/restore
6. ✅ **NomadOrchestratorV2** - Sjednocující orchestrátor

**Časový Odhad:** 10-12 dní  
**Přístup:** Iterativní - každá komponenta samostatně testovatelná

---

## 📊 Prioritizace Komponent

| Komponenta | Priorita | Dny | Závislosti | Kritičnost |
|------------|----------|-----|------------|------------|
| StateManager | 🔴 P0 | 2 | Žádné | BLOCKER |
| RecoveryManager | 🔴 P0 | 1 | StateManager | BLOCKER |
| PlanManager | 🟡 P1 | 2 | StateManager | VYSOKÁ |
| ReflectionEngine | 🟡 P1 | 2 | StateManager | VYSOKÁ |
| BudgetTracker | 🟢 P2 | 1 | Žádné | STŘEDNÍ |
| NomadOrchestratorV2 | 🔴 P0 | 3 | Všechny výše | BLOCKER |

---

## 🚀 FÁZE 1: StateManager + Recovery (3 dny)

### Den 1-2: StateManager

**Cíl:** Explicitní stavový stroj s validovanými přechody a persistence.

#### 1.1 Definice Stavů

```python
# core/state_manager.py

from enum import Enum
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

class State(Enum):
    """Možné stavy orchestrátora."""
    IDLE = "idle"                           # Čeká na úkol
    PLANNING = "planning"                   # Vytváří plán
    EXECUTING_STEP = "executing_step"       # Provádí krok plánu
    AWAITING_TOOL_RESULT = "awaiting_tool"  # Čeká na výsledek nástroje
    REFLECTION = "reflection"               # Analyzuje chybu/úspěch
    RESPONDING = "responding"               # Generuje odpověď uživateli
    COMPLETED = "completed"                 # Mise dokončena
    ERROR = "error"                         # Kritická chyba


class StateTransitionError(Exception):
    """Vyvolána při neplatném přechodu stavu."""
    pass


class StateManager:
    """
    Spravuje stav orchestrátora a zajišťuje platnost přechodů.
    """
    
    # Povolené přechody mezi stavy
    VALID_TRANSITIONS = {
        State.IDLE: [State.PLANNING],
        State.PLANNING: [State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.EXECUTING_STEP: [State.AWAITING_TOOL_RESULT, State.RESPONDING, State.ERROR],
        State.AWAITING_TOOL_RESULT: [State.REFLECTION, State.EXECUTING_STEP, State.ERROR],
        State.REFLECTION: [State.PLANNING, State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.RESPONDING: [State.COMPLETED, State.EXECUTING_STEP, State.PLANNING],
        State.COMPLETED: [State.IDLE],
        State.ERROR: [State.IDLE, State.REFLECTION],
    }
    
    def __init__(self, project_root: str = ".", session_id: str = None):
        self.project_root = project_root
        self.session_id = session_id or self._generate_session_id()
        self.current_state = State.IDLE
        self.state_data: Dict[str, Any] = {}
        self.state_history = []
        self.session_file = os.path.join(
            project_root, "memory", f"session_{self.session_id}.json"
        )
    
    def _generate_session_id(self) -> str:
        """Generuje unikátní ID sezení."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def transition_to(self, new_state: State, reason: str = "") -> bool:
        """
        Pokusí se přejít do nového stavu.
        
        Returns:
            True pokud přechod úspěšný, False pokud neplatný
        
        Raises:
            StateTransitionError pokud přechod zakázán
        """
        if new_state not in self.VALID_TRANSITIONS.get(self.current_state, []):
            raise StateTransitionError(
                f"Nelze přejít z {self.current_state.value} do {new_state.value}. "
                f"Povolené přechody: {[s.value for s in self.VALID_TRANSITIONS[self.current_state]]}"
            )
        
        # Zaznamenej přechod do historie
        self.state_history.append({
            "from": self.current_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        old_state = self.current_state
        self.current_state = new_state
        
        # Persist okamžitě po každém přechodu
        self.persist()
        
        print(f"🔄 State: {old_state.value} → {new_state.value} ({reason})")
        return True
    
    def get_state(self) -> State:
        """Vrátí aktuální stav."""
        return self.current_state
    
    def set_data(self, key: str, value: Any):
        """Uloží data asociovaná se stavem."""
        self.state_data[key] = value
        self.persist()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Načte data asociovaná se stavem."""
        return self.state_data.get(key, default)
    
    def persist(self):
        """Uloží kompletní stav do souboru."""
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        
        state_snapshot = {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "state_data": self.state_data,
            "state_history": self.state_history,
            "last_updated": datetime.now().isoformat()
        }
        
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
        
        with open(self.session_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        self.session_id = snapshot["session_id"]
        self.current_state = State(snapshot["current_state"])
        self.state_data = snapshot["state_data"]
        self.state_history = snapshot["state_history"]
        
        print(f"✅ Stav obnoven: {self.current_state.value}")
        return True
    
    def reset(self):
        """Resetuje stav na IDLE (pro novou misi)."""
        self.current_state = State.IDLE
        self.state_data = {}
        self.state_history = []
        self.persist()
```

#### 1.2 Testy StateManager

```python
# tests/test_state_manager.py

import pytest
from core.state_manager import StateManager, State, StateTransitionError

def test_valid_transition():
    sm = StateManager()
    assert sm.get_state() == State.IDLE
    
    sm.transition_to(State.PLANNING, "Starting mission")
    assert sm.get_state() == State.PLANNING


def test_invalid_transition():
    sm = StateManager()
    
    with pytest.raises(StateTransitionError):
        sm.transition_to(State.EXECUTING_STEP, "Invalid jump")


def test_persistence():
    sm = StateManager(session_id="test_session")
    sm.transition_to(State.PLANNING)
    sm.set_data("mission_goal", "Test úkol")
    
    # Vytvoř novou instanci a obnov
    sm2 = StateManager(session_id="test_session")
    assert sm2.restore() == True
    assert sm2.get_state() == State.PLANNING
    assert sm2.get_data("mission_goal") == "Test úkol"


def test_state_history():
    sm = StateManager()
    sm.transition_to(State.PLANNING)
    sm.transition_to(State.EXECUTING_STEP)
    
    assert len(sm.state_history) == 2
    assert sm.state_history[0]["from"] == "idle"
    assert sm.state_history[1]["to"] == "executing_step"
```

**CHECKPOINT 1:** ✅ Všechny testy v `test_state_manager.py` MUSÍ projít!

---

### Den 3: RecoveryManager

**Cíl:** Automatické obnovení po pádu.

```python
# core/recovery_manager.py

import os
from typing import Optional
from core.state_manager import StateManager, State
from core.rich_printer import RichPrinter

class RecoveryManager:
    """
    Spravuje obnovu po pádu orchestrátora.
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.memory_dir = os.path.join(project_root, "memory")
    
    def find_crashed_sessions(self) -> list[str]:
        """
        Najde session soubory, které nebyly dokončeny.
        
        Returns:
            Seznam session_id, které jsou v mid-flight
        """
        crashed = []
        
        if not os.path.exists(self.memory_dir):
            return crashed
        
        for filename in os.listdir(self.memory_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename.replace("session_", "").replace(".json", "")
                sm = StateManager(self.project_root, session_id)
                
                if sm.restore():
                    state = sm.get_state()
                    # Jakýkoli stav kromě IDLE, COMPLETED je považován za crashed
                    if state not in [State.IDLE, State.COMPLETED]:
                        crashed.append(session_id)
        
        return crashed
    
    def recover_session(self, session_id: str) -> Optional[StateManager]:
        """
        Pokusí se obnovit spadnuté sezení.
        
        Returns:
            StateManager s obnoveným stavem, nebo None pokud recovery nelze
        """
        sm = StateManager(self.project_root, session_id)
        
        if not sm.restore():
            RichPrinter.error(f"Nelze obnovit session {session_id} - soubor nenalezen")
            return None
        
        current_state = sm.get_state()
        
        RichPrinter.warning(f"🔧 Obnovuji spadnuté sezení {session_id}")
        RichPrinter.info(f"   Poslední stav: {current_state.value}")
        RichPrinter.info(f"   Historie přechodů: {len(sm.state_history)}")
        
        # Strategie recovery podle stavu
        recovery_strategies = {
            State.PLANNING: self._recover_from_planning,
            State.EXECUTING_STEP: self._recover_from_executing,
            State.AWAITING_TOOL_RESULT: self._recover_from_awaiting_tool,
            State.REFLECTION: self._recover_from_reflection,
            State.ERROR: self._recover_from_error,
        }
        
        strategy = recovery_strategies.get(current_state)
        if strategy:
            strategy(sm)
        
        return sm
    
    def _recover_from_planning(self, sm: StateManager):
        """Recovery když spadl během plánování."""
        RichPrinter.info("♻️  Recovery strategie: Restart plánování")
        # Přejdi zpět do IDLE a pak znovu do PLANNING
        sm.current_state = State.IDLE  # Force reset
        sm.transition_to(State.PLANNING, "Recovery: restarting planning")
    
    def _recover_from_executing(self, sm: StateManager):
        """Recovery když spadl během provádění kroku."""
        RichPrinter.info("♻️  Recovery strategie: Zkus krok znovu nebo přejdi na reflexi")
        # Pokud byl tool_call uložen, můžeme ho zkusit znovu
        pending_tool = sm.get_data("pending_tool_call")
        if pending_tool:
            RichPrinter.info(f"   Nalezen nedokončený tool call: {pending_tool.get('tool_name')}")
            # Orchestrátor se pokusí krok opakovat
        else:
            # Přejdi na reflexi - něco se pokazilo
            sm.current_state = State.AWAITING_TOOL_RESULT  # Force valid transition
            sm.transition_to(State.REFLECTION, "Recovery: analyzing failure")
    
    def _recover_from_awaiting_tool(self, sm: StateManager):
        """Recovery když spadl při čekání na výsledek nástroje."""
        RichPrinter.warning("⚠️  Recovery strategie: Tool pravděpodobně selhal")
        sm.transition_to(State.REFLECTION, "Recovery: tool execution interrupted")
    
    def _recover_from_reflection(self, sm: StateManager):
        """Recovery během reflexe."""
        RichPrinter.info("♻️  Recovery strategie: Pokračuj v reflexi")
        # Reflexe je bezpečná - můžeme pokračovat
        pass
    
    def _recover_from_error(self, sm: StateManager):
        """Recovery z chybového stavu."""
        RichPrinter.error("❌ Recovery strategie: Přejdi do reflexe k analýze chyby")
        sm.transition_to(State.REFLECTION, "Recovery: analyzing error state")
```

**CHECKPOINT 2:** ✅ RecoveryManager dokáže obnovit simulovaný pád

---

## 🚀 FÁZE 2: PlanManager (2 dny)

### Den 4-5: Proaktivní Plánování

**Cíl:** Transformovat reaktivní loop na proaktivní exekuci plánu.

```python
# core/plan_manager.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from core.rich_printer import RichPrinter

@dataclass
class PlanStep:
    """Reprezentuje jeden krok v plánu."""
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed, skipped
    dependencies: List[int] = None
    estimated_tokens: int = 0
    actual_tokens: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PlanManager:
    """
    Spravuje plán mise - vytváření, sledování, aktualizace.
    """
    
    def __init__(self, llm_manager, project_root: str = "."):
        self.llm_manager = llm_manager
        self.project_root = project_root
        self.steps: List[PlanStep] = []
        self.current_step_index = 0
    
    async def create_plan(self, mission_goal: str, context: str = "") -> List[PlanStep]:
        """
        Vytvoří plán pro daný cíl mise pomocí LLM.
        
        Returns:
            Seznam PlanStep objektů
        """
        RichPrinter.info("📋 Vytvářím plán mise...")
        
        planning_prompt = f"""Jsi strategický plánovač. Rozlož následující úkol na konkrétní, proveditelné kroky.

ÚKOL:
{mission_goal}

KONTEXT:
{context}

POŽADAVKY:
1. Každý krok musí být atomický a testovatelný
2. Kroky musí být seřazeny logicky (respektuj závislosti)
3. Odhadni složitost každého kroku (tokens: 100-2000)
4. Maximálně 10 kroků

FORMÁT ODPOVĚDI (striktní JSON):
{{
  "steps": [
    {{
      "id": 1,
      "description": "Konkrétní akce kterou provedu",
      "dependencies": [],
      "estimated_tokens": 500
    }},
    ...
  ]
}}
"""
        
        model = self.llm_manager.get_llm("powerful")  # Použij silný model pro plánování
        response, _ = await model.generate_content_async(planning_prompt)
        
        # Parse JSON z odpovědi
        import json, re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group(1))
        else:
            # Pokus se parsovat celou odpověď jako JSON
            plan_data = json.loads(response)
        
        # Konverze na PlanStep objekty
        self.steps = [
            PlanStep(
                id=step["id"],
                description=step["description"],
                dependencies=step.get("dependencies", []),
                estimated_tokens=step.get("estimated_tokens", 500)
            )
            for step in plan_data["steps"]
        ]
        
        # Zobraz plán
        RichPrinter.info("✅ Plán vytvořen:")
        for step in self.steps:
            deps_str = f" (závislosti: {step.dependencies})" if step.dependencies else ""
            RichPrinter.info(f"   {step.id}. {step.description}{deps_str}")
        
        return self.steps
    
    def get_next_step(self) -> Optional[PlanStep]:
        """
        Vrátí další krok k provedení (respektuje závislosti).
        
        Returns:
            PlanStep nebo None pokud žádný dostupný
        """
        for step in self.steps:
            if step.status == "pending":
                # Zkontroluj, zda jsou splněny závislosti
                if self._are_dependencies_met(step):
                    return step
        
        return None  # Žádný dostupný krok
    
    def _are_dependencies_met(self, step: PlanStep) -> bool:
        """Zkontroluje, zda jsou splněny všechny závislosti kroku."""
        for dep_id in step.dependencies:
            dep_step = next((s for s in self.steps if s.id == dep_id), None)
            if dep_step and dep_step.status != "completed":
                return False
        return True
    
    def mark_step_in_progress(self, step_id: int):
        """Označí krok jako probíhající."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "in_progress"
            RichPrinter.info(f"▶️  Krok {step_id}: {step.description}")
    
    def mark_step_completed(self, step_id: int, result: str, tokens_used: int):
        """Označí krok jako dokončený."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "completed"
            step.result = result
            step.actual_tokens = tokens_used
            RichPrinter.info(f"✅ Krok {step_id} dokončen")
    
    def mark_step_failed(self, step_id: int, error: str):
        """Označí krok jako selhavší."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "failed"
            step.error = error
            RichPrinter.error(f"❌ Krok {step_id} selhal: {error}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Vrátí statistiky pokroku."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == "completed")
        failed = sum(1 for s in self.steps if s.status == "failed")
        
        return {
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }
    
    def _get_step_by_id(self, step_id: int) -> Optional[PlanStep]:
        """Najde krok podle ID."""
        return next((s for s in self.steps if s.id == step_id), None)
    
    def is_plan_complete(self) -> bool:
        """True pokud jsou všechny kroky dokončeny nebo přeskočeny."""
        return all(s.status in ["completed", "skipped"] for s in self.steps)
    
    def serialize(self) -> Dict[str, Any]:
        """Serializuje plán do JSON-friendly formátu."""
        return {
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "status": s.status,
                    "dependencies": s.dependencies,
                    "estimated_tokens": s.estimated_tokens,
                    "actual_tokens": s.actual_tokens,
                    "result": s.result,
                    "error": s.error
                }
                for s in self.steps
            ],
            "current_step_index": self.current_step_index
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any], llm_manager) -> 'PlanManager':
        """Obnoví PlanManager ze serializované podoby."""
        pm = cls(llm_manager)
        pm.steps = [
            PlanStep(
                id=s["id"],
                description=s["description"],
                status=s["status"],
                dependencies=s["dependencies"],
                estimated_tokens=s["estimated_tokens"],
                actual_tokens=s["actual_tokens"],
                result=s.get("result"),
                error=s.get("error")
            )
            for s in data["steps"]
        ]
        pm.current_step_index = data["current_step_index"]
        return pm
```

**CHECKPOINT 3:** ✅ PlanManager vytvoří a vykoná 3-krokový testovací plán

---

## 🚀 FÁZE 3: ReflectionEngine (2 dny)

### Den 6-7: Učení z Chyb

**Cíl:** Analýza selhání a adaptace strategie.

```python
# core/reflection_engine.py

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from core.rich_printer import RichPrinter

@dataclass
class ReflectionResult:
    """Výsledek reflexe po chybě/úspěchu."""
    analysis: str
    root_cause: str
    suggested_action: str  # "retry", "replanning", "ask_user", "skip_step"
    confidence: float  # 0.0 - 1.0


class ReflectionEngine:
    """
    Provádí reflexi po chybách a adaptuje strategii.
    """
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.reflection_history: List[Dict] = []
    
    async def reflect_on_failure(
        self, 
        failed_step: Dict[str, Any],
        error_message: str,
        attempt_count: int,
        plan_context: str = ""
    ) -> ReflectionResult:
        """
        Analyzuje selhání kroku a navrhne další akci.
        
        Args:
            failed_step: Informace o selhaném kroku
            error_message: Chybová hláška
            attempt_count: Kolikátý pokus to byl
            plan_context: Kontext celkového plánu
        
        Returns:
            ReflectionResult s analýzou a doporučením
        """
        RichPrinter.warning(f"🤔 Reflexe selhání (pokus #{attempt_count})...")
        
        reflection_prompt = f"""Jsi analytik chyb AI agenta. Analyzuj následující selhání a navrhni nejlepší další krok.

SELHAVŠÍ KROK:
{failed_step.get('description', 'N/A')}

CHYBOVÁ HLÁŠKA:
{error_message}

POKUS Č.: {attempt_count}

KONTEXT PLÁNU:
{plan_context}

HISTORIE REFLEXÍ:
{self._format_reflection_history()}

TVŮJ ÚKOL:
1. Identifikuj skutečnou příčinu (root cause) - ne jen symptom
2. Navrhni konkrétní akci

MOŽNÉ AKCE:
- "retry": Zkus stejný krok znovu (pokud je chyba přechodná)
- "retry_modified": Zkus modifikovanou verzi (uprav parametry)
- "replanning": Plán je špatný, je třeba přeplánovat
- "ask_user": Potřebuji pomoc nebo upřesnění od uživatele
- "skip_step": Tento krok není kritický, lze přeskočit

FORMÁT ODPOVĚDI (JSON):
{{
  "analysis": "Co se skutečně stalo (2-3 věty)",
  "root_cause": "Skutečná příčina (ne symptom)",
  "suggested_action": "retry|retry_modified|replanning|ask_user|skip_step",
  "confidence": 0.8,
  "modification_hint": "Pokud action=retry_modified, jak upravit krok?"
}}
"""
        
        model = self.llm_manager.get_llm("powerful")
        response, _ = await model.generate_content_async(reflection_prompt)
        
        # Parse JSON
        import json, re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            reflection_data = json.loads(json_match.group(1))
        else:
            reflection_data = json.loads(response)
        
        result = ReflectionResult(
            analysis=reflection_data["analysis"],
            root_cause=reflection_data["root_cause"],
            suggested_action=reflection_data["suggested_action"],
            confidence=reflection_data.get("confidence", 0.5)
        )
        
        # Zaznamenej do historie
        self.reflection_history.append({
            "timestamp": datetime.now().isoformat(),
            "step": failed_step,
            "error": error_message,
            "result": result.__dict__
        })
        
        # Zobraz výsledek
        RichPrinter.info(f"💡 Analýza: {result.analysis}")
        RichPrinter.info(f"🎯 Příčina: {result.root_cause}")
        RichPrinter.info(f"➡️  Doporučení: {result.suggested_action} (confidence: {result.confidence:.0%})")
        
        return result
    
    def _format_reflection_history(self) -> str:
        """Formátuje historii reflexí pro kontext."""
        if not self.reflection_history:
            return "Žádné předchozí reflexe."
        
        # Zobraz posledních 3
        recent = self.reflection_history[-3:]
        formatted = []
        for i, ref in enumerate(recent, 1):
            formatted.append(
                f"{i}. Chyba: {ref['error'][:50]}... → Akce: {ref['result']['suggested_action']}"
            )
        return "\n".join(formatted)
    
    async def reflect_on_success(self, completed_step: Dict[str, Any]):
        """
        Reflexe po úspěšném kroku (pro učení co fungovalo).
        """
        # Jednodušší - jen zaznamenej do historie
        self.reflection_history.append({
            "timestamp": datetime.now().isoformat(),
            "step": completed_step,
            "result": {"status": "success"}
        })
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """
        Analyzuje opakující se vzory selhání.
        
        Returns:
            Slovník {typ_chyby: počet_výskytů}
        """
        patterns = {}
        for reflection in self.reflection_history:
            if "error" in reflection:
                root_cause = reflection["result"].get("root_cause", "unknown")
                patterns[root_cause] = patterns.get(root_cause, 0) + 1
        return patterns
```

**CHECKPOINT 4:** ✅ ReflectionEngine správně rozpozná "retry" vs "replanning" scénář

---

## 🚀 FÁZE 4: BudgetTracker (1 den)

### Den 8: Prevence Vyčerpání Rozpočtu

```python
# core/budget_tracker.py

from typing import Dict, Any
from core.rich_printer import RichPrinter

class BudgetTracker:
    """
    Sleduje spotřebu tokenů a času a varuje před vyčerpáním.
    """
    
    def __init__(self, max_tokens: int = 100000, max_time_seconds: int = 3600):
        self.max_tokens = max_tokens
        self.max_time_seconds = max_time_seconds
        self.tokens_used = 0
        self.time_elapsed = 0
        self.step_costs: Dict[int, int] = {}
    
    def record_step_cost(self, step_id: int, tokens: int, seconds: float):
        """Zaznamená náklady kroku."""
        self.tokens_used += tokens
        self.time_elapsed += seconds
        self.step_costs[step_id] = tokens
    
    def check_budget(self, estimated_tokens: int = 0) -> Dict[str, Any]:
        """
        Zkontroluje, zda je dostatek rozpočtu.
        
        Returns:
            {
                "can_proceed": bool,
                "warning": str,
                "tokens_remaining": int,
                "time_remaining": float
            }
        """
        tokens_remaining = self.max_tokens - self.tokens_used
        time_remaining = self.max_time_seconds - self.time_elapsed
        
        can_proceed = (
            tokens_remaining >= estimated_tokens and
            time_remaining > 60  # Aspoň 1 minuta
        )
        
        warning = None
        if tokens_remaining < self.max_tokens * 0.2:  # Méně než 20%
            warning = f"⚠️  NÍZKÝ ROZPOČET TOKENŮ: Zbývá {tokens_remaining}/{self.max_tokens}"
        elif tokens_remaining < estimated_tokens:
            warning = f"❌ NEDOSTATEK TOKENŮ: Potřeba {estimated_tokens}, zbývá {tokens_remaining}"
        
        if time_remaining < 300:  # Méně než 5 minut
            warning = (warning or "") + f"\n⚠️  MÁLO ČASU: Zbývá {time_remaining:.0f}s"
        
        if warning:
            RichPrinter.warning(warning)
        
        return {
            "can_proceed": can_proceed,
            "warning": warning,
            "tokens_remaining": tokens_remaining,
            "time_remaining": time_remaining
        }
    
    def get_summary(self) -> str:
        """Vrátí přehled spotřeby."""
        return (
            f"Tokeny: {self.tokens_used}/{self.max_tokens} "
            f"({self.tokens_used/self.max_tokens*100:.1f}%) | "
            f"Čas: {self.time_elapsed:.0f}s/{self.max_time_seconds}s"
        )
```

**CHECKPOINT 5:** ✅ BudgetTracker správně varuje při 80% spotřebě

---

## 🚀 FÁZE 5: NomadOrchestratorV2 (3 dny)

### Den 9-11: Sjednocující Orchestrátor

**Cíl:** Integrace všech komponent do stavově řízeného orchestrátoru.

```python
# core/orchestrator_v2.py

import asyncio
from typing import Optional
from datetime import datetime
import time

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
    """
    
    def __init__(self, project_root: str = ".", session_id: str = None):
        self.project_root = project_root
        
        # Komponenty
        self.state_manager = StateManager(project_root, session_id)
        self.recovery_manager = RecoveryManager(project_root)
        self.llm_manager = LLMManager(project_root)
        self.plan_manager = PlanManager(self.llm_manager, project_root)
        self.reflection_engine = ReflectionEngine(self.llm_manager)
        self.budget_tracker = BudgetTracker(max_tokens=100000, max_time_seconds=3600)
        self.mcp_client = MCPClient(project_root)
        
        self.max_step_retries = 3
    
    async def initialize(self):
        """Inicializace všech komponent."""
        await self.mcp_client.start_servers()
        RichPrinter.info("✅ NomadOrchestratorV2 inicializován")
    
    async def start_mission(self, mission_goal: str, recover_if_crashed: bool = True):
        """
        Hlavní vstupní bod - zahájí misi.
        """
        # Krok 1: Zkontroluj crashed sessions
        if recover_if_crashed:
            crashed = self.recovery_manager.find_crashed_sessions()
            if crashed:
                RichPrinter.warning(f"🔧 Nalezena {len(crashed)} nedokončená sezení")
                # Pro jednoduchost vezmeme první (v reálu by se zeptal uživatele)
                recovered_sm = self.recovery_manager.recover_session(crashed[0])
                if recovered_sm:
                    self.state_manager = recovered_sm
                    # Pokračuj v misi
                    await self._run_state_machine()
                    return
        
        # Krok 2: Nová mise
        self.state_manager.set_data("mission_goal", mission_goal)
        self.state_manager.set_data("mission_start_time", datetime.now().isoformat())
        self.state_manager.transition_to(State.PLANNING, "Nová mise")
        
        # Krok 3: Spusť stavový stroj
        await self._run_state_machine()
    
    async def _run_state_machine(self):
        """
        Hlavní smyčka stavového stroje.
        """
        RichPrinter.info("🚀 Spouštím stavový stroj...")
        
        while self.state_manager.get_state() not in [State.COMPLETED, State.IDLE]:
            current_state = self.state_manager.get_state()
            
            RichPrinter.info(f"📍 Stav: {current_state.value}")
            
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
                await handler()
            else:
                RichPrinter.error(f"❌ Neznámý stav: {current_state}")
                break
            
            # Krátká pauza mezi stavy (pro debugging)
            await asyncio.sleep(0.1)
        
        RichPrinter.info(f"🏁 Mise ukončena ve stavu: {self.state_manager.get_state().value}")
    
    async def _state_planning(self):
        """STAV: Vytváření plánu."""
        mission_goal = self.state_manager.get_data("mission_goal")
        
        # Vytvoř plán
        plan = await self.plan_manager.create_plan(mission_goal)
        
        # Uložení plánu do state
        self.state_manager.set_data("plan", self.plan_manager.serialize())
        
        # Přechod na exekuci
        self.state_manager.transition_to(State.EXECUTING_STEP, "Plán vytvořen")
    
    async def _state_executing_step(self):
        """STAV: Provádění kroku plánu."""
        start_time = time.time()
        
        # Získej další krok
        next_step = self.plan_manager.get_next_step()
        
        if not next_step:
            # Žádný další krok → plán dokončen
            if self.plan_manager.is_plan_complete():
                self.state_manager.transition_to(State.RESPONDING, "Plán dokončen")
                return
            else:
                # Jsou kroky, ale všechny mají nesplněné závislosti → chyba
                self.state_manager.set_data("error_message", "Deadlock v závislostech plánu")
                self.state_manager.transition_to(State.ERROR, "Deadlock")
                return
        
        # Zkontroluj budget
        budget_check = self.budget_tracker.check_budget(next_step.estimated_tokens)
        if not budget_check["can_proceed"]:
            RichPrinter.error("❌ Nedostatek rozpočtu!")
            self.state_manager.set_data("error_message", budget_check["warning"])
            self.state_manager.transition_to(State.ERROR, "Budget exceeded")
            return
        
        # Označ krok jako probíhající
        self.plan_manager.mark_step_in_progress(next_step.id)
        
        # Vytvoř prompt pro LLM
        prompt = self._build_step_prompt(next_step)
        
        # Zavolej LLM
        model = self.llm_manager.get_llm("powerful")
        response, usage = await model.generate_content_async(prompt)
        
        # Zaznamenej náklady
        tokens_used = usage.get("usage", {}).get("total_tokens", 0) if usage else 0
        elapsed = time.time() - start_time
        self.budget_tracker.record_step_cost(next_step.id, tokens_used, elapsed)
        
        # Parse odpověď LLM (očekáváme tool_call)
        tool_call = self._parse_tool_call(response)
        
        if not tool_call:
            # LLM nechtěl volat nástroj → přejdi na reflexi
            self.state_manager.set_data("error_message", "LLM nevygeneroval tool call")
            self.state_manager.transition_to(State.REFLECTION, "Missing tool call")
            return
        
        # Ulož pending tool call do stavu (pro recovery)
        self.state_manager.set_data("pending_tool_call", tool_call)
        self.state_manager.set_data("current_step_id", next_step.id)
        
        # Přechod na čekání na výsledek
        self.state_manager.transition_to(State.AWAITING_TOOL_RESULT, "Tool call prepared")
    
    async def _state_awaiting_tool_result(self):
        """STAV: Čekání na výsledek nástroje."""
        tool_call = self.state_manager.get_data("pending_tool_call")
        step_id = self.state_manager.get_data("current_step_id")
        
        # Proveď tool call
        try:
            result = await self.mcp_client.execute_tool(
                tool_call["tool_name"],
                tool_call.get("args", []),
                tool_call.get("kwargs", {}),
                verbose=True
            )
            
            # Úspěch
            self.plan_manager.mark_step_completed(step_id, result, tokens_used=0)
            
            # Reflexe úspěchu
            await self.reflection_engine.reflect_on_success({"id": step_id})
            
            # Vyčisti pending data
            self.state_manager.set_data("pending_tool_call", None)
            
            # Přechod zpět na exekuci dalšího kroku
            self.state_manager.transition_to(State.EXECUTING_STEP, "Tool succeeded")
            
        except Exception as e:
            # Selhání nástroje
            error_msg = str(e)
            self.plan_manager.mark_step_failed(step_id, error_msg)
            
            # Přechod na reflexi
            self.state_manager.set_data("error_message", error_msg)
            self.state_manager.transition_to(State.REFLECTION, "Tool failed")
    
    async def _state_reflection(self):
        """STAV: Reflexe po chybě."""
        error_msg = self.state_manager.get_data("error_message", "Unknown error")
        step_id = self.state_manager.get_data("current_step_id")
        
        failed_step = self.plan_manager._get_step_by_id(step_id)
        if not failed_step:
            # Chyba mimo kontext kroku
            RichPrinter.error("Kritická chyba mimo kontext kroku")
            self.state_manager.transition_to(State.ERROR, "Unrecoverable")
            return
        
        # Kolikátý pokus?
        attempt = self.state_manager.get_data(f"step_{step_id}_attempts", 0) + 1
        self.state_manager.set_data(f"step_{step_id}_attempts", attempt)
        
        # Reflexe
        reflection = await self.reflection_engine.reflect_on_failure(
            failed_step.__dict__,
            error_msg,
            attempt,
            plan_context=str(self.plan_manager.steps)
        )
        
        # Rozhodnutí podle doporučení
        if reflection.suggested_action == "retry" and attempt < self.max_step_retries:
            RichPrinter.info("🔄 Zkouším krok znovu...")
            failed_step.status = "pending"  # Reset na pending
            self.state_manager.transition_to(State.EXECUTING_STEP, "Retrying step")
        
        elif reflection.suggested_action == "replanning":
            RichPrinter.warning("📋 Přeplánovávám...")
            self.state_manager.transition_to(State.PLANNING, "Replanning")
        
        elif reflection.suggested_action == "ask_user":
            RichPrinter.warning("❓ Potřebuji pomoc uživatele")
            self.state_manager.transition_to(State.RESPONDING, "Asking user")
        
        elif reflection.suggested_action == "skip_step":
            RichPrinter.info("⏭️  Přeskakuji krok")
            failed_step.status = "skipped"
            self.state_manager.transition_to(State.EXECUTING_STEP, "Step skipped")
        
        else:
            # Vyčerpány pokusy → ERROR
            RichPrinter.error(f"❌ Krok selhal po {attempt} pokusech")
            self.state_manager.transition_to(State.ERROR, "Max retries exceeded")
    
    async def _state_responding(self):
        """STAV: Generování finální odpovědi."""
        progress = self.plan_manager.get_progress()
        
        RichPrinter.info(f"📊 Pokrok: {progress['progress_percent']:.0f}% dokončeno")
        
        # Vygeneruj shrnutí
        summary_prompt = f"""Úkol: {self.state_manager.get_data('mission_goal')}

Plán byl dokončen. Shrň výsledky.

STATISTIKY:
- Dokončeno kroků: {progress['completed']}/{progress['total_steps']}
- Selhalo: {progress['failed']}

Vytvoř stručné shrnutí pro uživatele (max 3 věty).
"""
        
        model = self.llm_manager.get_llm("economical")
        summary, _ = await model.generate_content_async(summary_prompt)
        
        RichPrinter.show_task_complete(summary)
        
        # Přechod na COMPLETED
        self.state_manager.transition_to(State.COMPLETED, "Mission accomplished")
    
    async def _state_error(self):
        """STAV: Kritická chyba."""
        error_msg = self.state_manager.get_data("error_message", "Unknown error")
        RichPrinter.error(f"💥 Kritická chyba: {error_msg}")
        
        # Přechod do IDLE (mise ukončena)
        self.state_manager.transition_to(State.IDLE, "Error recovery")
    
    def _build_step_prompt(self, step) -> str:
        """Sestaví prompt pro provedení kroku."""
        return f"""Jsi Nomád - autonomní AI agent.

AKTUÁLNÍ KROK:
{step.description}

Tvůj úkol: Vyber nejvhodnější nástroj a proveď tento krok.

Dostupné nástroje:
{self.mcp_client.get_tool_descriptions()}

Odpověz ve formátu:
|||TOOL_CALL|||
{{
  "tool_name": "název_nástroje",
  "args": [...],
  "kwargs": {{...}}
}}
"""
    
    def _parse_tool_call(self, response: str):
        """Parse tool call z LLM odpovědi."""
        if "|||TOOL_CALL|||" not in response:
            return None
        
        import json, re
        parts = response.split("|||TOOL_CALL|||", 1)
        json_str = parts[1].strip()
        
        # Najdi první platný JSON objekt
        match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
    
    async def shutdown(self):
        """Bezpečné vypnutí."""
        await self.mcp_client.shutdown_servers()
        RichPrinter.info("👋 Orchestrátor ukončen")
```

**CHECKPOINT 6:** ✅ Kompletní mise projde všemi stavy: PLANNING → EXECUTING → AWAITING → REFLECTION (při chybě) → RESPONDING → COMPLETED

---

## 🚀 FÁZE 6: Testování a Dokumentace (1 den)

### Den 12: E2E Testy a Dokumentace

```python
# tests/test_e2e_orchestrator_v2.py

import pytest
import asyncio
from core.orchestrator_v2 import NomadOrchestratorV2

@pytest.mark.asyncio
async def test_simple_mission_success():
    """Test jednoduché mise bez chyb."""
    orchestrator = NomadOrchestratorV2()
    await orchestrator.initialize()
    
    await orchestrator.start_mission("Vypiš obsah adresáře sandbox/")
    
    # Kontrola
    assert orchestrator.state_manager.get_state().value == "completed"
    assert orchestrator.plan_manager.is_plan_complete()


@pytest.mark.asyncio
async def test_mission_with_recovery():
    """Test recovery po simulovaném pádu."""
    # Fáze 1: Spusť misi a "spadni" uprostřed
    orch1 = NomadOrchestratorV2(session_id="recovery_test")
    await orch1.initialize()
    
    # Simuluj pád po vytvoření plánu
    orch1.state_manager.transition_to(State.PLANNING)
    await orch1._state_planning()
    # ... násilné ukončení ...
    
    # Fáze 2: Nová instance - měla by obnovit
    orch2 = NomadOrchestratorV2()
    await orch2.initialize()
    
    await orch2.start_mission("", recover_if_crashed=True)
    
    # Mělo by pokračovat tam, kde skončila první instance
    assert orch2.state_manager.session_id == "recovery_test"
```

**Finální Aktualizace Dokumentace:**

```markdown
# docs/ORCHESTRATOR_V2.md

# NomadOrchestratorV2 - Technická Dokumentace

## Architektura

### Stavový Diagram

```
IDLE → PLANNING → EXECUTING_STEP → AWAITING_TOOL_RESULT → EXECUTING_STEP (loop)
                      ↓                     ↓
                   ERROR              REFLECTION
                      ↓                     ↓
                REFLECTION            PLANNING (replanning)
                      ↓
                  RESPONDING → COMPLETED → IDLE
```

### Komponenty

1. **StateManager**: Spravuje přechody mezi stavy s validací
2. **RecoveryManager**: Automatické obnovení po pádu
3. **PlanManager**: Vytváření a sledování plánu mise
4. **ReflectionEngine**: Analýza selhání a adaptace
5. **BudgetTracker**: Sledování tokenů a času

## Použití

```python
orchestrator = NomadOrchestratorV2()
await orchestrator.initialize()
await orchestrator.start_mission("Vytvoř soubor test.txt s obsahem 'Hello'")
```

## Recovery Po Pádu

Pokud Nomád spadne, při dalším spuštění:
1. Detekuje nedokončenou session
2. Obnoví stav z `memory/session_*.json`
3. Pokračuje tam, kde skončil
```

---

## 📈 Výsledný Rozdíl: Před vs Po

### PŘED (JulesOrchestrator):
```python
for i in range(max_iterations):
    # ... volání LLM ...
    # ... provedení nástroje ...
    # ŽÁDNÁ persistence stavu
    # ŽÁDNÉ plánování
    # ŽÁDNÁ reflexe
```

### PO (NomadOrchestratorV2):
```python
# Explicitní stavy
IDLE → PLANNING → EXECUTING → AWAITING → REFLECTION → RESPONDING → COMPLETED

# Persistence po každém kroku
session_xyz.json:
{
  "current_state": "EXECUTING_STEP",
  "plan": { steps: [...], current: 3 },
  "pending_tool_call": {...}
}

# Proaktivní plánování
plan = PlanManager.create_plan(goal)

# Učení z chyb
reflection = ReflectionEngine.reflect_on_failure(...)
if reflection.action == "replanning":
    create_new_plan()
```

---

## ✅ Závěrečný Checklist

Před nasazením do produkce:

- [ ] Všechny unit testy projdou (`pytest tests/`)
- [ ] E2E test simuluje reálnou misi
- [ ] Recovery test simuluje pád a obnovu
- [ ] Budget tracker správně varuje při 80%
- [ ] Reflection engine správně kategorizuje chyby
- [ ] Dokumentace aktualizována (README, ARCHITECTURE)
- [ ] WORKLOG.md obsahuje záznam o refaktoringu

---

## 🎯 Další Kroky (Po Refaktoringu)

Jakmile je V2 stabilní:

1. **Migrace**: Přepnout `main.py` na `NomadOrchestratorV2`
2. **Cleanup**: Odstranit starý `JulesOrchestrator` (nebo přejmenovat na `orchestrator_legacy.py`)
3. **Monitoring**: Přidat metriky (průměrná doba kroku, úspěšnost, atd.)
4. **Optimalizace**: Profilování - kde se ztrácí nejvíc času?

---

**Autor:** Jules (Nomad)  
**Status:** ✅ FINÁLNÍ VERZE - Ready for Implementation  
**Datum:** 2025-10-12
