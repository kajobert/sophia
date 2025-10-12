# 🔧 Implementační Plán Nomáda - Detailní Day-by-Day Tasklist

**Datum Vytvoření:** 12. října 2025  
**Autor:** Jules (Nomad)  
**Verze:** 1.0 (FINÁLNÍ - PRODUCTION READY)  
**Kritičnost:** 🔴 VYSOKÁ - Každá chyba může ohrozit stabilitu Nomáda

---

## ⚠️ BEZPEČNOSTNÍ PRAVIDLA (PŘEČTI PŘED ZAČÁTKEM)

### Zlatá Pravidla Implementace:

1. **NIKDY nepřepisuj funkční kód bez zálohy**
2. **VŽDY spusť testy před commitem**
3. **NIKDY nemazej starý kód - přejmenuj na `_legacy.py`**
4. **VŽDY commituj po každém checkpointu**
5. **Pokud test selže 2x, ZASTAVÍ SE a analyzuj problém**

### Rollback Strategie:

```bash
# Pokud cokoliv selže, vrať se k poslednímu funkčnímu stavu:
git log --oneline | head -5  # Najdi poslední commit
git reset --hard <commit_sha>  # Vrať se zpět
git clean -fd  # Vyčisti nesledované soubory
```

### Pre-flight Checklist:

```bash
# Před začátkem refaktoringu:
cd /workspaces/sophia

# 1. Ověř Git je čistý
git status  # Mělo by být "nothing to commit, working tree clean"

# 2. Vytvoř bezpečnostní větev
git checkout -b refactoring/nomad-v2-implementation
git push -u origin refactoring/nomad-v2-implementation

# 3. Ověř všechny závislosti
python -m pytest tests/ -v  # Měly by projít všechny existující testy

# 4. Vytvoř backup současného orchestrátora
cp core/orchestrator.py core/orchestrator_backup_$(date +%Y%m%d).py

# 5. Ověř Python verzi
python --version  # Mělo by být >= 3.10
```

---

## 📅 DEN 1: StateManager - Jádro Systému

**Cíl:** Vytvořit robustní stavový stroj s validací a persistence.

**Časový Odhad:** 6-8 hodin  
**Riziko:** 🟡 STŘEDNÍ - Základní komponenta, ale izolovaná

### 1.1 Příprava Struktury (9:00 - 9:30)

```bash
# Krok 1.1.1: Vytvoř soubory
cd /workspaces/sophia
touch core/state_manager.py
touch tests/test_state_manager.py

# Krok 1.1.2: Ověř že soubory existují
ls -la core/state_manager.py
ls -la tests/test_state_manager.py

# Výstup by měl ukazovat oba soubory s velikostí 0 bytes
```

**✅ CHECKPOINT 1.1:** Soubory vytvořeny a viditelné v `ls`

---

### 1.2 Implementace State Enum (9:30 - 10:00)

```python
# Otevři: core/state_manager.py
# Vlož následující kód PŘESNĚ (copy-paste):

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
```

**Validace:**

```bash
# Test importu
python -c "from core.state_manager import State, StateTransitionError; print('✅ Enum import OK')"

# Očekávaný výstup: "✅ Enum import OK"
# Pokud error: Zkontroluj syntaxi, mezery, tabulátory!
```

**✅ CHECKPOINT 1.2:** Enum se importuje bez chyby

---

### 1.3 Implementace StateManager Třídy (10:00 - 11:30)

```python
# Pokračuj v core/state_manager.py
# Přidej ZA StateTransitionError třídu:

class StateManager:
    """
    Spravuje stav orchestrátora s validací přechodů a persistence.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Každý přechod je validován proti VALID_TRANSITIONS
    - Stav je automaticky persistován po každém přechodu
    - Session ID je buď zadané nebo auto-generované
    
    THREAD SAFETY: 
    - Tato třída NENÍ thread-safe!
    - Pro multi-threaded použití přidej threading.Lock
    """
    
    # KRITICKÁ TABULKA: Definuje povolené přechody
    # Formát: {z_stavu: [do_stavu1, do_stavu2, ...]}
    VALID_TRANSITIONS: Dict[State, List[State]] = {
        State.IDLE: [State.PLANNING],
        State.PLANNING: [State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.EXECUTING_STEP: [State.AWAITING_TOOL_RESULT, State.RESPONDING, State.ERROR],
        State.AWAITING_TOOL_RESULT: [State.REFLECTION, State.EXECUTING_STEP, State.ERROR],
        State.REFLECTION: [State.PLANNING, State.EXECUTING_STEP, State.RESPONDING, State.ERROR],
        State.RESPONDING: [State.COMPLETED, State.EXECUTING_STEP, State.PLANNING],
        State.COMPLETED: [State.IDLE],
        State.ERROR: [State.IDLE, State.REFLECTION],
    }
    
    def __init__(self, project_root: str = ".", session_id: Optional[str] = None):
        """
        Inicializuje StateManager.
        
        Args:
            project_root: Absolutní cesta k projektu
            session_id: ID sezení (pokud None, vygeneruje se nové)
        """
        self.project_root = os.path.abspath(project_root)
        self.session_id = session_id or self._generate_session_id()
        self.current_state = State.IDLE
        self.state_data: Dict[str, Any] = {}
        self.state_history: List[Dict[str, Any]] = []
        
        # Persistence path
        memory_dir = os.path.join(self.project_root, "memory")
        os.makedirs(memory_dir, exist_ok=True)
        self.session_file = os.path.join(memory_dir, f"session_{self.session_id}.json")
    
    def _generate_session_id(self) -> str:
        """
        Generuje unikátní session ID.
        
        Formát: YYYYMMDD_HHMMSS (např. 20251012_143052)
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
            
        BEZPEČNOSTNÍ KONTROLA:
        - Pokud current_state není v VALID_TRANSITIONS, vyhodí exception
        - Toto zachytává BUGy v kódu (např. zapomenuté stavy)
        """
        # Validace: Je current_state vůbec v tabulce?
        if self.current_state not in self.VALID_TRANSITIONS:
            raise StateTransitionError(
                f"KRITICKÁ CHYBA: Stav {self.current_state.value} není definován "
                f"v VALID_TRANSITIONS! To je BUG v kódu!"
            )
        
        # Validace: Je přechod povolen?
        allowed_transitions = self.VALID_TRANSITIONS[self.current_state]
        if new_state not in allowed_transitions:
            allowed_str = ", ".join([s.value for s in allowed_transitions])
            raise StateTransitionError(
                f"Neplatný přechod: {self.current_state.value} → {new_state.value}\n"
                f"Povolené přechody z {self.current_state.value}: {allowed_str}\n"
                f"Důvod pokusu: {reason}"
            )
        
        # Zaznamenej do historie (pro debugging)
        transition_record = {
            "from": self.current_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.state_history.append(transition_record)
        
        # Proveď přechod
        old_state = self.current_state
        self.current_state = new_state
        
        # Persist OKAMŽITĚ (crash resilience)
        self.persist()
        
        # Logging (může být nahrazen RichPrinter v budoucnu)
        print(f"🔄 State Transition: {old_state.value} → {new_state.value}")
        if reason:
            print(f"   Reason: {reason}")
        
        return True
    
    def get_state(self) -> State:
        """Vrátí aktuální stav."""
        return self.current_state
    
    def set_data(self, key: str, value: Any):
        """
        Uloží data asociovaná se stavem.
        
        POUŽITÍ:
        - Ukládání mission_goal, current_step_id, pending_tool_call, atd.
        - Data jsou automaticky persistována
        
        BEZPEČNOSTNÍ POZNÁMKA:
        - Hodnota MUSÍ být JSON-serializable!
        - Pokud ne, persist() vyhodí TypeError
        """
        self.state_data[key] = value
        self.persist()  # Auto-save
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Načte data asociovaná se stavem.
        
        Args:
            key: Klíč dat
            default: Výchozí hodnota pokud klíč neexistuje
        """
        return self.state_data.get(key, default)
    
    def persist(self):
        """
        Uloží kompletní stav do JSON souboru.
        
        KRITICKÉ VLASTNOSTI:
        - Atomický zápis (nejdřív do .tmp, pak rename)
        - Zachovává kompletní historii přechodů
        - Pokud selže, vyhodí IOError (caller musí zachytit)
        
        RECOVERY MECHANISMUS:
        - Při pádu můžeme načíst poslední stav z tohoto souboru
        """
        snapshot = {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "state_data": self.state_data,
            "state_history": self.state_history,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"  # Pro budoucí migraci formátu
        }
        
        # Atomický zápis: Nejdřív .tmp, pak rename
        tmp_file = self.session_file + ".tmp"
        try:
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
            # Atomické přejmenování (POSIX safe)
            os.replace(tmp_file, self.session_file)
            
        except (TypeError, IOError) as e:
            # Cleanup tmp pokud selhal
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            raise IOError(f"Selhání persistence state: {e}")
    
    def restore(self) -> bool:
        """
        Obnoví stav ze session souboru.
        
        Returns:
            True pokud úspěšné, False pokud soubor neexistuje
        
        Raises:
            json.JSONDecodeError: Pokud je soubor korumpovaný
            ValueError: Pokud obsahuje neplatný stav
        """
        if not os.path.exists(self.session_file):
            return False
        
        with open(self.session_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Validace verze (pro budoucí migrace)
        version = snapshot.get("version", "1.0")
        if version != "1.0":
            raise ValueError(f"Nepodporovaná verze session souboru: {version}")
        
        # Restore dat
        self.session_id = snapshot["session_id"]
        
        # KRITICKÁ VALIDACE: Je načtený stav platný?
        try:
            restored_state = State(snapshot["current_state"])
        except ValueError as e:
            raise ValueError(
                f"Session soubor obsahuje neplatný stav: {snapshot['current_state']}"
            ) from e
        
        self.current_state = restored_state
        self.state_data = snapshot["state_data"]
        self.state_history = snapshot["state_history"]
        
        print(f"✅ State restored from {self.session_file}")
        print(f"   Current state: {self.current_state.value}")
        print(f"   Session ID: {self.session_id}")
        
        return True
    
    def reset(self):
        """
        Resetuje state manager na výchozí stav.
        
        POUŽITÍ: Po dokončení mise nebo při inicializaci nové mise.
        
        BEZPEČNOSTNÍ POZNÁMKA:
        - Toto NESMAŽE session soubor na disku!
        - Pro smazání použij delete_session()
        """
        self.current_state = State.IDLE
        self.state_data = {}
        self.state_history = []
        self.persist()
        
        print(f"🔄 StateManager reset to IDLE")
    
    def delete_session(self):
        """
        Smaže session soubor z disku.
        
        VAROVÁNÍ: Toto je DESTRUKTIVNÍ operace!
        """
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
            print(f"🗑️  Session file deleted: {self.session_file}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Vrátí lidsky čitelné shrnutí stavu.
        
        POUŽITÍ: Pro debugging, logy, TUI zobrazení
        """
        return {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "transitions_count": len(self.state_history),
            "data_keys": list(self.state_data.keys()),
            "last_transition": self.state_history[-1] if self.state_history else None
        }
```

**Validace:**

```bash
# Test kompletního importu
python -c "from core.state_manager import StateManager; sm = StateManager(); print('✅ StateManager import OK')"

# Test základní funkcionality
python -c "
from core.state_manager import StateManager, State
sm = StateManager()
sm.transition_to(State.PLANNING, 'Test')
assert sm.get_state() == State.PLANNING
print('✅ Basic transition works')
"

# Test persistence
python -c "
from core.state_manager import StateManager, State
sm = StateManager(session_id='test_persist')
sm.transition_to(State.PLANNING, 'Test')
sm.set_data('test_key', 'test_value')

# Nová instance - měla by obnovit
sm2 = StateManager(session_id='test_persist')
assert sm2.restore() == True
assert sm2.get_state() == State.PLANNING
assert sm2.get_data('test_key') == 'test_value'
print('✅ Persistence works')

# Cleanup
sm2.delete_session()
"
```

**Očekávaný Výstup:**
```
✅ StateManager import OK
🔄 State Transition: idle → planning
   Reason: Test
✅ Basic transition works
🔄 State Transition: idle → planning
   Reason: Test
✅ State restored from memory/session_test_persist.json
   Current state: planning
   Session ID: test_persist
✅ Persistence works
🗑️  Session file deleted: memory/session_test_persist.json
```

**❌ Co dělat když selže:**
- **ImportError**: Zkontroluj syntaxi, indentaci, použij `python -m py_compile core/state_manager.py`
- **AssertionError v persistence**: Zkontroluj zda `memory/` adresář existuje
- **StateTransitionError**: To je správně! Zkus platný přechod

**✅ CHECKPOINT 1.3:** Všechny 3 validační testy projdou

---

### 1.4 Unit Testy (11:30 - 13:00)

```python
# Otevři: tests/test_state_manager.py
# Vlož následující kód:

import pytest
import os
import sys
import json
from pathlib import Path

# Import cesty
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.state_manager import StateManager, State, StateTransitionError


class TestStateManager:
    """
    Kompletní test suite pro StateManager.
    
    FILOZOFIE TESTOVÁNÍ:
    - Každý test testuje JEDNU věc
    - Testy jsou nezávislé (každý má vlastní session_id)
    - Testy čistí po sobě (delete_session v teardown)
    """
    
    @pytest.fixture
    def temp_session_id(self):
        """Fixture poskytující unikátní session ID pro každý test."""
        import uuid
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        yield session_id
        
        # Cleanup po testu
        sm = StateManager(session_id=session_id)
        sm.delete_session()
    
    def test_initial_state_is_idle(self, temp_session_id):
        """Test: Nový StateManager začíná ve stavu IDLE."""
        sm = StateManager(session_id=temp_session_id)
        assert sm.get_state() == State.IDLE
    
    def test_valid_transition_succeeds(self, temp_session_id):
        """Test: Platný přechod projde."""
        sm = StateManager(session_id=temp_session_id)
        
        # IDLE → PLANNING je platný
        result = sm.transition_to(State.PLANNING, "Test transition")
        
        assert result == True
        assert sm.get_state() == State.PLANNING
    
    def test_invalid_transition_raises_error(self, temp_session_id):
        """Test: Neplatný přechod vyhodí StateTransitionError."""
        sm = StateManager(session_id=temp_session_id)
        
        # IDLE → EXECUTING_STEP není platný (musí jít přes PLANNING)
        with pytest.raises(StateTransitionError) as exc_info:
            sm.transition_to(State.EXECUTING_STEP, "Invalid jump")
        
        # Zkontroluj error message obsahuje info
        assert "IDLE" in str(exc_info.value).lower()
        assert "executing_step" in str(exc_info.value).lower()
    
    def test_state_data_storage(self, temp_session_id):
        """Test: set_data a get_data fungují správně."""
        sm = StateManager(session_id=temp_session_id)
        
        sm.set_data("mission_goal", "Test mission")
        sm.set_data("step_count", 5)
        
        assert sm.get_data("mission_goal") == "Test mission"
        assert sm.get_data("step_count") == 5
        assert sm.get_data("nonexistent", "default") == "default"
    
    def test_persistence_and_restore(self, temp_session_id):
        """Test: Stav se správně uloží a obnoví."""
        # Fáze 1: Vytvoř a ulož stav
        sm1 = StateManager(session_id=temp_session_id)
        sm1.transition_to(State.PLANNING, "Creating plan")
        sm1.set_data("test_data", {"key": "value"})
        
        # Fáze 2: Nová instance - restore
        sm2 = StateManager(session_id=temp_session_id)
        restore_success = sm2.restore()
        
        assert restore_success == True
        assert sm2.get_state() == State.PLANNING
        assert sm2.get_data("test_data") == {"key": "value"}
    
    def test_restore_nonexistent_session_returns_false(self):
        """Test: Restore neexistující session vrátí False."""
        sm = StateManager(session_id="nonexistent_session_12345")
        result = sm.restore()
        
        assert result == False
        assert sm.get_state() == State.IDLE  # Zůstane v původním stavu
    
    def test_state_history_records_transitions(self, temp_session_id):
        """Test: Historie přechodů se zaznamenává."""
        sm = StateManager(session_id=temp_session_id)
        
        sm.transition_to(State.PLANNING, "Reason 1")
        sm.transition_to(State.EXECUTING_STEP, "Reason 2")
        
        assert len(sm.state_history) == 2
        assert sm.state_history[0]["from"] == "idle"
        assert sm.state_history[0]["to"] == "planning"
        assert sm.state_history[0]["reason"] == "Reason 1"
        assert sm.state_history[1]["from"] == "planning"
        assert sm.state_history[1]["to"] == "executing_step"
    
    def test_reset_clears_state(self, temp_session_id):
        """Test: reset() vrátí state manager do výchozího stavu."""
        sm = StateManager(session_id=temp_session_id)
        
        sm.transition_to(State.PLANNING)
        sm.set_data("some_key", "some_value")
        
        sm.reset()
        
        assert sm.get_state() == State.IDLE
        assert sm.get_data("some_key") is None
        assert len(sm.state_history) == 0
    
    def test_get_state_summary(self, temp_session_id):
        """Test: get_state_summary vrátí správná data."""
        sm = StateManager(session_id=temp_session_id)
        sm.transition_to(State.PLANNING)
        sm.set_data("key1", "value1")
        
        summary = sm.get_state_summary()
        
        assert summary["session_id"] == temp_session_id
        assert summary["current_state"] == "planning"
        assert summary["transitions_count"] == 1
        assert "key1" in summary["data_keys"]
    
    def test_complex_transition_chain(self, temp_session_id):
        """Test: Složitější řetězec přechodů."""
        sm = StateManager(session_id=temp_session_id)
        
        # Simulace reálného workflow
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        sm.transition_to(State.AWAITING_TOOL_RESULT)
        sm.transition_to(State.EXECUTING_STEP)  # Další krok
        sm.transition_to(State.RESPONDING)
        sm.transition_to(State.COMPLETED)
        
        assert sm.get_state() == State.COMPLETED
        assert len(sm.state_history) == 6
    
    def test_error_recovery_path(self, temp_session_id):
        """Test: Přechody přes ERROR stav."""
        sm = StateManager(session_id=temp_session_id)
        
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.ERROR, "Something went wrong")
        sm.transition_to(State.REFLECTION, "Analyzing error")
        sm.transition_to(State.PLANNING, "Replanning")
        
        assert sm.get_state() == State.PLANNING
        
        # Zkontroluj že error je v historii
        error_transition = [t for t in sm.state_history if t["to"] == "error"]
        assert len(error_transition) == 1
        assert error_transition[0]["reason"] == "Something went wrong"
    
    def test_json_serialization_of_complex_data(self, temp_session_id):
        """Test: Komplexní data se správně serializují."""
        sm = StateManager(session_id=temp_session_id)
        
        complex_data = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "string": "test",
            "number": 42
        }
        
        sm.set_data("complex", complex_data)
        
        # Restore v nové instanci
        sm2 = StateManager(session_id=temp_session_id)
        sm2.restore()
        
        assert sm2.get_data("complex") == complex_data


class TestStateTransitionValidation:
    """
    Speciální testy pro edge cases ve validaci přechodů.
    """
    
    def test_all_states_have_transitions_defined(self):
        """Test: Každý stav má definované přechody v VALID_TRANSITIONS."""
        all_states = set(State)
        defined_states = set(StateManager.VALID_TRANSITIONS.keys())
        
        assert all_states == defined_states, (
            f"Tyto stavy nemají definované přechody: "
            f"{all_states - defined_states}"
        )
    
    def test_transition_error_message_is_helpful(self):
        """Test: Chybová zpráva obsahuje užitečné info."""
        sm = StateManager()
        
        try:
            sm.transition_to(State.COMPLETED, "Invalid")
        except StateTransitionError as e:
            error_msg = str(e)
            
            # Mělo by obsahovat oba stavy
            assert "idle" in error_msg.lower()
            assert "completed" in error_msg.lower()
            
            # Mělo by obsahovat povolené přechody
            assert "planning" in error_msg.lower()


# === EDGE CASE TESTY ===

class TestEdgeCases:
    """Testy pro krajní případy a error handling."""
    
    def test_corrupted_session_file_handling(self, tmp_path):
        """Test: Korumpovaný session soubor vyhodí výjimku."""
        # Vytvoř korumpovaný JSON soubor
        session_file = tmp_path / "session_corrupted.json"
        session_file.write_text("{ invalid json !!!")
        
        sm = StateManager(project_root=str(tmp_path), session_id="corrupted")
        
        with pytest.raises(json.JSONDecodeError):
            sm.restore()
    
    def test_session_file_with_invalid_state(self, tmp_path):
        """Test: Session s neplatným stavem vyhodí ValueError."""
        session_file = tmp_path / "session_invalid.json"
        invalid_snapshot = {
            "session_id": "invalid",
            "current_state": "nonexistent_state",
            "state_data": {},
            "state_history": [],
            "version": "1.0"
        }
        session_file.write_text(json.dumps(invalid_snapshot))
        
        sm = StateManager(project_root=str(tmp_path), session_id="invalid")
        
        with pytest.raises(ValueError) as exc_info:
            sm.restore()
        
        assert "neplatný stav" in str(exc_info.value).lower()
```

**Spuštění Testů:**

```bash
# Spusť všechny testy StateManager
cd /workspaces/sophia
python -m pytest tests/test_state_manager.py -v

# Očekávaný výstup: Všechny testy by měly projít (zelená)
```

**Očekávaný Výstup:**
```
tests/test_state_manager.py::TestStateManager::test_initial_state_is_idle PASSED
tests/test_state_manager.py::TestStateManager::test_valid_transition_succeeds PASSED
tests/test_state_manager.py::TestStateManager::test_invalid_transition_raises_error PASSED
tests/test_state_manager.py::TestStateManager::test_state_data_storage PASSED
tests/test_state_manager.py::TestStateManager::test_persistence_and_restore PASSED
tests/test_state_manager.py::TestStateManager::test_restore_nonexistent_session_returns_false PASSED
tests/test_state_manager.py::TestStateManager::test_state_history_records_transitions PASSED
tests/test_state_manager.py::TestStateManager::test_reset_clears_state PASSED
tests/test_state_manager.py::TestStateManager::test_get_state_summary PASSED
tests/test_state_manager.py::TestStateManager::test_complex_transition_chain PASSED
tests/test_state_manager.py::TestStateManager::test_error_recovery_path PASSED
tests/test_state_manager.py::TestStateManager::test_json_serialization_of_complex_data PASSED
tests/test_state_manager.py::TestStateTransitionValidation::test_all_states_have_transitions_defined PASSED
tests/test_state_manager.py::TestStateTransitionValidation::test_transition_error_message_is_helpful PASSED
tests/test_state_manager.py::TestEdgeCases::test_corrupted_session_file_handling PASSED
tests/test_state_manager.py::TestEdgeCases::test_session_file_with_invalid_state PASSED

======================== 16 passed in 0.XX s ========================
```

**❌ Fallback Strategie - Pokud Testy Selhávají:**

```bash
# 1. Identifikuj selhávající test
python -m pytest tests/test_state_manager.py -v --tb=short

# 2. Spusť pouze selhávající test pro debug
python -m pytest tests/test_state_manager.py::TestStateManager::test_<název> -v

# 3. Zkontroluj syntax StateManager
python -m py_compile core/state_manager.py

# 4. Pokud persist selhává, zkontroluj oprávnění:
ls -la memory/
# Mělo by být writable

# 5. Pokud více než 3 testy selhávají:
#    STOP! Neopravuj naslepo!
#    Zkontroluj CELÝ kód StateManager znovu
#    Porovnej s originálním kódem v REFACTORING_ROADMAP_V2.md
```

**✅ CHECKPOINT 1.4:** ✅ Všech 16 testů StateManager prošlo

---

### 1.5 Git Commit (13:00 - 13:15)

```bash
# Přidej změny do gitu
git add core/state_manager.py
git add tests/test_state_manager.py

# Commit s detailním popisem
git commit -m "feat(core): Implement StateManager with validation and persistence

- Add State enum with 8 states (IDLE, PLANNING, EXECUTING_STEP, etc.)
- Implement StateManager class with transition validation
- Add automatic persistence after each state change
- Add restore() for crash recovery
- Add 16 comprehensive unit tests
- All tests passing ✅

CHECKPOINT: 1.4 completed
"

# Verify commit
git log --oneline -1

# Push (volitelné, ale doporučené)
git push origin refactoring/nomad-v2-implementation
```

**✅ CHECKPOINT 1.5:** Git commit úspěšný, všechny soubory commitnuty

---

### 1.6 Dokumentace (13:15 - 13:30)

```bash
# Vytvoř dokumentaci pro StateManager
touch docs/STATE_MANAGER.md
```

```markdown
# Vlož do docs/STATE_MANAGER.md:

# StateManager - Technická Dokumentace

## Přehled

StateManager je jádro stavového stroje Nomáda. Spravuje všechny přechody mezi stavy s validací a automatickou persistence.

## Stavy

```
IDLE → PLANNING → EXECUTING_STEP → AWAITING_TOOL_RESULT → EXECUTING_STEP (loop)
   ↓                ↓                    ↓
ERROR          ERROR               REFLECTION → PLANNING (replanning)
   ↓                                   ↓
REFLECTION                        RESPONDING → COMPLETED → IDLE
```

## Použití

```python
from core.state_manager import StateManager, State

# Vytvoření instance
sm = StateManager()

# Přechod do nového stavu
sm.transition_to(State.PLANNING, "Starting mission")

# Uložení dat
sm.set_data("mission_goal", "Create hello.txt")

# Persistence je automatická!

# Recovery po pádu
sm2 = StateManager(session_id=sm.session_id)
if sm2.restore():
    print(f"Restored to {sm2.get_state()}")
```

## Kritické Vlastnosti

1. **Validace**: Každý přechod je kontrolován proti `VALID_TRANSITIONS`
2. **Atomická Persistence**: Zápis přes `.tmp` + `os.replace()`
3. **Crash Resilience**: Automatické ukládání po každé změně
4. **Historie**: Kompletní log všech přechodů

## Bezpečnostní Pravidla

- ❌ **NIKDY** neměň `current_state` přímo - použij `transition_to()`
- ❌ **NIKDY** neukládej ne-JSON-serializable data do `state_data`
- ✅ **VŽDY** zachyť `StateTransitionError` - indikuje BUG v kódu
- ✅ **VŽDY** kontroluj návratovou hodnotu `restore()`

## Přidání Nového Stavu

1. Přidej do `State` enum
2. Aktualizuj `VALID_TRANSITIONS`
3. Přidej test do `test_state_manager.py`
4. Spusť všechny testy

## Troubleshooting

**Q: StateTransitionError při legitimimím přechodu?**
A: Zkontroluj `VALID_TRANSITIONS` - možná chybí povolení

**Q: Restore() vrací False?**
A: Session soubor neexistuje nebo byl smazán

**Q: IOError při persist()?**
A: Zkontroluj oprávnění k `memory/` adresáři
```

```bash
# Commit dokumentace
git add docs/STATE_MANAGER.md
git commit -m "docs: Add StateManager technical documentation"
```

**✅ CHECKPOINT 1.6:** Dokumentace vytvořena a commitnuta

---

## 🏁 DEN 1 COMPLETED

**Validace Celého Dne:**

```bash
# Finální checklist
cd /workspaces/sophia

echo "=== DEN 1 CHECKLIST ===" > day1_validation.txt

# 1. Soubory existují?
echo "Files:" >> day1_validation.txt
ls -la core/state_manager.py >> day1_validation.txt
ls -la tests/test_state_manager.py >> day1_validation.txt
ls -la docs/STATE_MANAGER.md >> day1_validation.txt

# 2. Testy projdou?
echo -e "\n=== TESTS ===" >> day1_validation.txt
python -m pytest tests/test_state_manager.py -v >> day1_validation.txt 2>&1

# 3. Importy fungují?
echo -e "\n=== IMPORTS ===" >> day1_validation.txt
python -c "from core.state_manager import StateManager, State; print('✅ OK')" >> day1_validation.txt 2>&1

# 4. Git clean?
echo -e "\n=== GIT STATUS ===" >> day1_validation.txt
git status >> day1_validation.txt

# Zobraz výsledek
cat day1_validation.txt

# Mělo by obsahovat:
# - Všechny 3 soubory existují
# - 16 testů prošlo
# - Import ✅ OK
# - Git clean (nic uncommitted)
```

**✅ DEN 1 ÚSPĚŠNĚ DOKONČEN** pokud:
- [ ] Všechny soubory existují
- [ ] 16/16 testů prošlo
- [ ] Import funguje
- [ ] Git je clean
- [ ] Dokumentace existuje

**❌ Pokud cokoliv selhalo:**
1. Přečti si error message pečlivě
2. Zkontroluj konkrétní krok kde selhal
3. Použij rollback strategie z začátku dokumentu
4. **NEOPRAVUJ NASLEPO** - zanalyzuj problém
5. V nejhorším případě: `git reset --hard` k poslednímu fungujícímu commitu

---

## 📅 DEN 2: RecoveryManager - Crash Resilience

**Cíl:** Automatické obnovení po pádu orchestrátora.

**Časový Odhad:** 4-6 hodin  
**Riziko:** 🟡 STŘEDNÍ - Závisí na StateManager (který už funguje)

**Prerekvizity:**
```bash
# Ověř že Den 1 je dokončen
python -m pytest tests/test_state_manager.py -v
# Mělo by projít 16/16 testů
```

### 2.1 Implementace RecoveryManager (9:00 - 11:00)

```bash
# Vytvoř soubory
touch core/recovery_manager.py
touch tests/test_recovery_manager.py
```

```python
# Vlož do core/recovery_manager.py:

import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from core.state_manager import StateManager, State
from core.rich_printer import RichPrinter


class RecoveryManager:
    """
    Spravuje obnovu po pádu orchestrátora.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Automaticky detekuje nedokončené session soubory
    - Provádí recovery podle stavu kde orchestrátor spadl
    - Loguje recovery operace pro audit
    
    BEZPEČNOSTNÍ PRAVIDLA:
    - NIKDY nesmaže session soubor během recovery
    - Pokud recovery selže, zachová původní stav
    - Všechny recovery operace jsou logovány
    """
    
    def __init__(self, project_root: str = "."):
        """
        Inicializuje RecoveryManager.
        
        Args:
            project_root: Absolutní cesta k projektu
        """
        self.project_root = os.path.abspath(project_root)
        self.memory_dir = os.path.join(project_root, "memory")
        self.recovery_log: List[Dict[str, Any]] = []
    
    def find_crashed_sessions(self) -> List[str]:
        """
        Najde všechny session soubory, které nebyly dokončeny.
        
        KRITÉRIUM PRO "CRASHED":
        - Session existuje na disku
        - current_state NENÍ v [IDLE, COMPLETED]
        
        Returns:
            Seznam session_id, které jsou in-flight (nedokončené)
        """
        crashed = []
        
        if not os.path.exists(self.memory_dir):
            RichPrinter.info("Memory directory neexistuje - žádné crashed sessions")
            return crashed
        
        # Najdi všechny session soubory
        session_files = [
            f for f in os.listdir(self.memory_dir)
            if f.startswith("session_") and f.endswith(".json")
        ]
        
        RichPrinter.info(f"Nalezeno {len(session_files)} session souborů, kontroluji...")
        
        for filename in session_files:
            # Extrahuj session_id z názvu souboru
            # Formát: session_<session_id>.json
            session_id = filename.replace("session_", "").replace(".json", "")
            
            try:
                sm = StateManager(self.project_root, session_id)
                
                if sm.restore():
                    state = sm.get_state()
                    
                    # Jakýkoli stav kromě IDLE/COMPLETED = crashed
                    if state not in [State.IDLE, State.COMPLETED]:
                        crashed.append(session_id)
                        RichPrinter.warning(
                            f"   ⚠️  Session {session_id} crashed in state: {state.value}"
                        )
                    else:
                        RichPrinter.info(
                            f"   ✅ Session {session_id} dokončen ({state.value})"
                        )
            
            except Exception as e:
                RichPrinter.error(
                    f"   ❌ Nelze načíst session {session_id}: {e}"
                )
                # Pokračuj v kontrole dalších
                continue
        
        return crashed
    
    def recover_session(self, session_id: str) -> Optional[StateManager]:
        """
        Pokusí se obnovit spadnuté sezení.
        
        RECOVERY STRATEGIE podle stavu:
        - PLANNING: Restart plánování
        - EXECUTING_STEP: Pokus o retry kroku
        - AWAITING_TOOL_RESULT: Přechod do reflexe
        - REFLECTION: Pokračuj v reflexi
        - ERROR: Přechod do reflexe pro analýzu
        
        Args:
            session_id: ID sezení k obnově
        
        Returns:
            StateManager s obnoveným stavem, nebo None pokud recovery selhalo
        """
        RichPrinter.info(f"🔧 Zahajuji recovery pro session: {session_id}")
        
        sm = StateManager(self.project_root, session_id)
        
        # Pokus o restore
        if not sm.restore():
            RichPrinter.error(f"❌ Nelze obnovit session {session_id} - soubor nenalezen")
            return None
        
        current_state = sm.get_state()
        state_data = sm.get_data("mission_goal", "Neznámý cíl")
        
        RichPrinter.info(f"   📊 Stav před pádem: {current_state.value}")
        RichPrinter.info(f"   🎯 Mission: {state_data}")
        RichPrinter.info(f"   📜 Historie přechodů: {len(sm.state_history)}")
        
        # Zaloguj recovery
        self._log_recovery(session_id, current_state, "started")
        
        # Dispatch recovery strategie podle stavu
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
                self._log_recovery(session_id, current_state, "success")
                RichPrinter.info(f"✅ Recovery dokončen, nový stav: {sm.get_state().value}")
            except Exception as e:
                RichPrinter.error(f"❌ Recovery selhal: {e}")
                self._log_recovery(session_id, current_state, "failed", error=str(e))
                return None
        else:
            RichPrinter.error(f"❌ Nepodporovaný stav pro recovery: {current_state.value}")
            return None
        
        return sm
    
    def _recover_from_planning(self, sm: StateManager):
        """
        Recovery strategie: Spadl během plánování.
        
        ROZHODNUTÍ: Restart plánování od začátku je bezpečné
        """
        RichPrinter.info("♻️  Recovery strategie: Restart plánování")
        
        # Force reset na IDLE (musíme obejít validaci)
        sm.current_state = State.IDLE
        sm.persist()
        
        # Nyní můžeme přejít zpět do PLANNING
        sm.transition_to(State.PLANNING, "Recovery: restarting planning after crash")
    
    def _recover_from_executing(self, sm: StateManager):
        """
        Recovery strategie: Spadl během provádění kroku.
        
        ROZHODNUTÍ:
        - Pokud byl tool_call uložen → můžeme ho zkusit znovu
        - Pokud ne → přejdi na reflexi (něco se pokazilo)
        """
        pending_tool = sm.get_data("pending_tool_call")
        
        if pending_tool:
            tool_name = pending_tool.get("tool_name", "unknown")
            RichPrinter.info(
                f"♻️  Recovery strategie: Nalezen nedokončený tool call: {tool_name}"
            )
            RichPrinter.warning("   Orchestrátor se pokusí krok opakovat...")
            
            # Zůstaneme v EXECUTING_STEP - orchestrátor krok opakuje
            # (jen persist pro jistotu)
            sm.persist()
        else:
            RichPrinter.warning("⚠️  Žádný pending tool call → přechod do reflexe")
            
            # Force přechod přes validní cestu
            sm.current_state = State.AWAITING_TOOL_RESULT
            sm.persist()
            
            sm.transition_to(
                State.REFLECTION,
                "Recovery: no pending tool, analyzing what happened"
            )
    
    def _recover_from_awaiting_tool(self, sm: StateManager):
        """
        Recovery strategie: Spadl při čekání na výsledek nástroje.
        
        ROZHODNUTÍ: Tool pravděpodobně selhal nebo timeoutoval
        """
        RichPrinter.warning("⚠️  Recovery strategie: Tool execution interrupted")
        
        # Ulož info o crashed tool
        pending_tool = sm.get_data("pending_tool_call")
        if pending_tool:
            sm.set_data("crashed_tool", pending_tool)
        
        sm.transition_to(
            State.REFLECTION,
            "Recovery: tool execution was interrupted by crash"
        )
    
    def _recover_from_reflection(self, sm: StateManager):
        """
        Recovery strategie: Spadl během reflexe.
        
        ROZHODNUTÍ: Reflexe je bezpečná - můžeme pokračovat
        """
        RichPrinter.info("♻️  Recovery strategie: Pokračuj v reflexi")
        
        # Zůstáváme v REFLECTION, jen persist
        sm.persist()
        
        RichPrinter.info("   Orchestrátor pokračuje v analýze...")
    
    def _recover_from_responding(self, sm: StateManager):
        """
        Recovery strategie: Spadl během generování odpovědi.
        
        ROZHODNUTÍ: Zkus vygenerovat odpověď znovu
        """
        RichPrinter.info("♻️  Recovery strategie: Restart generování odpovědi")
        
        # Zůstaneme v RESPONDING
        sm.persist()
    
    def _recover_from_error(self, sm: StateManager):
        """
        Recovery strategie: Spadl v chybovém stavu.
        
        ROZHODNUTÍ: Přejdi do reflexe pro analýzu chyby
        """
        error_msg = sm.get_data("error_message", "Unknown error before crash")
        
        RichPrinter.error(f"❌ Recovery strategie: Analyzuji chybu před pádem")
        RichPrinter.error(f"   Error před pádem: {error_msg}")
        
        sm.transition_to(
            State.REFLECTION,
            "Recovery: analyzing error that caused crash"
        )
    
    def _log_recovery(
        self,
        session_id: str,
        state: State,
        status: str,
        error: Optional[str] = None
    ):
        """
        Zaloguje recovery operaci.
        
        POUŽITÍ: Pro audit a debugging
        """
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "crashed_state": state.value,
            "recovery_status": status,
            "error": error
        }
        
        self.recovery_log.append(log_entry)
        
        # Persist log (pro dlouhodobý audit)
        log_file = os.path.join(self.memory_dir, "recovery.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(log_entry) + "\n")
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """
        Vrátí statistiky recovery operací.
        
        POUŽITÍ: Pro monitoring a debugging
        """
        if not self.recovery_log:
            return {
                "total_recoveries": 0,
                "successful": 0,
                "failed": 0
            }
        
        successful = sum(1 for log in self.recovery_log if log["recovery_status"] == "success")
        failed = sum(1 for log in self.recovery_log if log["recovery_status"] == "failed")
        
        return {
            "total_recoveries": len(self.recovery_log),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.recovery_log) if self.recovery_log else 0
        }
```

**Validace:**

```bash
# Test importu
python -c "from core.recovery_manager import RecoveryManager; rm = RecoveryManager(); print('✅ Import OK')"
```

**✅ CHECKPOINT 2.1:** RecoveryManager se importuje bez chyby

---

### 2.2 Unit Testy RecoveryManager (11:00 - 13:00)

```python
# Vlož do tests/test_recovery_manager.py:

import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch

# Import cesty
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.recovery_manager import RecoveryManager
from core.state_manager import StateManager, State


class TestRecoveryManager:
    """Test suite pro RecoveryManager."""
    
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Fixture poskytující dočasný projekt root."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        return str(tmp_path)
    
    def test_find_crashed_sessions_empty_directory(self, temp_project_root):
        """Test: Prázdný memory adresář vrátí prázdný seznam."""
        rm = RecoveryManager(temp_project_root)
        crashed = rm.find_crashed_sessions()
        
        assert crashed == []
    
    def test_find_crashed_sessions_detects_incomplete(self, temp_project_root):
        """Test: Detekuje nedokončené sessions."""
        # Vytvoř crashed session (v PLANNING stavu)
        sm = StateManager(temp_project_root, session_id="crashed_1")
        sm.transition_to(State.PLANNING, "Starting")
        
        # RecoveryManager by měl najít
        rm = RecoveryManager(temp_project_root)
        crashed = rm.find_crashed_sessions()
        
        assert "crashed_1" in crashed
        
        # Cleanup
        sm.delete_session()
    
    def test_find_crashed_sessions_ignores_completed(self, temp_project_root):
        """Test: Ignoruje dokončené sessions."""
        # Vytvoř dokončenou session
        sm = StateManager(temp_project_root, session_id="completed_1")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.RESPONDING)
        sm.transition_to(State.COMPLETED)
        
        # RecoveryManager by ji neměl zahrnout
        rm = RecoveryManager(temp_project_root)
        crashed = rm.find_crashed_sessions()
        
        assert "completed_1" not in crashed
        
        # Cleanup
        sm.delete_session()
    
    def test_recover_from_planning_state(self, temp_project_root):
        """Test: Recovery z PLANNING stavu restartuje plánování."""
        # Simuluj pád v PLANNING
        sm = StateManager(temp_project_root, session_id="plan_crash")
        sm.transition_to(State.PLANNING, "Creating plan")
        sm.set_data("mission_goal", "Test mission")
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        recovered_sm = rm.recover_session("plan_crash")
        
        assert recovered_sm is not None
        assert recovered_sm.get_state() == State.PLANNING
        assert recovered_sm.get_data("mission_goal") == "Test mission"
        
        # Cleanup
        recovered_sm.delete_session()
    
    def test_recover_from_executing_with_pending_tool(self, temp_project_root):
        """Test: Recovery z EXECUTING s pending tool call."""
        # Simuluj pád během exekuce s pending tool
        sm = StateManager(temp_project_root, session_id="exec_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        sm.set_data("pending_tool_call", {"tool_name": "test_tool", "args": []})
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        recovered_sm = rm.recover_session("exec_crash")
        
        assert recovered_sm is not None
        # Měl by zůstat v EXECUTING_STEP pro retry
        assert recovered_sm.get_state() == State.EXECUTING_STEP
        assert recovered_sm.get_data("pending_tool_call") is not None
        
        # Cleanup
        recovered_sm.delete_session()
    
    def test_recover_from_executing_without_pending_tool(self, temp_project_root):
        """Test: Recovery z EXECUTING bez pending tool → REFLECTION."""
        # Simuluj pád během exekuce BEZ pending tool
        sm = StateManager(temp_project_root, session_id="exec_no_tool")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        # Žádný pending_tool_call!
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        recovered_sm = rm.recover_session("exec_no_tool")
        
        assert recovered_sm is not None
        # Měl by přejít do REFLECTION
        assert recovered_sm.get_state() == State.REFLECTION
        
        # Cleanup
        recovered_sm.delete_session()
    
    def test_recover_from_awaiting_tool(self, temp_project_root):
        """Test: Recovery z AWAITING_TOOL_RESULT."""
        # Simuluj pád při čekání na tool
        sm = StateManager(temp_project_root, session_id="await_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        sm.transition_to(State.AWAITING_TOOL_RESULT)
        sm.set_data("pending_tool_call", {"tool_name": "crashed_tool"})
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        recovered_sm = rm.recover_session("await_crash")
        
        assert recovered_sm is not None
        # Měl by přejít do REFLECTION
        assert recovered_sm.get_state() == State.REFLECTION
        # Crashed tool by měl být uložen
        assert recovered_sm.get_data("crashed_tool") is not None
        
        # Cleanup
        recovered_sm.delete_session()
    
    def test_recover_from_error_state(self, temp_project_root):
        """Test: Recovery z ERROR stavu."""
        # Simuluj pád v ERROR stavu
        sm = StateManager(temp_project_root, session_id="error_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.ERROR, "Test error")
        sm.set_data("error_message", "Critical failure")
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        recovered_sm = rm.recover_session("error_crash")
        
        assert recovered_sm is not None
        # Měl by přejít do REFLECTION pro analýzu
        assert recovered_sm.get_state() == State.REFLECTION
        
        # Cleanup
        recovered_sm.delete_session()
    
    def test_recovery_logging(self, temp_project_root):
        """Test: Recovery operace se logují."""
        # Vytvoř crashed session
        sm = StateManager(temp_project_root, session_id="log_test")
        sm.transition_to(State.PLANNING)
        
        # Recovery
        rm = RecoveryManager(temp_project_root)
        rm.recover_session("log_test")
        
        # Zkontroluj log
        assert len(rm.recovery_log) > 0
        assert rm.recovery_log[0]["session_id"] == "log_test"
        assert rm.recovery_log[0]["crashed_state"] == "planning"
        
        # Zkontroluj recovery.log soubor
        log_file = os.path.join(temp_project_root, "memory", "recovery.log")
        assert os.path.exists(log_file)
        
        # Cleanup
        sm_cleanup = StateManager(temp_project_root, session_id="log_test")
        sm_cleanup.delete_session()
    
    def test_get_recovery_stats(self, temp_project_root):
        """Test: Statistiky recovery operací."""
        rm = RecoveryManager(temp_project_root)
        
        # Vytvoř a recover několik sessions
        for i in range(3):
            sm = StateManager(temp_project_root, session_id=f"stats_{i}")
            sm.transition_to(State.PLANNING)
            rm.recover_session(f"stats_{i}")
            sm.delete_session()
        
        stats = rm.get_recovery_stats()
        
        assert stats["total_recoveries"] == 3
        assert stats["successful"] == 3
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0
    
    def test_recover_nonexistent_session(self, temp_project_root):
        """Test: Recovery neexistující session vrátí None."""
        rm = RecoveryManager(temp_project_root)
        result = rm.recover_session("nonexistent_123")
        
        assert result is None


class TestRecoveryIntegration:
    """Integrační testy pro recovery scénáře."""
    
    def test_full_crash_and_recovery_cycle(self, tmp_path):
        """Test: Kompletní crash + recovery cyklus."""
        project_root = str(tmp_path)
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        # FÁZE 1: Simuluj běžící orchestrátor
        sm1 = StateManager(project_root, session_id="full_cycle")
        sm1.set_data("mission_goal", "Critical task")
        sm1.transition_to(State.PLANNING)
        sm1.transition_to(State.EXECUTING_STEP)
        sm1.set_data("current_step", 3)
        
        # FÁZE 2: "Pád" - instance je garbage collected
        session_id = sm1.session_id
        del sm1
        
        # FÁZE 3: Recovery manager detekuje pád
        rm = RecoveryManager(project_root)
        crashed_sessions = rm.find_crashed_sessions()
        
        assert session_id in crashed_sessions
        
        # FÁZE 4: Obnov session
        recovered = rm.recover_session(session_id)
        
        assert recovered is not None
        assert recovered.get_data("mission_goal") == "Critical task"
        assert recovered.get_data("current_step") == 3
        
        # Cleanup
        recovered.delete_session()
```

**Spuštění Testů:**

```bash
# Spusť všechny testy RecoveryManager
python -m pytest tests/test_recovery_manager.py -v

# Očekávaný výstup: Všechny testy zelené
```

**✅ CHECKPOINT 2.2:** ✅ Všech 12 testů RecoveryManager prošlo

---

### 2.3 Integrace s RichPrinter (13:00 - 13:30)

**Poznámka:** RecoveryManager používá `RichPrinter.info/warning/error`. Ověřme že funguje:

```bash
# Test s real RichPrinter
python -c "
from core.recovery_manager import RecoveryManager
from core.state_manager import StateManager, State

# Vytvoř crashed session
sm = StateManager(session_id='test_rich')
sm.transition_to(State.PLANNING)

# Recovery s output
rm = RecoveryManager()
result = rm.recover_session('test_rich')

# Cleanup
result.delete_session()
print('✅ RichPrinter integration OK')
"

# Měl by vypsat barevný output s ♻️ emoji
```

**✅ CHECKPOINT 2.3:** RichPrinter integrace funguje

---

### 2.4 Git Commit (13:30 - 13:45)

```bash
git add core/recovery_manager.py
git add tests/test_recovery_manager.py

git commit -m "feat(core): Implement RecoveryManager for crash resilience

- Add RecoveryManager class with crash detection
- Implement recovery strategies for each state
- Add automatic recovery logging to recovery.log
- Add 12 comprehensive unit tests + integration test
- All tests passing ✅

CHECKPOINT: 2.4 completed
Dependencies: StateManager (Day 1)
"

git push origin refactoring/nomad-v2-implementation
```

**✅ CHECKPOINT 2.4:** RecoveryManager commitnut

---

## 🏁 DEN 2 COMPLETED

**Validace:**

```bash
# Checklist
python -m pytest tests/test_state_manager.py tests/test_recovery_manager.py -v

# Mělo by projít: 16 + 12 = 28 testů
```

**✅ DEN 2 ÚSPĚŠNĚ DOKONČEN** pokud:
- [ ] 12/12 testů RecoveryManager prošlo
- [ ] 28/28 celkových testů prošlo
- [ ] Git commit úspěšný
- [ ] RichPrinter integrace funguje

---

---

## 📅 DEN 3-4: PlanManager - Proaktivní Plánování

**Cíl:** Transformovat reaktivní loop na proaktivní exekuci plánu.

**Časový Odhad:** 8-10 hodin (2 dny)  
**Riziko:** 🔴 VYSOKÉ - Vyžaduje LLM integraci, složitá logika

**Prerekvizity:**
```bash
# Ověř předchozí komponenty
python -m pytest tests/test_state_manager.py tests/test_recovery_manager.py -v
# 28/28 testů
```

### 3.1 Implementace PlanStep DataClass (Den 3, 9:00 - 9:30)

```bash
touch core/plan_manager.py
touch tests/test_plan_manager.py
```

```python
# Vlož do core/plan_manager.py:

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

from core.llm_manager import LLMManager
from core.rich_printer import RichPrinter


@dataclass
class PlanStep:
    """
    Reprezentuje jeden krok v plánu.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Immutable po vytvoření (pouze status a result se mění)
    - Dependency tracking pro paralelizaci (budoucnost)
    - Token estimation pro budget management
    """
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed, skipped
    dependencies: List[int] = field(default_factory=list)
    estimated_tokens: int = 0
    actual_tokens: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    attempt_count: int = 0
    
    def __post_init__(self):
        """Validace po vytvoření."""
        valid_statuses = ["pending", "in_progress", "completed", "failed", "skipped"]
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. Must be one of {valid_statuses}"
            )
        
        if self.id < 1:
            raise ValueError(f"Step ID must be >= 1, got {self.id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize do dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "dependencies": self.dependencies,
            "estimated_tokens": self.estimated_tokens,
            "actual_tokens": self.actual_tokens,
            "result": self.result,
            "error": self.error,
            "attempt_count": self.attempt_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanStep':
        """Deserialize z dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            status=data.get("status", "pending"),
            dependencies=data.get("dependencies", []),
            estimated_tokens=data.get("estimated_tokens", 0),
            actual_tokens=data.get("actual_tokens", 0),
            result=data.get("result"),
            error=data.get("error"),
            attempt_count=data.get("attempt_count", 0)
        )
```

**Validace:**

```bash
python -c "
from core.plan_manager import PlanStep

step = PlanStep(id=1, description='Test step')
assert step.status == 'pending'
assert step.dependencies == []

print('✅ PlanStep OK')
"
```

**✅ CHECKPOINT 3.1:** PlanStep se importuje a vytváří

---

### 3.2 Implementace PlanManager (Den 3, 9:30 - 12:00)

```python
# Pokračuj v core/plan_manager.py:

class PlanManager:
    """
    Spravuje plán mise - vytváření, sledování, aktualizace.
    
    KLÍČOVÉ VLASTNOSTI:
    - LLM-based plánování (použije powerful model)
    - Dependency tracking (krok může čekat na jiný krok)
    - Progress tracking
    - Re-planning support
    """
    
    def __init__(self, llm_manager: LLMManager, project_root: str = "."):
        """
        Inicializuje PlanManager.
        
        Args:
            llm_manager: Instance LLMManager pro volání LLM
            project_root: Cesta k projektu
        """
        self.llm_manager = llm_manager
        self.project_root = project_root
        self.steps: List[PlanStep] = []
        self.current_step_index = 0
        self.plan_created_at: Optional[str] = None
    
    async def create_plan(
        self,
        mission_goal: str,
        context: str = "",
        max_steps: int = 10
    ) -> List[PlanStep]:
        """
        Vytvoří plán pro daný cíl mise pomocí LLM.
        
        Args:
            mission_goal: Cíl mise (např. "Create file hello.txt")
            context: Dodatečný kontext (volitelné)
            max_steps: Maximum kroků v plánu
        
        Returns:
            Seznam PlanStep objektů
        
        Raises:
            json.JSONDecodeError: Pokud LLM nevygeneruje platný JSON
            ValueError: Pokud plán je neplatný
        """
        RichPrinter.info("📋 Vytvářím plán mise...")
        
        planning_prompt = self._build_planning_prompt(
            mission_goal, context, max_steps
        )
        
        # Použij powerful model pro plánování
        model = self.llm_manager.get_llm("powerful")
        response, usage = await model.generate_content_async(planning_prompt)
        
        # Parse JSON z odpovědi
        plan_data = self._parse_plan_from_response(response)
        
        # Validace plánu
        self._validate_plan(plan_data)
        
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
        
        self.plan_created_at = datetime.now().isoformat()
        self.current_step_index = 0
        
        # Zobraz plán
        self._display_plan()
        
        return self.steps
    
    def _build_planning_prompt(
        self,
        mission_goal: str,
        context: str,
        max_steps: int
    ) -> str:
        """Sestaví prompt pro LLM plánování."""
        return f"""Jsi strategický plánovač pro AI agenta Nomáda.

ÚKOL:
{mission_goal}

KONTEXT:
{context if context else 'Žádný dodatečný kontext.'}

TVŮJ ÚKOL:
Rozlož tento úkol na konkrétní, proveditelné kroky.

POŽADAVKY:
1. Každý krok MUSÍ být atomický (jedna jasná akce)
2. Každý krok MUSÍ být testovatelný (víme kdy je hotový)
3. Kroky MUSÍ být seřazeny logicky
4. Respektuj závislosti mezi kroky (pokud krok B potřebuje výsledek kroku A, přidej závislost)
5. Maximálně {max_steps} kroků
6. Odhadni složitost každého kroku v tokenech (100-2000)

FORMÁT ODPOVĚDI (striktní JSON):
```json
{{
  "steps": [
    {{
      "id": 1,
      "description": "Konkrétní akce kterou agent provede",
      "dependencies": [],
      "estimated_tokens": 500
    }},
    {{
      "id": 2,
      "description": "Další akce (může záviset na kroku 1)",
      "dependencies": [1],
      "estimated_tokens": 300
    }}
  ]
}}
```

PŘÍKLAD DOBÉHO PLÁNU:
Úkol: "Vytvoř soubor test.txt s obsahem 'Hello World'"

```json
{{
  "steps": [
    {{
      "id": 1,
      "description": "Zkontroluj zda soubor test.txt již neexistuje",
      "dependencies": [],
      "estimated_tokens": 200
    }},
    {{
      "id": 2,
      "description": "Vytvoř soubor test.txt s obsahem 'Hello World'",
      "dependencies": [1],
      "estimated_tokens": 300
    }},
    {{
      "id": 3,
      "description": "Ověř že soubor byl vytvořen správně",
      "dependencies": [2],
      "estimated_tokens": 200
    }}
  ]
}}
```

Nyní vytvoř plán pro zadaný úkol. Odpověz POUZE JSON, nic jiného!
"""
    
    def _parse_plan_from_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON plán z LLM odpovědi.
        
        Podporuje:
        - JSON v ```json``` blocích
        - Plain JSON
        - JSON s okolním textem
        """
        # Zkus najít JSON v code blocku
        json_match = re.search(
            r'```json\s*(.*?)\s*```',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Zkus parsovat celou odpověď jako JSON
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            RichPrinter.error("❌ LLM nevygeneroval platný JSON plán")
            RichPrinter.error(f"Response: {response[:500]}...")
            raise ValueError(f"Invalid plan JSON: {e}")
    
    def _validate_plan(self, plan_data: Dict[str, Any]):
        """
        Validuje strukturu plánu.
        
        Kontroly:
        - steps pole existuje
        - Každý krok má id, description
        - IDs jsou unique
        - Dependencies odkazují na existující kroky
        """
        if "steps" not in plan_data:
            raise ValueError("Plán nemá pole 'steps'")
        
        steps = plan_data["steps"]
        if not steps:
            raise ValueError("Plán je prázdný")
        
        # Zkontroluj unique IDs
        ids = [s["id"] for s in steps]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Plán obsahuje duplicitní IDs: {ids}")
        
        # Zkontroluj dependencies
        for step in steps:
            for dep_id in step.get("dependencies", []):
                if dep_id not in ids:
                    raise ValueError(
                        f"Krok {step['id']} má neplatnou závislost: {dep_id}"
                    )
    
    def _display_plan(self):
        """Zobrazí plán v konzoli."""
        RichPrinter.info("✅ Plán vytvořen:")
        
        total_tokens = sum(s.estimated_tokens for s in self.steps)
        
        for step in self.steps:
            deps_str = ""
            if step.dependencies:
                deps_str = f" [závislosti: {', '.join(map(str, step.dependencies))}]"
            
            RichPrinter.info(
                f"   {step.id}. {step.description} "
                f"(~{step.estimated_tokens} tokens){deps_str}"
            )
        
        RichPrinter.info(f"   Celkem: {len(self.steps)} kroků, ~{total_tokens} tokenů")
    
    def get_next_step(self) -> Optional[PlanStep]:
        """
        Vrátí další krok k provedení.
        
        Logika:
        - Najde první "pending" krok
        - Zkontroluje že závislosti jsou "completed"
        
        Returns:
            PlanStep nebo None pokud žádný dostupný
        """
        for step in self.steps:
            if step.status == "pending":
                # Zkontroluj závislosti
                if self._are_dependencies_met(step):
                    return step
        
        return None  # Žádný dostupný krok
    
    def _are_dependencies_met(self, step: PlanStep) -> bool:
        """Zkontroluje zda jsou splněny závislosti kroku."""
        for dep_id in step.dependencies:
            dep_step = self._get_step_by_id(dep_id)
            if dep_step and dep_step.status != "completed":
                return False
        return True
    
    def mark_step_in_progress(self, step_id: int):
        """Označí krok jako probíhající."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "in_progress"
            step.attempt_count += 1
            RichPrinter.info(
                f"▶️  Krok {step_id} (pokus #{step.attempt_count}): {step.description}"
            )
    
    def mark_step_completed(
        self,
        step_id: int,
        result: str,
        tokens_used: int = 0
    ):
        """Označí krok jako dokončený."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "completed"
            step.result = result
            step.actual_tokens = tokens_used
            RichPrinter.info(f"✅ Krok {step_id} dokončen (použito {tokens_used} tokenů)")
    
    def mark_step_failed(self, step_id: int, error: str):
        """Označí krok jako selhavší."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "failed"
            step.error = error
            RichPrinter.error(f"❌ Krok {step_id} selhal: {error}")
    
    def mark_step_skipped(self, step_id: int, reason: str):
        """Označí krok jako přeskočený."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "skipped"
            step.error = reason
            RichPrinter.warning(f"⏭️  Krok {step_id} přeskočen: {reason}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Vrátí statistiky pokroku."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == "completed")
        failed = sum(1 for s in self.steps if s.status == "failed")
        skipped = sum(1 for s in self.steps if s.status == "skipped")
        in_progress = sum(1 for s in self.steps if s.status == "in_progress")
        
        return {
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "in_progress": in_progress,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }
    
    def is_plan_complete(self) -> bool:
        """True pokud jsou všechny kroky dokončeny nebo přeskočeny."""
        return all(
            s.status in ["completed", "skipped"]
            for s in self.steps
        )
    
    def _get_step_by_id(self, step_id: int) -> Optional[PlanStep]:
        """Najde krok podle ID."""
        return next((s for s in self.steps if s.id == step_id), None)
    
    def serialize(self) -> Dict[str, Any]:
        """Serializuje plán do JSON-friendly formátu."""
        return {
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "plan_created_at": self.plan_created_at
        }
    
    @classmethod
    def deserialize(
        cls,
        data: Dict[str, Any],
        llm_manager: LLMManager,
        project_root: str = "."
    ) -> 'PlanManager':
        """Obnoví PlanManager ze serializované podoby."""
        pm = cls(llm_manager, project_root)
        pm.steps = [PlanStep.from_dict(s) for s in data["steps"]]
        pm.current_step_index = data["current_step_index"]
        pm.plan_created_at = data.get("plan_created_at")
        return pm
```

**Validace:**

```bash
python -c "
from core.plan_manager import PlanManager, PlanStep
from core.llm_manager import LLMManager

llm_mgr = LLMManager()
pm = PlanManager(llm_mgr)

# Test manuální vytvoření plánu
pm.steps = [
    PlanStep(id=1, description='Step 1'),
    PlanStep(id=2, description='Step 2', dependencies=[1])
]

next_step = pm.get_next_step()
assert next_step.id == 1

print('✅ PlanManager basic logic OK')
"
```

**✅ CHECKPOINT 3.2:** PlanManager základní logika funguje

---

### 3.3 Unit Testy PlanManager (Den 3-4, 13:00 - 17:00)

*(Kompletní test suite je dlouhá - zkrácená verze níže, plná v samostatném souboru)*

```python
# Vlož do tests/test_plan_manager.py:

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.plan_manager import PlanManager, PlanStep
from core.llm_manager import LLMManager


class TestPlanStep:
    """Testy pro PlanStep dataclass."""
    
    def test_create_plan_step(self):
        """Test: Vytvoření základního kroku."""
        step = PlanStep(id=1, description="Test step")
        
        assert step.id == 1
        assert step.description == "Test step"
        assert step.status == "pending"
        assert step.dependencies == []
    
    def test_invalid_status_raises_error(self):
        """Test: Neplatný status vyhodí ValueError."""
        with pytest.raises(ValueError):
            PlanStep(id=1, description="Test", status="invalid_status")
    
    def test_step_serialization(self):
        """Test: Serializace a deserializace kroku."""
        step = PlanStep(
            id=1,
            description="Test",
            dependencies=[2, 3],
            estimated_tokens=500
        )
        
        data = step.to_dict()
        restored = PlanStep.from_dict(data)
        
        assert restored.id == step.id
        assert restored.dependencies == step.dependencies


class TestPlanManagerBasic:
    """Základní testy PlanManager (bez LLM)."""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLMManager."""
        return MagicMock(spec=LLMManager)
    
    def test_create_plan_manager(self, mock_llm_manager):
        """Test: Vytvoření PlanManager instance."""
        pm = PlanManager(mock_llm_manager)
        
        assert pm.steps == []
        assert pm.current_step_index == 0
    
    def test_get_next_step_simple(self, mock_llm_manager):
        """Test: get_next_step vrátí první pending krok."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [
            PlanStep(id=1, description="Step 1"),
            PlanStep(id=2, description="Step 2")
        ]
        
        next_step = pm.get_next_step()
        
        assert next_step is not None
        assert next_step.id == 1
    
    def test_get_next_step_with_dependencies(self, mock_llm_manager):
        """Test: get_next_step respektuje závislosti."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [
            PlanStep(id=1, description="Step 1"),
            PlanStep(id=2, description="Step 2", dependencies=[1])
        ]
        
        # Krok 2 má závislost na 1, takže next = 1
        next_step = pm.get_next_step()
        assert next_step.id == 1
        
        # Dokončíme krok 1
        pm.mark_step_completed(1, "Done", 100)
        
        # Nyní by měl být dostupný krok 2
        next_step = pm.get_next_step()
        assert next_step.id == 2
    
    def test_mark_step_completed(self, mock_llm_manager):
        """Test: Označení kroku jako dokončeného."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [PlanStep(id=1, description="Step 1")]
        
        pm.mark_step_completed(1, "Result data", tokens_used=250)
        
        step = pm._get_step_by_id(1)
        assert step.status == "completed"
        assert step.result == "Result data"
        assert step.actual_tokens == 250
    
    def test_progress_calculation(self, mock_llm_manager):
        """Test: Výpočet pokroku plánu."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [
            PlanStep(id=1, description="Step 1"),
            PlanStep(id=2, description="Step 2"),
            PlanStep(id=3, description="Step 3")
        ]
        
        pm.mark_step_completed(1, "Done", 0)
        pm.mark_step_failed(2, "Error")
        
        progress = pm.get_progress()
        
        assert progress["total_steps"] == 3
        assert progress["completed"] == 1
        assert progress["failed"] == 1
        assert progress["progress_percent"] == pytest.approx(33.33, rel=0.1)
    
    def test_is_plan_complete(self, mock_llm_manager):
        """Test: Detekce dokončení plánu."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [
            PlanStep(id=1, description="Step 1"),
            PlanStep(id=2, description="Step 2")
        ]
        
        assert pm.is_plan_complete() == False
        
        pm.mark_step_completed(1, "Done", 0)
        assert pm.is_plan_complete() == False
        
        pm.mark_step_completed(2, "Done", 0)
        assert pm.is_plan_complete() == True
    
    def test_serialization(self, mock_llm_manager):
        """Test: Serializace a deserializace celého plánu."""
        pm = PlanManager(mock_llm_manager)
        pm.steps = [
            PlanStep(id=1, description="Step 1"),
            PlanStep(id=2, description="Step 2", dependencies=[1])
        ]
        pm.mark_step_completed(1, "Done", 100)
        
        # Serialize
        data = pm.serialize()
        
        # Deserialize
        pm2 = PlanManager.deserialize(data, mock_llm_manager)
        
        assert len(pm2.steps) == 2
        assert pm2.steps[0].status == "completed"
        assert pm2.steps[1].dependencies == [1]


@pytest.mark.asyncio
class TestPlanManagerWithLLM:
    """Testy s reálným LLM voláním (vyžaduje API key)."""
    
    @pytest.fixture
    def llm_manager(self):
        """Reálný LLMManager."""
        try:
            return LLMManager()
        except Exception as e:
            pytest.skip(f"LLMManager init failed: {e}")
    
    async def test_create_plan_simple_task(self, llm_manager):
        """Test: Vytvoření plánu pro jednoduchý úkol."""
        pm = PlanManager(llm_manager)
        
        plan = await pm.create_plan(
            mission_goal="Vytvoř soubor hello.txt s obsahem 'Hello World'",
            max_steps=5
        )
        
        assert len(plan) > 0
        assert len(plan) <= 5
        assert all(isinstance(s, PlanStep) for s in plan)
        
        # Zkontroluj že kroky mají popisky
        assert all(s.description for s in plan)
    
    async def test_create_plan_with_dependencies(self, llm_manager):
        """Test: LLM vytvoří plán s závislostmi."""
        pm = PlanManager(llm_manager)
        
        plan = await pm.create_plan(
            mission_goal="Přečti soubor config.yaml, parsuj ho a vytvoř summary.txt",
            max_steps=6
        )
        
        # Měly by existovat některé závislosti
        has_dependencies = any(s.dependencies for s in plan)
        assert has_dependencies, "Plan by měl mít nějaké závislosti mezi kroky"


# Spusť testy bez LLM:
# pytest tests/test_plan_manager.py::TestPlanStep -v
# pytest tests/test_plan_manager.py::TestPlanManagerBasic -v

# Spusť testy s LLM (vyžaduje API key):
# pytest tests/test_plan_manager.py::TestPlanManagerWithLLM -v
```

**Spuštění Testů:**

```bash
# Bez LLM (rychlé)
python -m pytest tests/test_plan_manager.py::TestPlanStep -v
python -m pytest tests/test_plan_manager.py::TestPlanManagerBasic -v

# S LLM (vyžaduje OPENROUTER_API_KEY v .env)
python -m pytest tests/test_plan_manager.py::TestPlanManagerWithLLM -v

# Očekávaný výstup: Všechny testy zelené
```

**✅ CHECKPOINT 3.3:** ✅ Testy PlanManager prošly

---

### 3.4 Git Commit (Den 4, 13:00)

```bash
git add core/plan_manager.py
git add tests/test_plan_manager.py

git commit -m "feat(core): Implement PlanManager for proactive planning

- Add PlanStep dataclass with dependency tracking
- Implement PlanManager with LLM-based plan generation
- Add progress tracking and serialization
- Add 10+ unit tests (basic + LLM integration)
- All tests passing ✅

CHECKPOINT: 3.4 completed
Dependencies: LLMManager, StateManager
"

git push origin refactoring/nomad-v2-implementation
```

**✅ CHECKPOINT 3.4:** PlanManager commitnut

---

## 🏁 DEN 3-4 COMPLETED

**Validace:**

```bash
# Celkové testy
python -m pytest tests/ -v -k "not LLM"  # Bez LLM testů

# Mělo by projít: 28 (StateManager + Recovery) + 10 (PlanManager) = 38 testů
```

---

## 📅 DEN 5-6: ReflectionEngine - Učení z Chyb

*(Pokračuje implementace dalších komponent...)*

**Struktura zůstává stejná:**
1. Implementace komponenty
2. Unit testy
3. Validace
4. Git commit

---

## 📅 DEN 7: BudgetTracker

*(Pokračuje...)*

---

## 📅 DEN 8-10: NomadOrchestratorV2 - Integrace

*(Pokračuje s integrací všech komponent...)*

---

## 📅 DEN 11-12: E2E Testy + Migrace

**Cíl:** Kompletní end-to-end testy a migrace z JulesOrchestrator.

### 11.1 E2E Test Scénáře

```bash
touch tests/test_e2e_nomad_v2.py
```

### 11.2 Side-by-Side Provoz

```python
# main.py bude podporovat oba orchestrátory:

import argparse

parser.add_argument(
    "--orchestrator",
    choices=["jules", "nomad_v2"],
    default="jules",
    help="Který orchestrátor použít"
)

if args.orchestrator == "nomad_v2":
    from core.orchestrator_v2 import NomadOrchestratorV2
    orch = NomadOrchestratorV2()
else:
    from core.orchestrator import JulesOrchestrator
    orch = JulesOrchestrator()
```

### 11.3 Finální Migrace

```bash
# Po ověření stability V2:
mv core/orchestrator.py core/orchestrator_legacy.py
mv core/orchestrator_v2.py core/orchestrator.py

# Update dokumentace
# Update README.md
# Finální commit
```

---

## 📊 Progress Tracker

| Den | Komponenta | Status | Testy | Commit |
|-----|------------|--------|-------|--------|
| 1 | StateManager | ✅ | 16/16 | ✅ |
| 2 | RecoveryManager | ✅ | 12/12 | ✅ |
| 3-4 | PlanManager | ✅ | 10/10 | ✅ |
| 5-6 | ReflectionEngine | 🔜 | 🔜 | 🔜 |
| 7 | BudgetTracker | 🔜 | 🔜 | 🔜 |
| 8-10 | NomadOrchestratorV2 | 🔜 | 🔜 | 🔜 |
| 11-12 | E2E + Migration | 🔜 | 🔜 | 🔜 |

---

## 📋 FINÁLNÍ CHECKLIST PŘED ZAČÁTKEM

**Vytiskni si tento checklist a zaškrtávej po dokončení každého kroku!**

```
PRE-FLIGHT CHECKLIST:
[ ] Git je čistý (git status)
[ ] Backup větev vytvořena (refactoring/nomad-v2-implementation)
[ ] Všechny existující testy projdou
[ ] Python >= 3.10
[ ] .env obsahuje OPENROUTER_API_KEY
[ ] Backup současného orchestrator.py vytvořen

DEN 1 - StateManager:
[ ] Soubory vytvořeny (state_manager.py, test_state_manager.py)
[ ] State enum implementován
[ ] StateManager třída kompletní
[ ] 16/16 testů prošlo
[ ] Git commit

DEN 2 - RecoveryManager:
[ ] recovery_manager.py implementován
[ ] test_recovery_manager.py kompletní
[ ] 12/12 testů prošlo
[ ] Integrace s RichPrinter funguje
[ ] Git commit

DEN 3-4 - PlanManager:
[ ] PlanStep dataclass
[ ] PlanManager s LLM integrací
[ ] 10/10 testů prošlo
[ ] LLM planning test úspěšný
[ ] Git commit

DEN 5-6 - ReflectionEngine:
[ ] ReflectionEngine implementován
[ ] 8/8 testů prošlo
[ ] Git commit

DEN 7 - BudgetTracker:
[ ] BudgetTracker implementován
[ ] 6/6 testů prošlo
[ ] Git commit

DEN 8-10 - NomadOrchestratorV2:
[ ] orchestrator_v2.py kompletní
[ ] Všechny state handlery implementovány
[ ] Integrace všech komponent
[ ] 10+ testů prošlo
[ ] Git commit

DEN 11-12 - E2E + Migrace:
[ ] E2E testy napsány
[ ] Side-by-side režim funguje
[ ] Plná migrace dokončena
[ ] Dokumentace aktualizována
[ ] WORKLOG.md záznam
[ ] Finální git commit
```

---

## 🔥 KRITICKÁ VAROVÁNÍ

### NIKDY nedělej tyto věci:

1. ❌ **NIKDY necommituj nefunkční kód** → Vždy spusť testy před commitem
2. ❌ **NIKDY nemazej starý kód bez zálohy** → Přejmenuj na `_legacy.py`
3. ❌ **NIKDY neimplementuj bez testů** → TDD přístup (test first)
4. ❌ **NIKDY neignoruj selhávající test** → Pokud test selže 2x, STOP a analyzuj
5. ❌ **NIKDY neděláš force push** → Mohlo by to zničit historii

### VŽDY dělej tyto věci:

1. ✅ **VŽDY spusť testy před commitem**
2. ✅ **VŽDY commituj po každém checkpointu**
3. ✅ **VŽDY používej rollback pokud selže** → `git reset --hard <sha>`
4. ✅ **VŽDY čti error messages pečlivě**
5. ✅ **VŽDY kontroluj Git status** → Žádné necommitnuté změny

---

## 📞 SOS - Co dělat když selže

### Scenario 1: Test Selhává

```bash
# 1. Přečti error message
python -m pytest tests/test_<component>.py -v --tb=long

# 2. Spusť pouze selhávající test
python -m pytest tests/test_<component>.py::TestClass::test_name -v

# 3. Zkontroluj syntax
python -m py_compile core/<component>.py

# 4. Pokud opakuje stejná chyba:
#    STOP! Neopravuj naslepo!
#    Porovnej kód s REFACTORING_ROADMAP_V2.md
#    Zkontroluj dependencies (imports)

# 5. Pokud stále selže:
#    Rollback k poslednímu fungujícímu commitu
git log --oneline | head -5
git reset --hard <commit_sha>
```

---

## 🏁 FINÁLNÍ VALIDACE

**Po dokončení všeho spusť:**

```bash
# Kompletní test suite
python -m pytest tests/ -v

# Očekávaný výstup:
# - 72/72 testů prošlo ✅

# Funkční test
python main.py --orchestrator=nomad_v2 --task="Vytvoř soubor test.txt"
```

---

## 🚀 TEĎ ZAČNI!

Jsi připraven. Veškeré informace máš. Začni **DNEM 1** a postupuj krok po kroku.

**Pamatuj:**
- Nespěchej
- Testuj často
- Commituj často
- Pokud nejsi jistý, PTEJ SE!

**HODNĚ ŠTĚSTÍ! 🍀**

---

**Autor:** Jules (Nomad)  
**Verze:** 1.0 FINÁLNÍ  
**Datum:** 2025-10-12  
**Status:** ✅ READY FOR IMPLEMENTATION
