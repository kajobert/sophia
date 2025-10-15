"""
Unit testy pro RecoveryManager.

Test Coverage:
- ✅ Detekce crashed sessions
- ✅ Recovery strategie pro každý stav
- ✅ Bezpečné recovery (nezničí data)
- ✅ Cleanup starých sessions
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta

from core.state_manager import StateManager, State
from core.recovery_manager import RecoveryManager


class TestCrashedSessionDetection:
    """Testy pro detekci crashed sessions."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rm = RecoveryManager(self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_sessions_returns_empty_list(self):
        """Pokud žádné sessions, mělo by vrátit prázdný seznam."""
        crashed = self.rm.find_crashed_sessions()
        assert crashed == []
    
    def test_completed_session_not_detected_as_crashed(self):
        """Dokončené sessions by neměly být detekovány jako crashed."""
        sm = StateManager(self.temp_dir, "completed_session")
        sm.current_state = State.COMPLETED
        sm.persist()
        
        crashed = self.rm.find_crashed_sessions()
        assert "completed_session" not in crashed
    
    def test_idle_session_not_detected_as_crashed(self):
        """IDLE sessions by neměly být detekovány jako crashed."""
        sm = StateManager(self.temp_dir, "idle_session")
        # current_state je defaultně IDLE
        sm.persist()
        
        crashed = self.rm.find_crashed_sessions()
        assert "idle_session" not in crashed
    
    def test_planning_session_detected_as_crashed(self):
        """Session v PLANNING by měla být detekována jako crashed."""
        sm = StateManager(self.temp_dir, "planning_session")
        sm.transition_to(State.PLANNING, "Test")
        
        crashed = self.rm.find_crashed_sessions()
        assert "planning_session" in crashed
    
    def test_executing_session_detected_as_crashed(self):
        """Session v EXECUTING_STEP by měla být detekována."""
        sm = StateManager(self.temp_dir, "executing_session")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        
        crashed = self.rm.find_crashed_sessions()
        assert "executing_session" in crashed
    
    def test_multiple_crashed_sessions(self):
        """Test detekce více crashed sessions."""
        # Vytvoř 3 crashed sessions
        for i, state in enumerate([State.PLANNING, State.EXECUTING_STEP, State.ERROR]):
            sm = StateManager(self.temp_dir, f"crashed_{i}")
            if state != State.IDLE:  # IDLE je default
                # Musíme přejít validní cestou
                if state == State.PLANNING:
                    sm.transition_to(State.PLANNING)
                elif state == State.EXECUTING_STEP:
                    sm.transition_to(State.PLANNING)
                    sm.transition_to(State.EXECUTING_STEP)
                elif state == State.ERROR:
                    sm.transition_to(State.PLANNING)
                    sm.transition_to(State.ERROR, "Test error")
        
        # Vytvoř 1 completed session
        sm_ok = StateManager(self.temp_dir, "completed")
        sm_ok.current_state = State.COMPLETED
        sm_ok.persist()
        
        crashed = self.rm.find_crashed_sessions()
        assert len(crashed) == 3
        assert "completed" not in crashed


class TestRecoveryStrategies:
    """Testy pro recovery strategie."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rm = RecoveryManager(self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_recover_nonexistent_session(self):
        """Recovery neexistující session by mělo vrátit None."""
        result = self.rm.recover_session("nonexistent")
        assert result is None
    
    def test_recover_from_planning(self):
        """Recovery z PLANNING by mělo restartovat plánování."""
        # Vytvoř crashed session v PLANNING
        sm = StateManager(self.temp_dir, "planning_crash")
        sm.transition_to(State.PLANNING, "Original planning")
        sm.set_data("plan", {"steps": [1, 2, 3]})
        
        # Recover
        recovered_sm = self.rm.recover_session("planning_crash")
        
        assert recovered_sm is not None
        # Po recovery by měl být v PLANNING (restart)
        assert recovered_sm.get_state() == State.PLANNING
        # Partial plán by měl být smazán
        assert recovered_sm.get_data("plan") is None
    
    def test_recover_from_executing_with_pending_tool(self):
        """Recovery z EXECUTING_STEP s pending tool call."""
        sm = StateManager(self.temp_dir, "executing_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        sm.set_data("pending_tool_call", {"tool_name": "test_tool", "args": []})
        
        recovered_sm = self.rm.recover_session("executing_crash")
        
        assert recovered_sm is not None
        # Pending tool call by měl zůstat (pro retry)
        assert recovered_sm.get_data("pending_tool_call") is not None
    
    def test_recover_from_executing_without_pending_tool(self):
        """Recovery z EXECUTING_STEP bez pending tool → reflexe."""
        sm = StateManager(self.temp_dir, "executing_crash_no_tool")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        # ŽÁDNÝ pending_tool_call
        
        recovered_sm = self.rm.recover_session("executing_crash_no_tool")
        
        assert recovered_sm is not None
        # Mělo by přejít do REFLECTION
        assert recovered_sm.get_state() == State.REFLECTION
    
    def test_recover_from_awaiting_tool(self):
        """Recovery z AWAITING_TOOL → reflexe s error message."""
        sm = StateManager(self.temp_dir, "awaiting_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.EXECUTING_STEP)
        sm.transition_to(State.AWAITING_TOOL_RESULT)
        
        recovered_sm = self.rm.recover_session("awaiting_crash")
        
        assert recovered_sm is not None
        assert recovered_sm.get_state() == State.REFLECTION
        # Měla by být uložena error message
        error_msg = recovered_sm.get_data("error_message")
        assert error_msg is not None
        assert "interrupted" in error_msg.lower()
    
    def test_recover_from_reflection(self):
        """Recovery z REFLECTION → pokračuj (idempotentní)."""
        sm = StateManager(self.temp_dir, "reflection_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.ERROR, "Test")
        sm.transition_to(State.REFLECTION)
        
        recovered_sm = self.rm.recover_session("reflection_crash")
        
        assert recovered_sm is not None
        # Měl by zůstat v REFLECTION
        assert recovered_sm.get_state() == State.REFLECTION
    
    def test_recover_from_error(self):
        """Recovery z ERROR → reflexe."""
        sm = StateManager(self.temp_dir, "error_crash")
        sm.transition_to(State.PLANNING)
        sm.transition_to(State.ERROR, "Critical failure")
        sm.set_data("error_message", "Test error message")
        
        recovered_sm = self.rm.recover_session("error_crash")
        
        assert recovered_sm is not None
        assert recovered_sm.get_state() == State.REFLECTION
        # Error message by měla zůstat
        assert recovered_sm.get_data("error_message") == "Test error message"
    
    def test_recover_from_responding(self):
        """Recovery z RESPONDING → retry response generation."""
        sm = StateManager(self.temp_dir, "responding_crash")
        sm.current_state = State.RESPONDING  # Force set pro test
        sm.persist()
        
        recovered_sm = self.rm.recover_session("responding_crash")
        
        assert recovered_sm is not None
        # Měl by zůstat v RESPONDING
        assert recovered_sm.get_state() == State.RESPONDING


class TestCleanup:
    """Testy pro cleanup starých sessions."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rm = RecoveryManager(self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cleanup_does_not_delete_recent_sessions(self):
        """Cleanup by neměl smazat nedávné sessions."""
        sm = StateManager(self.temp_dir, "recent")
        sm.current_state = State.COMPLETED
        sm.persist()
        
        self.rm.cleanup_old_sessions(max_age_days=7)
        
        # Session by měla stále existovat
        session_file = os.path.join(
            self.temp_dir, "memory", "session_recent.json"
        )
        assert os.path.exists(session_file)
    
    def test_cleanup_does_not_delete_crashed_sessions(self):
        """Cleanup by NIKDY neměl smazat crashed sessions (i když staré)."""
        sm = StateManager(self.temp_dir, "old_crashed")
        sm.transition_to(State.PLANNING)
        sm.persist()
        
        # Simuluj starý soubor (změň mtime)
        session_file = os.path.join(
            self.temp_dir, "memory", "session_old_crashed.json"
        )
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(session_file, (old_time, old_time))
        
        self.rm.cleanup_old_sessions(max_age_days=7)
        
        # Crashed session by měla ZŮSTAT (i když je stará)
        assert os.path.exists(session_file)


class TestStatistics:
    """Testy pro get_recovery_statistics."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rm = RecoveryManager(self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_statistics_with_no_sessions(self):
        """Statistiky pro prázdný memory adresář."""
        stats = self.rm.get_recovery_statistics()
        
        assert stats["total_sessions"] == 0
        assert stats["crashed_sessions"] == 0
        assert stats["states"] == {}
    
    def test_statistics_with_mixed_sessions(self):
        """Statistiky s mixed sessions."""
        # 2 completed
        for i in range(2):
            sm = StateManager(self.temp_dir, f"completed_{i}")
            sm.current_state = State.COMPLETED
            sm.persist()
        
        # 1 crashed (planning)
        sm = StateManager(self.temp_dir, "crashed")
        sm.transition_to(State.PLANNING)
        
        # 1 idle
        sm = StateManager(self.temp_dir, "idle")
        sm.persist()
        
        stats = self.rm.get_recovery_statistics()
        
        assert stats["total_sessions"] == 4
        assert stats["crashed_sessions"] == 1  # Pouze planning
        assert stats["states"]["completed"] == 2
        assert stats["states"]["planning"] == 1
        assert stats["states"]["idle"] == 1


# Spuštění testů
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
