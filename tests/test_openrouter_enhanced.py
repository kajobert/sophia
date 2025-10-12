"""
Tests for enhanced OpenRouterAdapter.

Validates new features:
- Billing tracking
- Generation parameters
- Provider preferences
- Enhanced usage data
- Cost calculation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.llm_adapters import OpenRouterAdapter


class TestOpenRouterAdapterEnhanced:
    """Test enhanced OpenRouter features."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock AsyncOpenAI client."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def adapter(self, mock_client):
        """Create OpenRouterAdapter with mock client."""
        return OpenRouterAdapter(
            model_name="anthropic/claude-3-haiku",
            client=mock_client,
            temperature=0.7,
            max_tokens=2000,
            provider_preferences=["Anthropic", "OpenAI"]
        )
    
    def test_init_with_custom_params(self, mock_client):
        """Test initialization with custom parameters."""
        adapter = OpenRouterAdapter(
            model_name="openai/gpt-4o",
            client=mock_client,
            fallback_models=["openai/gpt-4o-mini", "anthropic/claude-3-haiku"],
            temperature=0.5,
            top_p=0.9,
            max_tokens=1000,
            provider_preferences=["OpenAI"]
        )
        
        assert adapter.model_name == "openai/gpt-4o"
        assert adapter.temperature == 0.5
        assert adapter.top_p == 0.9
        assert adapter.max_tokens == 1000
        assert adapter.provider_preferences == ["OpenAI"]
        assert len(adapter.models_to_try) == 3  # primary + 2 fallbacks
    
    def test_billing_tracking_initialization(self, adapter):
        """Test billing tracking starts at zero."""
        assert adapter._total_cost == 0.0
        assert len(adapter._call_history) == 0
        
        summary = adapter.get_billing_summary()
        assert summary["total_cost"] == 0.0
        assert summary["total_calls"] == 0
        assert summary["total_tokens"] == 0
    
    @pytest.mark.asyncio
    async def test_generate_with_json_mode(self, adapter, mock_client):
        """Test generation with JSON mode enabled."""
        # Mock response
        mock_response = Mock()
        mock_response.id = "test-123"
        mock_response.model = "anthropic/claude-3-haiku"
        mock_response.choices = [Mock(message=Mock(content='{"name": "Alice"}'))]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Generate with JSON mode
        content, usage = await adapter.generate_content_async(
            prompt="Generate user profile",
            response_format={"type": "json_object"}
        )
        
        # Verify JSON mode was passed
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "response_format" in call_kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}
        
        # Verify content
        assert '"name": "Alice"' in content
        assert usage["usage"]["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_temperature(self, adapter, mock_client):
        """Test generation with custom temperature."""
        mock_response = Mock()
        mock_response.id = "test-123"
        mock_response.model = "anthropic/claude-3-haiku"
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Generate with custom temperature
        await adapter.generate_content_async(
            prompt="Test",
            temperature=0.9
        )
        
        # Verify temperature was overridden
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_billing_tracking_after_call(self, adapter, mock_client):
        """Test billing is tracked after generation."""
        mock_response = Mock()
        mock_response.id = "test-123"
        mock_response.model = "anthropic/claude-3-haiku"
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Make 2 calls
        await adapter.generate_content_async("Test 1")
        await adapter.generate_content_async("Test 2")
        
        # Check billing summary
        summary = adapter.get_billing_summary()
        
        assert summary["total_calls"] == 2
        assert summary["total_tokens"] == 300  # 150 * 2
        assert summary["total_cost"] > 0.0
        assert "anthropic/claude-3-haiku" in summary["by_model"]
        assert summary["by_model"]["anthropic/claude-3-haiku"]["calls"] == 2
    
    def test_cost_calculation_claude_haiku(self, adapter):
        """Test cost calculation for Claude Haiku."""
        cost = adapter._calculate_cost(
            model="anthropic/claude-3-haiku",
            prompt_tokens=1_000_000,  # 1M tokens
            completion_tokens=1_000_000
        )
        
        # Expected: (1M * 0.25) + (1M * 1.25) = $1.50
        assert cost == pytest.approx(1.50, rel=0.01)
    
    def test_cost_calculation_gpt4o(self, adapter):
        """Test cost calculation for GPT-4o."""
        cost = adapter._calculate_cost(
            model="openai/gpt-4o",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000
        )
        
        # Expected: (1M * 5.0) + (1M * 15.0) = $20.00
        assert cost == pytest.approx(20.00, rel=0.01)
    
    def test_cost_calculation_unknown_model(self, adapter):
        """Test cost calculation for unknown model returns 0."""
        cost = adapter._calculate_cost(
            model="unknown/model",
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        assert cost == 0.0
    
    def test_billing_group_by_model(self, adapter):
        """Test grouping billing by model."""
        # Simulate 3 calls to different models
        adapter._call_history = [
            {
                "model": "anthropic/claude-3-haiku",
                "usage": {"total_tokens": 100},
                "cost": 0.0001
            },
            {
                "model": "anthropic/claude-3-haiku",
                "usage": {"total_tokens": 150},
                "cost": 0.00015
            },
            {
                "model": "openai/gpt-4o-mini",
                "usage": {"total_tokens": 200},
                "cost": 0.0002
            }
        ]
        adapter._total_cost = 0.00045
        
        by_model = adapter._group_by_model()
        
        assert len(by_model) == 2
        assert by_model["anthropic/claude-3-haiku"]["calls"] == 2
        assert by_model["anthropic/claude-3-haiku"]["tokens"] == 250
        assert by_model["anthropic/claude-3-haiku"]["cost"] == pytest.approx(0.00025)
        assert by_model["openai/gpt-4o-mini"]["calls"] == 1
        assert by_model["openai/gpt-4o-mini"]["tokens"] == 200
    
    def test_reset_billing(self, adapter):
        """Test billing reset."""
        # Add some fake data
        adapter._total_cost = 1.5
        adapter._call_history = [{"mock": "data"}]
        
        # Reset
        adapter.reset_billing()
        
        assert adapter._total_cost == 0.0
        assert len(adapter._call_history) == 0
    
    def test_extract_usage_data_structure(self, adapter):
        """Test usage data extraction structure."""
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "anthropic/claude-3-haiku"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        usage_data = adapter._extract_usage_data(mock_response)
        
        assert "id" in usage_data
        assert "model" in usage_data
        assert "usage" in usage_data
        assert "cost" in usage_data
        assert "timestamp" in usage_data
        assert usage_data["model"] == "anthropic/claude-3-haiku"
        assert usage_data["usage"]["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_provider_preferences_in_request(self, adapter, mock_client):
        """Test provider preferences are sent in extra_body."""
        mock_response = Mock()
        mock_response.id = "test-123"
        mock_response.model = "anthropic/claude-3-haiku"
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        await adapter.generate_content_async("Test")
        
        # Verify extra_body with provider preferences
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        assert "provider" in call_kwargs["extra_body"]
        assert call_kwargs["extra_body"]["provider"]["order"] == ["Anthropic", "OpenAI"]
        assert call_kwargs["extra_body"]["provider"]["allow_fallbacks"] is True
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, adapter, mock_client):
        """Test fallback to secondary model on error."""
        # Configure adapter with fallback
        adapter.models_to_try = [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet"
        ]
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.id = "test-123"
        mock_response.model = "anthropic/claude-3-sonnet"  # Fallback model
        mock_response.choices = [Mock(message=Mock(content="Fallback response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("Primary model failed"),
                mock_response
            ]
        )
        
        content, usage = await adapter.generate_content_async("Test")
        
        assert content == "Fallback response"
        assert usage["model"] == "anthropic/claude-3-sonnet"
        assert mock_client.chat.completions.create.call_count == 2


class TestBillingCalculations:
    """Test billing calculation accuracy."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter for billing tests."""
        mock_client = AsyncMock()
        return OpenRouterAdapter(
            model_name="test/model",
            client=mock_client
        )
    
    def test_micro_transaction_precision(self, adapter):
        """Test that micro-transactions maintain precision."""
        cost = adapter._calculate_cost(
            model="google/gemini-2.0-flash-exp",
            prompt_tokens=100,
            completion_tokens=50
        )
        
        # Small transaction should have high precision
        assert isinstance(cost, float)
        assert cost > 0
        assert cost < 0.001  # Less than 0.1 cent
    
    def test_large_transaction_calculation(self, adapter):
        """Test calculation for large token counts."""
        cost = adapter._calculate_cost(
            model="anthropic/claude-3-opus",
            prompt_tokens=10_000_000,  # 10M tokens
            completion_tokens=5_000_000  # 5M tokens
        )
        
        # Expected: (10M * 15.0) + (5M * 75.0) = $525.00
        assert cost == pytest.approx(525.00, rel=0.01)
    
    def test_cost_rounding(self, adapter):
        """Test cost is rounded to 8 decimal places."""
        cost = adapter._calculate_cost(
            model="google/gemini-2.0-flash-exp",
            prompt_tokens=1,
            completion_tokens=1
        )
        
        # Should be rounded to 8 decimals
        assert len(str(cost).split('.')[-1]) <= 8
