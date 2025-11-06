#!/usr/bin/env python3
"""
Test Phase 3.6: Adaptive Model Escalation

Verifies that cognitive_reflection uses 3-tier escalation strategy
before calling expensive cloud LLMs.

Expected behavior:
  1. Try llama3.1:8b (3 attempts) - FREE
  2. If fail, try llama3.1:70b (3 attempts) - FREE  
  3. If fail, try gpt-4o-mini (1 attempt) - $0.005
  4. If fail, try claude-3.5-sonnet (1 attempt) - $0.015
  
Budget savings: 90% reduction ($0.60/month vs $6/month)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import json
import logging

# Import plugin
from plugins.cognitive_reflection import CognitiveReflection
from core.context import SharedContext

# Setup logging
logger = logging.getLogger(__name__)


class TestAdaptiveEscalation:
    """Test suite for adaptive model escalation strategy."""
    
    @pytest.fixture
    def mock_router(self):
        """Create mock cognitive_task_router plugin."""
        router = MagicMock()
        router.execute = AsyncMock()
        return router
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory manager."""
        memory = MagicMock()
        memory.db = MagicMock()
        return memory
    
    @pytest.fixture
    def test_config(self, mock_router, mock_memory):
        """Create test configuration."""
        return {
            "all_plugins": {
                "cognitive_task_router": mock_router,
                "memory_sqlite": mock_memory
            },
            "event_bus": MagicMock(),
            "reflection": {
                "failure_threshold": 3,
                "analysis_window_hours": 24
            }
        }
    
    @pytest.mark.asyncio
    async def test_tier1_success_8b_model(self, test_config, mock_router):
        """Test successful response from Tier 1 (llama3.1:8b)."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        # Mock successful response from 8B model
        valid_hypothesis = {
            "root_cause": "Test root cause",
            "hypothesis": "Test hypothesis",
            "proposed_fix": "Fix code",
            "fix_type": "code"
        }
        
        mock_context = SharedContext(
            session_id="test",
            current_state="test",
            user_input="test",
            logger=logger
        )
        mock_context.payload["llm_response"] = json.dumps(valid_hypothesis)
        mock_router.execute.return_value = mock_context
        
        # Call escalation
        response = await plugin._call_expert_llm("Test prompt")
        
        # Verify
        assert response is not None
        assert "root_cause" in response
        
        # Should only call once (Tier 1 success)
        assert mock_router.execute.call_count == 1
        
        # Verify used llama3.1:8b
        call_args = mock_router.execute.call_args[0][0]
        assert call_args.payload.get("force_model") == "llama3.1:8b"
        print("✅ Tier 1 (8B) success - 1 call, $0.00")
    
    @pytest.mark.asyncio
    async def test_tier1_fail_escalate_to_tier2(self, test_config, mock_router):
        """Test escalation from Tier 1 → Tier 2 (70B model)."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        call_count = 0
        
        async def mock_execute(context):
            nonlocal call_count
            call_count += 1
            
            result = SharedContext(
                session_id="test",
                current_state="test",
                user_input="test",
                logger=logger
            )
            
            # First 3 calls (8B) return invalid JSON
            if call_count <= 3:
                result.payload["llm_response"] = "Invalid response"
                return result
            
            # 4th call (70B) succeeds
            valid_hypothesis = {
                "root_cause": "Root cause from 70B",
                "hypothesis": "Hypothesis from 70B",
                "proposed_fix": "Fix from 70B",
                "fix_type": "code"
            }
            result.payload["llm_response"] = json.dumps(valid_hypothesis)
            return result
        
        mock_router.execute.side_effect = mock_execute
        
        # Call escalation
        response = await plugin._call_expert_llm("Test prompt")
        
        # Verify
        assert response is not None
        assert "70B" in response
        
        # Should call 4 times (3x Tier 1, 1x Tier 2)
        assert call_count == 4
        print("✅ Escalation 8B → 70B - 4 calls, $0.00")
    
    @pytest.mark.asyncio
    async def test_tier2_fail_escalate_to_tier3_cloud(self, test_config, mock_router):
        """Test escalation to Tier 3 (gpt-4o-mini) after local models fail."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        call_count = 0
        
        async def mock_execute(context):
            nonlocal call_count
            call_count += 1
            
            result = SharedContext(
                session_id="test",
                current_state="test",
                user_input="test",
                logger=logger
            )
            
            # First 6 calls (3x 8B, 3x 70B) fail
            if call_count <= 6:
                result.payload["llm_response"] = "Invalid"
                return result
            
            # 7th call (gpt-4o-mini) succeeds
            valid_hypothesis = {
                "root_cause": "Cloud analysis",
                "hypothesis": "Cloud hypothesis",
                "proposed_fix": "Cloud fix",
                "fix_type": "prompt"
            }
            result.payload["llm_response"] = json.dumps(valid_hypothesis)
            return result
        
        mock_router.execute.side_effect = mock_execute
        
        # Call escalation
        response = await plugin._call_expert_llm("Test prompt")
        
        # Verify
        assert response is not None
        assert "Cloud" in response
        
        # Should call 7 times (3x Tier 1, 3x Tier 2, 1x Tier 3)
        assert call_count == 7
        
        # Verify last call was gpt-4o-mini
        last_call = mock_router.execute.call_args_list[-1][0][0]
        assert "gpt-4o-mini" in last_call.payload.get("force_model", "")
        print("✅ Escalation 8B → 70B → GPT-4o-mini - 7 calls, $0.005")
    
    @pytest.mark.asyncio
    async def test_all_tiers_fail_fallback(self, test_config, mock_router):
        """Test fallback behavior when all tiers fail."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        call_count = 0
        
        async def mock_execute(context):
            nonlocal call_count
            call_count += 1
            
            result = SharedContext(
                session_id="test",
                current_state="test",
                user_input="test",
                logger=logger
            )
            
            # All but last call return invalid JSON
            if call_count < 8:
                result.payload["llm_response"] = f"Invalid response {call_count}"
            else:
                # Last call (Claude) also invalid, but keep as fallback
                result.payload["llm_response"] = "Best effort response"
            
            return result
        
        mock_router.execute.side_effect = mock_execute
        
        # Call escalation
        response = await plugin._call_expert_llm("Test prompt")
        
        # Verify fallback response returned
        assert response == "Best effort response"
        
        # Should call all tiers (3+3+1+1 = 8)
        assert call_count == 8
        print("✅ All tiers exhausted, using fallback - 8 calls, $0.020")
    
    @pytest.mark.asyncio
    async def test_empty_response_retry(self, test_config, mock_router):
        """Test retry on empty responses."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        call_count = 0
        
        async def mock_execute(context):
            nonlocal call_count
            call_count += 1
            
            result = SharedContext(
                session_id="test",
                current_state="test",
                user_input="test",
                logger=logger
            )
            
            # First 2 calls return empty
            if call_count <= 2:
                result.payload["llm_response"] = ""
                return result
            
            # 3rd call succeeds
            valid_hypothesis = {
                "root_cause": "Fixed root cause",
                "hypothesis": "Fixed hypothesis",
                "proposed_fix": "Fixed fix",
                "fix_type": "config"
            }
            result.payload["llm_response"] = json.dumps(valid_hypothesis)
            return result
        
        mock_router.execute.side_effect = mock_execute
        
        # Call escalation
        response = await plugin._call_expert_llm("Test prompt")
        
        # Verify
        assert response is not None
        assert "Fixed" in response
        assert call_count == 3
        print("✅ Empty response retry - 3 calls, $0.00")
    
    @pytest.mark.asyncio
    async def test_json_validation_logic(self, test_config):
        """Test _validate_hypothesis_json method."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        # Valid JSON
        valid = json.dumps({
            "root_cause": "Test",
            "hypothesis": "Test",
            "proposed_fix": "Test",
            "fix_type": "code"
        })
        assert plugin._validate_hypothesis_json(valid) is True
        
        # Valid with markdown
        valid_md = f"```json\n{valid}\n```"
        assert plugin._validate_hypothesis_json(valid_md) is True
        
        # Missing field
        invalid_missing = json.dumps({
            "root_cause": "Test",
            "hypothesis": "Test"
            # Missing proposed_fix, fix_type
        })
        assert plugin._validate_hypothesis_json(invalid_missing) is False
        
        # Invalid JSON
        assert plugin._validate_hypothesis_json("Not JSON") is False
        
        print("✅ JSON validation working correctly")
    
    @pytest.mark.asyncio
    async def test_budget_savings_calculation(self, test_config, mock_router):
        """Test budget savings logging."""
        plugin = CognitiveReflection()
        plugin.setup(test_config)
        
        # Mock Tier 1 success
        valid_hypothesis = {
            "root_cause": "Test",
            "hypothesis": "Test",
            "proposed_fix": "Test",
            "fix_type": "code"
        }
        
        mock_context = SharedContext(
            session_id="test",
            current_state="test",
            user_input="test",
            logger=logger
        )
        mock_context.payload["llm_response"] = json.dumps(valid_hypothesis)
        mock_router.execute.return_value = mock_context
        
        # Capture logs
        with patch('plugins.cognitive_reflection.logger') as mock_logger:
            response = await plugin._call_expert_llm("Test prompt")
            
            # Verify budget savings logged
            # Max cost = 0 + 0 + 0.005 + 0.015 = 0.020
            # Actual cost = 0 (Tier 1)
            # Savings = 0.020 - 0 = 0.020 (100%)
            
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            budget_log = [log for log in log_calls if "saved" in log.lower()]
            
            # Should have budget savings log
            assert len(budget_log) > 0
            print("✅ Budget savings calculation logged")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
