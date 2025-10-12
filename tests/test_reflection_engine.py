"""
Unit testy pro ReflectionEngine.

Test Coverage:
- ✅ Reflection na různé typy chyb
- ✅ Parsování LLM odpovědí
- ✅ Suggested actions (retry, replanning, ask_user, atd.)
- ✅ Confidence scoring
- ✅ Pattern detection
- ✅ Historie reflexí
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from core.reflection_engine import ReflectionEngine, ReflectionResult


# Mock LLM Manager pro testy
class MockLLMManager:
    """Mock LLM Manager který vrací předpřipravené odpovědi."""
    
    def __init__(self, response: str = None):
        self.response = response or self._default_response()
        self.default_llm_name = "mock_model"
    
    def _default_response(self) -> str:
        """Default validní reflexe."""
        return json.dumps({
            "analysis": "Test analysis",
            "root_cause": "Test root cause",
            "suggested_action": "retry",
            "confidence": 0.8,
            "modification_hint": None
        })
    
    def get_llm(self, name: str):
        """Vrátí mock model."""
        model = MagicMock()
        model.generate_content_async = AsyncMock(return_value=(self.response, None))
        return model


class TestReflectionResult:
    """Testy pro ReflectionResult dataclass."""
    
    def test_reflection_result_creation(self):
        """Test vytvoření ReflectionResult."""
        result = ReflectionResult(
            analysis="Test analysis",
            root_cause="Test cause",
            suggested_action="retry",
            confidence=0.9
        )
        
        assert result.analysis == "Test analysis"
        assert result.root_cause == "Test cause"
        assert result.suggested_action == "retry"
        assert result.confidence == 0.9
    
    def test_reflection_result_to_dict(self):
        """Test serializace ReflectionResult."""
        result = ReflectionResult(
            analysis="Analysis",
            root_cause="Cause",
            suggested_action="replanning",
            confidence=0.7,
            modification_hint="Change path"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["analysis"] == "Analysis"
        assert result_dict["suggested_action"] == "replanning"
        assert result_dict["modification_hint"] == "Change path"


class TestReflectionExecution:
    """Testy pro provádění reflexe."""
    
    @pytest.mark.asyncio
    async def test_reflect_on_failure_basic(self):
        """Test základní reflexe."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test step"},
            error_message="Error message",
            attempt_count=1
        )
        
        assert isinstance(result, ReflectionResult)
        assert result.suggested_action == "retry"
        assert result.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_reflect_on_failure_with_plan_context(self):
        """Test reflexe s plan contextem."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 2, "description": "Complex step"},
            error_message="Complex error",
            attempt_count=2,
            plan_context="Full plan context here"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reflection_records_history(self):
        """Reflexe by měla zaznamenat do historie."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Step"},
            error_message="Error",
            attempt_count=1
        )
        
        assert len(re.reflection_history) == 1
        assert re.reflection_history[0]["step_id"] == 1


class TestResponseParsing:
    """Testy pro parsování LLM odpovědí."""
    
    @pytest.mark.asyncio
    async def test_parse_json_in_markdown(self):
        """Test parsování JSON v markdown code blocku."""
        response = """
Zde je analýza:

```json
{
  "analysis": "Markdown analysis",
  "root_cause": "Markdown cause",
  "suggested_action": "replanning",
  "confidence": 0.85
}
```

To je vše.
"""
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test"},
            error_message="Error",
            attempt_count=1
        )
        
        assert result.analysis == "Markdown analysis"
        assert result.suggested_action == "replanning"
        assert result.confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_parse_plain_json(self):
        """Test parsování plain JSON."""
        response = json.dumps({
            "analysis": "Plain JSON",
            "root_cause": "Plain cause",
            "suggested_action": "ask_user",
            "confidence": 0.6
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test"},
            error_message="Error",
            attempt_count=1
        )
        
        assert result.analysis == "Plain JSON"
        assert result.suggested_action == "ask_user"
    
    @pytest.mark.asyncio
    async def test_parse_json_with_extra_text(self):
        """Test parsování JSON s extra textem okolo."""
        response = f"""
Nějaký text před...

{json.dumps({
    "analysis": "Extracted",
    "root_cause": "Extraction test",
    "suggested_action": "skip_step",
    "confidence": 0.9
})}

...a nějaký text po.
"""
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test"},
            error_message="Error",
            attempt_count=1
        )
        
        assert result.analysis == "Extracted"
        assert result.suggested_action == "skip_step"


class TestFallbackReflection:
    """Testy pro fallback když LLM parsing selže."""
    
    @pytest.mark.asyncio
    async def test_fallback_first_attempt(self):
        """Fallback pro první pokus by měl být 'retry'."""
        llm = MockLLMManager(response="Invalid JSON response!!!")
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test"},
            error_message="Error",
            attempt_count=1
        )
        
        assert result.suggested_action == "retry"
        assert result.confidence < 0.5  # Fallback má nízkou confidence
    
    @pytest.mark.asyncio
    async def test_fallback_third_attempt(self):
        """Fallback pro 3+ pokus by měl být 'ask_user'."""
        llm = MockLLMManager(response="Still invalid JSON!!!")
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Test"},
            error_message="Error",
            attempt_count=3
        )
        
        assert result.suggested_action == "ask_user"


class TestSuggestedActions:
    """Testy pro různé suggested actions."""
    
    @pytest.mark.asyncio
    async def test_suggested_action_retry(self):
        """Test retry action."""
        response = json.dumps({
            "analysis": "Transient error",
            "root_cause": "Network timeout",
            "suggested_action": "retry",
            "confidence": 0.7
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Network call"},
            error_message="Timeout",
            attempt_count=1
        )
        
        assert result.suggested_action == "retry"
    
    @pytest.mark.asyncio
    async def test_suggested_action_retry_modified(self):
        """Test retry_modified action s modification_hint."""
        response = json.dumps({
            "analysis": "File path issue",
            "root_cause": "Missing PROJECT_ROOT prefix",
            "suggested_action": "retry_modified",
            "confidence": 0.85,
            "modification_hint": "Add PROJECT_ROOT/ prefix to path"
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 2, "description": "Read file"},
            error_message="FileNotFoundError",
            attempt_count=1
        )
        
        assert result.suggested_action == "retry_modified"
        assert result.modification_hint is not None
        assert "PROJECT_ROOT" in result.modification_hint
    
    @pytest.mark.asyncio
    async def test_suggested_action_replanning(self):
        """Test replanning action."""
        response = json.dumps({
            "analysis": "Fundamental approach issue",
            "root_cause": "Unrealistic plan",
            "suggested_action": "replanning",
            "confidence": 0.9
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 3, "description": "Complex task"},
            error_message="Multiple errors",
            attempt_count=3
        )
        
        assert result.suggested_action == "replanning"
    
    @pytest.mark.asyncio
    async def test_suggested_action_ask_user(self):
        """Test ask_user action."""
        response = json.dumps({
            "analysis": "Unclear requirements",
            "root_cause": "Ambiguous task description",
            "suggested_action": "ask_user",
            "confidence": 0.75
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 4, "description": "Vague task"},
            error_message="ValidationError",
            attempt_count=2
        )
        
        assert result.suggested_action == "ask_user"
    
    @pytest.mark.asyncio
    async def test_suggested_action_skip_step(self):
        """Test skip_step action."""
        response = json.dumps({
            "analysis": "Non-critical step",
            "root_cause": "Optional feature",
            "suggested_action": "skip_step",
            "confidence": 0.8
        })
        llm = MockLLMManager(response=response)
        re = ReflectionEngine(llm)
        
        result = await re.reflect_on_failure(
            failed_step={"id": 5, "description": "Optional step"},
            error_message="Error",
            attempt_count=2
        )
        
        assert result.suggested_action == "skip_step"


class TestReflectionHistory:
    """Testy pro historii reflexí."""
    
    @pytest.mark.asyncio
    async def test_history_limit(self):
        """Historie by měla být omezena na max_history_size."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        re.max_history_size = 3  # Nastav malý limit pro test
        
        # Vytvoř 5 reflexí
        for i in range(5):
            await re.reflect_on_failure(
                failed_step={"id": i, "description": f"Step {i}"},
                error_message=f"Error {i}",
                attempt_count=1
            )
        
        # Mělo by být pouze 3 (max_history_size)
        assert len(re.reflection_history) == 3
        # A měly by to být poslední 3 (indexy 2, 3, 4)
        assert re.reflection_history[0]["step_id"] == 2
        assert re.reflection_history[2]["step_id"] == 4
    
    @pytest.mark.asyncio
    async def test_reflect_on_success(self):
        """Test reflexe úspěchu (jednodušší)."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        await re.reflect_on_success(
            completed_step={"id": 1, "description": "Success step"}
        )
        
        assert len(re.reflection_history) == 1
        assert re.reflection_history[0]["result"]["status"] == "success"


class TestPatternDetection:
    """Testy pro detekci vzorů selhání."""
    
    @pytest.mark.asyncio
    async def test_get_failure_patterns(self):
        """Test get_failure_patterns()."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        # Simuluj 3 reflexe s různými root causes
        for i in range(3):
            response = json.dumps({
                "analysis": f"Analysis {i}",
                "root_cause": "Network timeout" if i < 2 else "File not found",
                "suggested_action": "retry",
                "confidence": 0.8
            })
            llm.response = response
            
            await re.reflect_on_failure(
                failed_step={"id": i, "description": f"Step {i}"},
                error_message=f"Error {i}",
                attempt_count=1
            )
        
        patterns = re.get_failure_patterns()
        
        assert patterns["Network timeout"] == 2
        assert patterns["File not found"] == 1
    
    @pytest.mark.asyncio
    async def test_get_most_common_failure(self):
        """Test get_most_common_failure()."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        # Vytvoř 5 reflexí: 3x "Timeout", 2x "Permission denied"
        causes = ["Timeout", "Timeout", "Permission denied", "Timeout", "Permission denied"]
        
        for i, cause in enumerate(causes):
            response = json.dumps({
                "analysis": "Analysis",
                "root_cause": cause,
                "suggested_action": "retry",
                "confidence": 0.7
            })
            llm.response = response
            
            await re.reflect_on_failure(
                failed_step={"id": i, "description": f"Step {i}"},
                error_message="Error",
                attempt_count=1
            )
        
        most_common = re.get_most_common_failure()
        assert most_common == "Timeout"
    
    def test_get_most_common_failure_empty(self):
        """Test get_most_common_failure() s prázdnou historií."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        assert re.get_most_common_failure() is None


class TestClearHistory:
    """Test pro clear_history()."""
    
    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test že clear_history() smaže historii."""
        llm = MockLLMManager()
        re = ReflectionEngine(llm)
        
        # Vytvoř nějaké reflexe
        await re.reflect_on_failure(
            failed_step={"id": 1, "description": "Step"},
            error_message="Error",
            attempt_count=1
        )
        
        assert len(re.reflection_history) > 0
        
        re.clear_history()
        
        assert len(re.reflection_history) == 0


# Spuštění testů
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
