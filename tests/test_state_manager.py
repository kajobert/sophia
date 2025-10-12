"""
Unit testy pro StateManager.

Tyto testy MUSÍ všechny projít před pokračováním v implementaci!

Test Coverage:
- ✅ Validace přechodů (valid & invalid)
- ✅ Persistence a restore
- ✅ Historie přechodů
- ✅ Data storage
- ✅ Session ID generování
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime

from core.state_manager import State, StateTransitionError, StateManager


class TestStateEnum:
    """Testy pro State enum."""
    
    def test_all_states_exist(self):
        """Ověř že všechny očekávané stavy existují."""
        expected_states = [
            "idle", "planning", "executing_step", "awaiting_tool",
            "reflection", "responding", "completed", "error"
        ]
        
        actual_states = [s.value for s in State]
        assert set(actual_states) == set(expected_states)
    
    def test_state_enum_values(self):
        """Ověř že enum values jsou správně nastaveny."""
        assert State.IDLE.value == "idle"
        assert State.PLANNING.value == "planning"
        assert State.ERROR.value == "error"


class TestStateTransitions:
    """Testy pro validaci přechodů mezi stavy."""
    
    def setup_method(self):
        """Příprava před každým testem."""
        self.temp_dir = tempfile.mkdtemp()
        self.sm = StateManager(project_root=self.temp_dir, session_id="test_session")
    
    def teardown_method(self):
        """Úklid po každém testu."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initial_state_is_idle(self):
        """Nový StateManager by měl začínat v IDLE."""
        assert self.sm.get_state() == State.IDLE
    
    def test_valid_transition_idle_to_planning(self):
        """Validní přechod IDLE → PLANNING."""
        result = self.sm.transition_to(State.PLANNING, "Starting mission")
        assert result is True
        assert self.sm.get_state() == State.PLANNING
    
    def test_invalid_transition_idle_to_executing(self):
        """Nevalidní přechod IDLE → EXECUTING_STEP by měl vyhodit exception."""
        with pytest.raises(StateTransitionError) as exc_info:
            self.sm.transition_to(State.EXECUTING_STEP, "Invalid jump")
        
        assert "Nelze přejít" in str(exc_info.value)
        assert self.sm.get_state() == State.IDLE  # Stav by se neměl změnit
    
    def test_transition_chain_planning_to_executing_to_awaiting(self):
        """Test řetězce validních přechodů."""
        self.sm.transition_to(State.PLANNING)
        self.sm.transition_to(State.EXECUTING_STEP)
        self.sm.transition_to(State.AWAITING_TOOL_RESULT)
        
        assert self.sm.get_state() == State.AWAITING_TOOL_RESULT
    
    def test_error_state_recovery(self):
        """Test že z ERROR lze přejít do REFLECTION."""
        self.sm.current_state = State.ERROR  # Force set pro test
        self.sm.transition_to(State.REFLECTION, "Analyzing error")
        
        assert self.sm.get_state() == State.REFLECTION
    
    def test_completed_to_idle(self):
        """Test že COMPLETED může přejít zpět do IDLE."""
        self.sm.current_state = State.COMPLETED  # Force set
        self.sm.transition_to(State.IDLE, "Ready for new mission")
        
        assert self.sm.get_state() == State.IDLE


class TestStatePersistence:
    """Testy pro ukládání a obnovování stavu."""
    
    def setup_method(self):
        """Příprava před každým testem."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_id = "test_persistence"
    
    def teardown_method(self):
        """Úklid po každém testu."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persist_creates_file(self):
        """Ověř že persist() vytvoří JSON soubor."""
        sm = StateManager(self.temp_dir, self.session_id)
        sm.persist()
        
        expected_file = os.path.join(self.temp_dir, "memory", f"session_{self.session_id}.json")
        assert os.path.exists(expected_file)
    
    def test_persist_and_restore(self):
        """Test kompletního cyklu persist → restore."""
        # Krok 1: Vytvoř SM a změň stav
        sm1 = StateManager(self.temp_dir, self.session_id)
        sm1.transition_to(State.PLANNING, "Test mission")
        sm1.set_data("mission_goal", "Test úkol")
        sm1.set_data("iteration", 5)
        
        # Krok 2: Vytvoř NOVOU instanci a obnov
        sm2 = StateManager(self.temp_dir, self.session_id)
        restored = sm2.restore()
        
        # Validace
        assert restored is True
        assert sm2.get_state() == State.PLANNING
        assert sm2.get_data("mission_goal") == "Test úkol"
        assert sm2.get_data("iteration") == 5
    
    def test_restore_nonexistent_session(self):
        """Test že restore() vrací False pro neexistující session."""
        sm = StateManager(self.temp_dir, "nonexistent_session")
        restored = sm.restore()
        
        assert restored is False
    
    def test_state_data_persistence(self):
        """Ověř že state_data je správně uloženo."""
        sm = StateManager(self.temp_dir, self.session_id)
        sm.set_data("key1", "value1")
        sm.set_data("key2", {"nested": "data"})
        sm.set_data("key3", [1, 2, 3])
        
        # Načti JSON přímo
        session_file = os.path.join(self.temp_dir, "memory", f"session_{self.session_id}.json")
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert data["state_data"]["key1"] == "value1"
        assert data["state_data"]["key2"]["nested"] == "data"
        assert data["state_data"]["key3"] == [1, 2, 3]


class TestStateHistory:
    """Testy pro historii přechodů."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sm = StateManager(self.temp_dir, "test_history")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_transition_creates_history_record(self):
        """Každý přechod by měl vytvořit záznam v historii."""
        self.sm.transition_to(State.PLANNING, "Reason 1")
        
        assert len(self.sm.state_history) == 1
        assert self.sm.state_history[0]["from"] == "idle"
        assert self.sm.state_history[0]["to"] == "planning"
        assert self.sm.state_history[0]["reason"] == "Reason 1"
    
    def test_multiple_transitions_history(self):
        """Test že historie zaznamenává všechny přechody."""
        self.sm.transition_to(State.PLANNING)
        self.sm.transition_to(State.EXECUTING_STEP)
        self.sm.transition_to(State.AWAITING_TOOL_RESULT)
        
        assert len(self.sm.state_history) == 3
        
        # Ověř sekvenci
        assert self.sm.state_history[0]["to"] == "planning"
        assert self.sm.state_history[1]["from"] == "planning"
        assert self.sm.state_history[1]["to"] == "executing_step"
        assert self.sm.state_history[2]["to"] == "awaiting_tool"
    
    def test_history_has_timestamps(self):
        """Každý záznam by měl mít timestamp."""
        self.sm.transition_to(State.PLANNING)
        
        timestamp_str = self.sm.state_history[0]["timestamp"]
        # Zkus parsovat timestamp
        timestamp = datetime.fromisoformat(timestamp_str)
        
        assert isinstance(timestamp, datetime)
    
    def test_get_transition_history_limit(self):
        """Test že get_transition_history respektuje limit."""
        # Vytvoř 5 přechodů
        for _ in range(5):
            current = self.sm.get_state()
            # Najdi validní přechod
            next_state = self.sm.VALID_TRANSITIONS[current][0]
            self.sm.transition_to(next_state)
        
        recent = self.sm.get_transition_history(limit=3)
        assert len(recent) == 3


class TestStateData:
    """Testy pro state_data storage."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sm = StateManager(self.temp_dir, "test_data")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_set_and_get_data(self):
        """Test základního set/get."""
        self.sm.set_data("test_key", "test_value")
        
        assert self.sm.get_data("test_key") == "test_value"
    
    def test_get_data_with_default(self):
        """Test že get_data vrací default pro neexistující klíč."""
        result = self.sm.get_data("nonexistent", default="default_value")
        
        assert result == "default_value"
    
    def test_overwrite_data(self):
        """Test přepsání existujících dat."""
        self.sm.set_data("key", "value1")
        self.sm.set_data("key", "value2")
        
        assert self.sm.get_data("key") == "value2"
    
    def test_data_persists_across_transitions(self):
        """Data by měla přežít přechody stavů."""
        self.sm.set_data("persistent_key", "persistent_value")
        self.sm.transition_to(State.PLANNING)
        self.sm.transition_to(State.EXECUTING_STEP)
        
        assert self.sm.get_data("persistent_key") == "persistent_value"


class TestSessionID:
    """Testy pro session ID generování."""
    
    def test_auto_generated_session_id_format(self):
        """Auto-generované ID by mělo mít formát YYYYMMDD_HHMMSS."""
        temp_dir = tempfile.mkdtemp()
        sm = StateManager(temp_dir)
        
        # Formát: 20251012_143022
        assert len(sm.session_id) == 15  # 8 digits + _ + 6 digits
        assert sm.session_id[8] == "_"
        
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_custom_session_id(self):
        """Pokud předáno session_id, mělo by být použito."""
        temp_dir = tempfile.mkdtemp()
        custom_id = "custom_test_session"
        sm = StateManager(temp_dir, session_id=custom_id)
        
        assert sm.session_id == custom_id
        
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestReset:
    """Testy pro reset() metodu."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sm = StateManager(self.temp_dir, "test_reset")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_reset_clears_state(self):
        """Reset by měl vrátit stav do IDLE."""
        self.sm.transition_to(State.PLANNING)
        self.sm.set_data("key", "value")
        
        self.sm.reset()
        
        assert self.sm.get_state() == State.IDLE
        assert self.sm.get_data("key") is None
        assert len(self.sm.state_history) == 0


# Spuštění testů s detailním výstupem
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
