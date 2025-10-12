"""
Unit testy pro BudgetTracker.

Test Coverage:
- ✅ Budget initialization
- ✅ Recording step costs
- ✅ Budget checking
- ✅ Warning levels (info, warning, critical)
- ✅ Thresholds (80%, 95%)
- ✅ Summary generation
- ✅ Estimation of remaining steps
- ✅ Serialization/deserialization
"""

import pytest
import time
from core.budget_tracker import BudgetTracker, BudgetWarning


class TestBudgetTrackerInit:
    """Testy pro inicializaci BudgetTracker."""
    
    def test_default_initialization(self):
        """Test výchozí inicializace."""
        bt = BudgetTracker()
        
        assert bt.max_tokens == 100000
        assert bt.max_time_seconds == 3600
        assert bt.warning_threshold == 0.8
        assert bt.critical_threshold == 0.95
        assert bt.tokens_used == 0
        assert bt.time_elapsed == 0.0
        assert len(bt.step_costs) == 0
    
    def test_custom_initialization(self):
        """Test inicializace s custom parametry."""
        bt = BudgetTracker(
            max_tokens=50000,
            max_time_seconds=1800,
            warning_threshold=0.7,
            critical_threshold=0.9
        )
        
        assert bt.max_tokens == 50000
        assert bt.max_time_seconds == 1800
        assert bt.warning_threshold == 0.7
        assert bt.critical_threshold == 0.9


class TestRecordStepCost:
    """Testy pro zaznamenávání nákladů kroků."""
    
    def test_record_single_step(self):
        """Test zaznamenání jednoho kroku."""
        bt = BudgetTracker()
        
        bt.record_step_cost(step_id=1, tokens=1000, seconds=10.5)
        
        assert bt.tokens_used == 1000
        assert bt.time_elapsed == 10.5
        assert 1 in bt.step_costs
        assert bt.step_costs[1]["tokens"] == 1000
        assert bt.step_costs[1]["seconds"] == 10.5
    
    def test_record_multiple_steps(self):
        """Test zaznamenání více kroků."""
        bt = BudgetTracker()
        
        bt.record_step_cost(1, 1000, 10.0)
        bt.record_step_cost(2, 2000, 15.0)
        bt.record_step_cost(3, 1500, 12.0)
        
        assert bt.tokens_used == 4500
        assert bt.time_elapsed == 37.0
        assert len(bt.step_costs) == 3
    
    def test_record_with_description(self):
        """Test zaznamenání s popisem."""
        bt = BudgetTracker()
        
        bt.record_step_cost(1, 1000, 10.0, "Test step")
        
        assert bt.step_costs[1]["description"] == "Test step"


class TestCheckBudget:
    """Testy pro kontrolu rozpočtu."""
    
    def test_check_budget_sufficient(self):
        """Test check_budget kdy je dostatek rozpočtu."""
        bt = BudgetTracker(max_tokens=10000, max_time_seconds=600)
        bt.record_step_cost(1, 1000, 10.0)
        
        result = bt.check_budget(estimated_tokens=500)
        
        assert result["can_proceed"] is True
        assert result["warning"] is None
        assert result["tokens_remaining"] == 9000
        assert result["tokens_used_percent"] == 0.1
    
    def test_check_budget_insufficient_tokens(self):
        """Test check_budget kdy není dostatek tokenů."""
        bt = BudgetTracker(max_tokens=10000)
        bt.record_step_cost(1, 9000, 10.0)
        
        result = bt.check_budget(estimated_tokens=2000)
        
        assert result["can_proceed"] is False
        assert result["warning"] is not None
        assert result["warning"].level == "critical"
        assert "NEDOSTATEK TOKENŮ" in result["warning"].message
    
    def test_check_budget_warning_threshold(self):
        """Test check_budget při warning threshold (80%)."""
        bt = BudgetTracker(max_tokens=10000, warning_threshold=0.8)
        bt.record_step_cost(1, 8500, 10.0)  # 85% použito
        
        result = bt.check_budget(estimated_tokens=100)
        
        assert result["can_proceed"] is True  # Stále můžeme pokračovat
        assert result["warning"] is not None
        assert result["warning"].level == "warning"
        assert "NÍZKÝ ROZPOČET TOKENŮ" in result["warning"].message
    
    def test_check_budget_critical_threshold(self):
        """Test check_budget při critical threshold (95%)."""
        bt = BudgetTracker(max_tokens=10000, critical_threshold=0.95)
        bt.record_step_cost(1, 9600, 10.0)  # 96% použito
        
        result = bt.check_budget(estimated_tokens=100)
        
        assert result["warning"] is not None
        assert result["warning"].level == "critical"
        assert "KRITICKY NÍZKÝ ROZPOČET" in result["warning"].message
    
    def test_check_budget_time_warning(self):
        """Test varování při nízkém času."""
        bt = BudgetTracker(max_tokens=100000, max_time_seconds=100)
        
        # Simuluj že uplynulo 85 sekund (85%)
        bt.start_time = time.time() - 85
        
        result = bt.check_budget(estimated_tokens=100)
        
        assert result["warning"] is not None
        assert "MÁLO ČASU" in result["warning"].message or "KRITICKY MÁLO ČASU" in result["warning"].message


class TestWarningGeneration:
    """Testy pro generování varování."""
    
    def test_no_warning_low_usage(self):
        """Žádné varování při nízké spotřebě."""
        bt = BudgetTracker(max_tokens=10000)
        bt.record_step_cost(1, 1000, 10.0)  # 10%
        
        result = bt.check_budget(estimated_tokens=100)
        
        assert result["warning"] is None
    
    def test_warning_at_exact_threshold(self):
        """Varování přesně na prahu."""
        bt = BudgetTracker(max_tokens=10000, warning_threshold=0.8)
        bt.record_step_cost(1, 8000, 10.0)  # Přesně 80%
        
        result = bt.check_budget()
        
        assert result["warning"] is not None
        assert result["warning"].level == "warning"
    
    def test_warnings_are_recorded(self):
        """Varování se zaznamenávají do history."""
        bt = BudgetTracker(max_tokens=10000, warning_threshold=0.8)
        
        assert len(bt.warnings_issued) == 0
        
        bt.record_step_cost(1, 8500, 10.0)
        bt.check_budget()
        
        assert len(bt.warnings_issued) == 1
        assert bt.warnings_issued[0].level == "warning"


class TestSummaries:
    """Testy pro summary metody."""
    
    def test_get_summary_format(self):
        """Test formátu get_summary()."""
        bt = BudgetTracker(max_tokens=10000, max_time_seconds=600)
        bt.record_step_cost(1, 2000, 100.0)
        
        summary = bt.get_summary()
        
        assert "BUDGET SUMMARY" in summary
        assert "Tokeny:" in summary
        assert "Čas:" in summary
        assert "Kroky:" in summary
    
    def test_get_detailed_summary(self):
        """Test get_detailed_summary()."""
        bt = BudgetTracker(max_tokens=10000)
        bt.record_step_cost(1, 2000, 50.0)
        bt.record_step_cost(2, 1500, 30.0)
        
        summary = bt.get_detailed_summary()
        
        assert summary["tokens"]["used"] == 3500
        assert summary["tokens"]["remaining"] == 6500
        assert summary["steps"]["count"] == 2
        assert len(summary["steps"]["costs"]) == 2
    
    def test_get_step_cost(self):
        """Test získání nákladů konkrétního kroku."""
        bt = BudgetTracker()
        bt.record_step_cost(1, 1000, 10.0, "Test step")
        
        cost = bt.get_step_cost(1)
        
        assert cost is not None
        assert cost["tokens"] == 1000
        assert cost["seconds"] == 10.0
        assert cost["description"] == "Test step"
    
    def test_get_step_cost_nonexistent(self):
        """Test get_step_cost pro neexistující krok."""
        bt = BudgetTracker()
        
        cost = bt.get_step_cost(999)
        
        assert cost is None


class TestAverages:
    """Testy pro průměry a odhady."""
    
    def test_get_average_step_cost(self):
        """Test průměrných nákladů."""
        bt = BudgetTracker()
        bt.record_step_cost(1, 1000, 10.0)
        bt.record_step_cost(2, 2000, 20.0)
        bt.record_step_cost(3, 1500, 15.0)
        
        avg = bt.get_average_step_cost()
        
        assert avg["tokens"] == 1500.0  # (1000+2000+1500)/3
        assert avg["seconds"] == 15.0   # (10+20+15)/3
    
    def test_get_average_step_cost_empty(self):
        """Test průměru bez kroků."""
        bt = BudgetTracker()
        
        avg = bt.get_average_step_cost()
        
        assert avg["tokens"] == 0.0
        assert avg["seconds"] == 0.0
    
    def test_estimate_remaining_steps(self):
        """Test odhadu zbývajících kroků."""
        bt = BudgetTracker(max_tokens=10000, max_time_seconds=1000)
        bt.record_step_cost(1, 1000, 100.0)
        bt.record_step_cost(2, 1000, 100.0)
        
        # Průměr: 1000 tokenů, 100 sekund
        # Zbývá: 8000 tokenů, ~800 sekund
        # Odhad: min(8 steps by tokens, 8 steps by time) = 8
        
        remaining = bt.estimate_remaining_steps()
        
        assert remaining == 8
    
    def test_estimate_remaining_steps_empty(self):
        """Test odhadu bez historie."""
        bt = BudgetTracker(max_tokens=10000)
        
        remaining = bt.estimate_remaining_steps()
        
        assert remaining == 999  # Ještě nic nespotřebováno


class TestReset:
    """Testy pro reset funkci."""
    
    def test_reset(self):
        """Test resetování trackeru."""
        bt = BudgetTracker()
        bt.record_step_cost(1, 1000, 10.0)
        bt.record_step_cost(2, 2000, 20.0)
        
        # Simuluj varování
        bt.check_budget()
        
        assert bt.tokens_used > 0
        assert len(bt.step_costs) > 0
        
        bt.reset()
        
        assert bt.tokens_used == 0
        assert bt.time_elapsed == 0.0
        assert len(bt.step_costs) == 0
        assert len(bt.warnings_issued) == 0


class TestSerialization:
    """Testy pro serializaci a deserializaci."""
    
    def test_serialize(self):
        """Test serializace."""
        bt = BudgetTracker(max_tokens=50000, max_time_seconds=1800)
        bt.record_step_cost(1, 1000, 10.0)
        bt.record_step_cost(2, 2000, 20.0)
        
        data = bt.serialize()
        
        assert data["max_tokens"] == 50000
        assert data["max_time_seconds"] == 1800
        assert data["tokens_used"] == 3000
        assert len(data["step_costs"]) == 2
    
    def test_deserialize(self):
        """Test deserializace."""
        data = {
            "max_tokens": 50000,
            "max_time_seconds": 1800,
            "warning_threshold": 0.7,
            "critical_threshold": 0.9,
            "tokens_used": 3000,
            "time_elapsed": 30.0,
            "step_costs": {
                "1": {"tokens": 1000, "seconds": 10.0},
                "2": {"tokens": 2000, "seconds": 20.0}
            },
            "warnings_count": 1
        }
        
        bt = BudgetTracker.deserialize(data)
        
        assert bt.max_tokens == 50000
        assert bt.tokens_used == 3000
        assert bt.warning_threshold == 0.7
        assert len(bt.step_costs) == 2
    
    def test_serialize_deserialize_roundtrip(self):
        """Test round-trip serializace."""
        bt1 = BudgetTracker(max_tokens=10000)
        bt1.record_step_cost(1, 1000, 10.0)
        bt1.record_step_cost(2, 2000, 20.0)
        
        data = bt1.serialize()
        bt2 = BudgetTracker.deserialize(data)
        
        assert bt2.max_tokens == bt1.max_tokens
        assert bt2.tokens_used == bt1.tokens_used
        # time_elapsed může mírně lišit kvůli času běhu testu
        assert len(bt2.step_costs) == len(bt1.step_costs)


class TestBudgetWarning:
    """Testy pro BudgetWarning dataclass."""
    
    def test_budget_warning_creation(self):
        """Test vytvoření BudgetWarning."""
        warning = BudgetWarning(
            level="warning",
            message="Test warning",
            tokens_remaining=5000,
            time_remaining=300.0
        )
        
        assert warning.level == "warning"
        assert warning.message == "Test warning"
        assert warning.tokens_remaining == 5000
        assert warning.time_remaining == 300.0


# Spuštění testů
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
