"""
Unit testy pro PlanManager.

Test Coverage:
- ✅ Vytváření plánu z LLM odpovědi
- ✅ Parsování různých JSON formátů
- ✅ Validace plánu (duplicitní ID, cykly, závislosti)
- ✅ Dependency resolution
- ✅ Progress tracking
- ✅ Serializace/deserializace
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from core.plan_manager import PlanManager, PlanStep


# Mock LLM Manager pro testy
class MockLLMManager:
    """Mock LLM Manager který vrací předpřipravené odpovědi."""
    
    def __init__(self, response: str = None):
        self.response = response or self._default_response()
        self.default_llm_name = "mock_model"
    
    def _default_response(self) -> str:
        """Default validní plán."""
        return json.dumps({
            "steps": [
                {
                    "id": 1,
                    "description": "Krok 1",
                    "dependencies": [],
                    "estimated_tokens": 100
                },
                {
                    "id": 2,
                    "description": "Krok 2",
                    "dependencies": [1],
                    "estimated_tokens": 200
                }
            ]
        })
    
    def get_llm(self, name: str):
        """Vrátí mock model."""
        model = MagicMock()
        model.generate_content_async = AsyncMock(return_value=(self.response, None))
        return model


class TestPlanStep:
    """Testy pro PlanStep dataclass."""
    
    def test_plan_step_creation(self):
        """Test vytvoření PlanStep."""
        step = PlanStep(
            id=1,
            description="Test step",
            dependencies=[],
            estimated_tokens=500
        )
        
        assert step.id == 1
        assert step.description == "Test step"
        assert step.status == "pending"
        assert step.dependencies == []
        assert step.estimated_tokens == 500
    
    def test_plan_step_to_dict(self):
        """Test serializace PlanStep."""
        step = PlanStep(id=1, description="Test", estimated_tokens=100)
        step_dict = step.to_dict()
        
        assert step_dict["id"] == 1
        assert step_dict["description"] == "Test"
        assert step_dict["status"] == "pending"
    
    def test_plan_step_from_dict(self):
        """Test deserializace PlanStep."""
        data = {
            "id": 1,
            "description": "Test",
            "status": "completed",
            "dependencies": [2, 3],
            "estimated_tokens": 100,
            "actual_tokens": 150,
            "result": "Success",
            "error": None
        }
        
        step = PlanStep.from_dict(data)
        
        assert step.id == 1
        assert step.status == "completed"
        assert step.dependencies == [2, 3]
        assert step.actual_tokens == 150


class TestPlanCreation:
    """Testy pro vytváření plánu."""
    
    @pytest.mark.asyncio
    async def test_create_simple_plan(self):
        """Test vytvoření jednoduchého plánu."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        plan = await pm.create_plan("Test mission")
        
        assert len(plan) == 2
        assert plan[0].id == 1
        assert plan[1].id == 2
        assert plan[1].dependencies == [1]
    
    @pytest.mark.asyncio
    async def test_create_plan_with_markdown_json(self):
        """Test parsování JSON z markdown code blocku."""
        json_in_markdown = """
Zde je plán:

```json
{
  "steps": [
    {
      "id": 1,
      "description": "Krok v markdownu",
      "dependencies": [],
      "estimated_tokens": 300
    }
  ]
}
```

To je vše!
"""
        llm = MockLLMManager(response=json_in_markdown)
        pm = PlanManager(llm)
        
        plan = await pm.create_plan("Test")
        
        assert len(plan) == 1
        assert plan[0].description == "Krok v markdownu"
    
    @pytest.mark.asyncio
    async def test_create_plan_max_steps_limit(self):
        """Test že max_steps limituje počet kroků."""
        # LLM odpověď s 5 kroky
        response = json.dumps({
            "steps": [
                {"id": i, "description": f"Krok {i}", "dependencies": [], "estimated_tokens": 100}
                for i in range(1, 6)
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        plan = await pm.create_plan("Test", max_steps=3)
        
        # Mělo by být max 3 kroky
        assert len(plan) <= 3


class TestPlanValidation:
    """Testy pro validaci plánu."""
    
    @pytest.mark.asyncio
    async def test_validate_rejects_duplicate_ids(self):
        """Plán s duplicitními ID by měl být zamítnut."""
        response = json.dumps({
            "steps": [
                {"id": 1, "description": "Krok 1", "dependencies": [], "estimated_tokens": 100},
                {"id": 1, "description": "Duplicitní krok", "dependencies": [], "estimated_tokens": 100}
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        with pytest.raises(ValueError, match="duplicitní ID"):
            await pm.create_plan("Test")
    
    @pytest.mark.asyncio
    async def test_validate_rejects_invalid_dependency(self):
        """Plán se závislostí na neexistující krok by měl být zamítnut."""
        response = json.dumps({
            "steps": [
                {"id": 1, "description": "Krok 1", "dependencies": [999], "estimated_tokens": 100}
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        with pytest.raises(ValueError, match="neexistujícím kroku"):
            await pm.create_plan("Test")
    
    @pytest.mark.asyncio
    async def test_validate_rejects_self_dependency(self):
        """Krok nemůže záviset sám na sobě."""
        response = json.dumps({
            "steps": [
                {"id": 1, "description": "Krok 1", "dependencies": [1], "estimated_tokens": 100}
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        with pytest.raises(ValueError, match="nemůže záviset sám na sobě"):
            await pm.create_plan("Test")
    
    @pytest.mark.asyncio
    async def test_validate_rejects_circular_dependencies(self):
        """Plán s cyklickými závislostmi by měl být zamítnut."""
        response = json.dumps({
            "steps": [
                {"id": 1, "description": "Krok 1", "dependencies": [2], "estimated_tokens": 100},
                {"id": 2, "description": "Krok 2", "dependencies": [1], "estimated_tokens": 100}
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        with pytest.raises(ValueError, match="cyklické závislosti"):
            await pm.create_plan("Test")


class TestDependencyResolution:
    """Testy pro dependency resolution."""
    
    @pytest.mark.asyncio
    async def test_get_next_step_respects_dependencies(self):
        """get_next_step by měl vrátit pouze kroky se splněnými závislostmi."""
        response = json.dumps({
            "steps": [
                {"id": 1, "description": "Krok 1", "dependencies": [], "estimated_tokens": 100},
                {"id": 2, "description": "Krok 2", "dependencies": [1], "estimated_tokens": 100},
                {"id": 3, "description": "Krok 3", "dependencies": [1, 2], "estimated_tokens": 100}
            ]
        })
        llm = MockLLMManager(response=response)
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        # První next step by měl být krok 1 (žádné závislosti)
        next_step = pm.get_next_step()
        assert next_step.id == 1
        
        # Krok 2 by neměl být dostupný, dokud 1 není complete
        pm.mark_step_in_progress(1)
        next_step = pm.get_next_step()
        assert next_step is None  # Krok 1 ještě není completed
        
        # Po dokončení kroku 1 by měl být dostupný krok 2
        pm.mark_step_completed(1, "Success", 100)
        next_step = pm.get_next_step()
        assert next_step.id == 2
    
    @pytest.mark.asyncio
    async def test_get_next_step_returns_none_when_all_complete(self):
        """get_next_step by měl vrátit None když všechny kroky dokončeny."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        # Dokončit všechny kroky
        for step in pm.steps:
            pm.mark_step_completed(step.id, "Success", 100)
        
        next_step = pm.get_next_step()
        assert next_step is None


class TestProgressTracking:
    """Testy pro sledování pokroku."""
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test get_progress()."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        # Inicialně všechny pending
        progress = pm.get_progress()
        assert progress["total_steps"] == 2
        assert progress["pending"] == 2
        assert progress["completed"] == 0
        assert progress["progress_percent"] == 0
        
        # Dokončit první krok
        pm.mark_step_completed(1, "Success", 100)
        progress = pm.get_progress()
        assert progress["completed"] == 1
        assert progress["progress_percent"] == 50.0
        
        # Dokončit druhý krok
        pm.mark_step_completed(2, "Success", 200)
        progress = pm.get_progress()
        assert progress["completed"] == 2
        assert progress["progress_percent"] == 100.0
    
    @pytest.mark.asyncio
    async def test_is_plan_complete(self):
        """Test is_plan_complete()."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        assert pm.is_plan_complete() is False
        
        # Dokončit všechny kroky
        for step in pm.steps:
            pm.mark_step_completed(step.id, "Success", 100)
        
        assert pm.is_plan_complete() is True
    
    @pytest.mark.asyncio
    async def test_mark_step_failed(self):
        """Test mark_step_failed()."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        pm.mark_step_failed(1, "Error message")
        
        step = pm._get_step_by_id(1)
        assert step.status == "failed"
        assert step.error == "Error message"
        
        assert pm.has_failures() is True
        failed = pm.get_failed_steps()
        assert len(failed) == 1
        assert failed[0].id == 1


class TestSerialization:
    """Testy pro serializaci/deserializaci."""
    
    @pytest.mark.asyncio
    async def test_serialize_and_deserialize(self):
        """Test kompletního cyklu serialize → deserialize."""
        llm = MockLLMManager()
        pm1 = PlanManager(llm)
        
        await pm1.create_plan("Test mission")
        pm1.mark_step_completed(1, "Result", 150)
        
        # Serializuj
        data = pm1.serialize()
        
        # Deserializuj do nové instance
        pm2 = PlanManager.deserialize(data, llm)
        
        # Validace
        assert len(pm2.steps) == len(pm1.steps)
        assert pm2.steps[0].status == "completed"
        assert pm2.steps[0].result == "Result"
        assert pm2.steps[0].actual_tokens == 150
    
    @pytest.mark.asyncio
    async def test_serialize_preserves_all_data(self):
        """Serializace by měla zachovat všechna data."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        pm.mark_step_in_progress(1)
        pm.mark_step_failed(2, "Test error")
        
        data = pm.serialize()
        
        assert "steps" in data
        assert "current_step_index" in data
        assert "plan_created_at" in data
        assert len(data["steps"]) == 2
        assert data["steps"][0]["status"] == "in_progress"
        assert data["steps"][1]["status"] == "failed"


class TestSkipStep:
    """Testy pro přeskakování kroků."""
    
    @pytest.mark.asyncio
    async def test_mark_step_skipped(self):
        """Test mark_step_skipped()."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        pm.mark_step_skipped(1, "Not needed")
        
        step = pm._get_step_by_id(1)
        assert step.status == "skipped"
    
    @pytest.mark.asyncio
    async def test_skipped_steps_count_as_complete(self):
        """Přeskočené kroky by měly být považovány za kompletní."""
        llm = MockLLMManager()
        pm = PlanManager(llm)
        
        await pm.create_plan("Test")
        
        pm.mark_step_skipped(1, "Skip 1")
        pm.mark_step_skipped(2, "Skip 2")
        
        assert pm.is_plan_complete() is True


# Spuštění testů
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
