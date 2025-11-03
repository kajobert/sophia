"""
Unit tests for LocalLLMTool plugin.

Tests local LLM integration with Ollama, LM Studio, and llamafile.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from plugins.tool_local_llm import (
    LocalLLMTool,
    LocalModelConfig
)
from plugins.base_plugin import PluginType
from core.context import SharedContext


@pytest.fixture
def local_llm():
    """Create a LocalLLMTool instance for testing."""
    plugin = LocalLLMTool()
    config = {
        "local_llm": {
            "runtime": "ollama",
            "base_url": "http://localhost:11434",
            "model": "gemma2:2b",
            "timeout": 60,
            "max_tokens": 1024,
            "temperature": 0.7
        }
    }
    plugin.setup(config)
    return plugin


@pytest.fixture
def mock_context():
    """Create a mock SharedContext."""
    import logging
    return SharedContext(
        session_id="test_session",
        current_state="processing",
        logger=logging.getLogger("test"),
        user_input="test input"
    )


class TestPluginMetadata:
    """Test plugin metadata and initialization."""
    
    def test_plugin_name(self, local_llm):
        """Test plugin name."""
        assert local_llm.name == "tool_local_llm"
    
    def test_plugin_type(self, local_llm):
        """Test plugin type."""
        assert local_llm.plugin_type == PluginType.TOOL
    
    def test_plugin_version(self, local_llm):
        """Test plugin version."""
        assert local_llm.version == "1.0.0"
    
    def test_config_loading(self, local_llm):
        """Test configuration is loaded correctly."""
        assert local_llm.config.runtime == "ollama"
        assert local_llm.config.base_url == "http://localhost:11434"
        assert local_llm.config.model == "gemma2:2b"
        assert local_llm.config.max_tokens == 1024


class TestConfiguration:
    """Test configuration models."""
    
    def test_local_model_config_defaults(self):
        """Test LocalModelConfig default values."""
        config = LocalModelConfig()
        assert config.runtime == "ollama"
        assert config.base_url == "http://localhost:11434"
        assert config.model == "gemma2:2b"
        assert config.timeout == 120
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
    
    def test_local_model_config_custom(self):
        """Test LocalModelConfig with custom values."""
        config = LocalModelConfig(
            runtime="lmstudio",
            base_url="http://localhost:1234",
            model="llama3:8b",
            timeout=300,
            max_tokens=4096,
            temperature=0.5
        )
        assert config.runtime == "lmstudio"
        assert config.base_url == "http://localhost:1234"
        assert config.model == "llama3:8b"
        assert config.timeout == 300
        assert config.max_tokens == 4096
        assert config.temperature == 0.5


class TestOllamaIntegration:
    """Test Ollama runtime integration."""
    
    @pytest.mark.asyncio
    async def test_generate_ollama_success(self, local_llm):
        """Test successful text generation with Ollama."""
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "This is a test response from Ollama"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(local_llm.client, 'post', new=AsyncMock(return_value=mock_response)):
            result = await local_llm.generate(
                prompt="Test prompt",
                system_prompt="You are helpful",
                temperature=0.7
            )
        
        assert result == "This is a test response from Ollama"
    
    @pytest.mark.asyncio
    async def test_generate_ollama_http_error(self, local_llm):
        """Test Ollama HTTP error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        
        with patch.object(local_llm.client, 'post', new=AsyncMock(return_value=mock_response)):
            with pytest.raises(httpx.HTTPStatusError):
                await local_llm.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_check_availability_ollama_success(self, local_llm):
        """Test Ollama availability check - model available."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "gemma2:2b"},
                {"name": "llama3:8b"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(local_llm.client, 'get', new=AsyncMock(return_value=mock_response)):
            available = await local_llm.check_availability()
        
        assert available is True
    
    @pytest.mark.asyncio
    async def test_check_availability_ollama_model_missing(self, local_llm):
        """Test Ollama availability check - model not downloaded."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:8b"}  # gemma2:2b not in list
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(local_llm.client, 'get', new=AsyncMock(return_value=mock_response)):
            available = await local_llm.check_availability()
        
        assert available is False
    
    @pytest.mark.asyncio
    async def test_list_models_ollama(self, local_llm):
        """Test listing available models in Ollama."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "gemma2:2b"},
                {"name": "llama3:8b"},
                {"name": "mistral:7b"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(local_llm.client, 'get', new=AsyncMock(return_value=mock_response)):
            models = await local_llm.list_models()
        
        assert len(models) == 3
        assert "gemma2:2b" in models
        assert "llama3:8b" in models


class TestLMStudioIntegration:
    """Test LM Studio runtime integration."""
    
    @pytest.mark.asyncio
    async def test_generate_lmstudio_success(self):
        """Test successful text generation with LM Studio."""
        plugin = LocalLLMTool()
        config = {
            "local_llm": {
                "runtime": "lmstudio",
                "base_url": "http://localhost:1234",
                "model": "gemma-2-2b-it"
            }
        }
        plugin.setup(config)
        
        # Mock OpenAI-compatible response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "LM Studio response"
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(plugin.client, 'post', new=AsyncMock(return_value=mock_response)):
            result = await plugin.generate("Test prompt")
        
        assert result == "LM Studio response"


class TestToolDefinitions:
    """Test LLM tool definitions."""
    
    def test_get_tool_definitions(self, local_llm):
        """Test tool definitions are provided."""
        tools = local_llm.get_tool_definitions()
        
        assert len(tools) == 2
        
        tool_names = [t["function"]["name"] for t in tools]
        assert "execute_local_llm" in tool_names
        assert "check_local_llm_status" in tool_names
    
    def test_execute_local_llm_tool_schema(self, local_llm):
        """Test execute_local_llm tool schema."""
        tools = local_llm.get_tool_definitions()
        exec_tool = next(
            t for t in tools if t["function"]["name"] == "execute_local_llm"
        )
        
        params = exec_tool["function"]["parameters"]["properties"]
        assert "prompt" in params
        assert "system_prompt" in params
        assert "temperature" in params
        assert "max_tokens" in params
        
        # Check required fields
        required = exec_tool["function"]["parameters"]["required"]
        assert "prompt" in required


class TestToolExecution:
    """Test tool execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_execute_local_llm(self, local_llm, mock_context):
        """Test execute_local_llm tool execution."""
        # Mock generate method
        with patch.object(local_llm, 'generate', new=AsyncMock(return_value="Generated text")):
            result = await local_llm.execute_tool(
                "execute_local_llm",
                {
                    "prompt": "Test prompt",
                    "temperature": 0.5
                },
                mock_context
            )
        
        assert result["success"] is True
        assert result["result"] == "Generated text"
        assert result["model"] == "gemma2:2b"
        assert result["cost"] == 0.0  # Local is free!
    
    @pytest.mark.asyncio
    async def test_execute_tool_execute_local_llm_error(self, local_llm, mock_context):
        """Test execute_local_llm handles errors gracefully."""
        # Mock generate to raise error
        with patch.object(local_llm, 'generate', new=AsyncMock(side_effect=Exception("Connection failed"))):
            result = await local_llm.execute_tool(
                "execute_local_llm",
                {"prompt": "Test"},
                mock_context
            )
        
        assert result["success"] is False
        assert "Connection failed" in result["error"]
        assert "Ollama" in result["suggestion"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_check_status(self, local_llm, mock_context):
        """Test check_local_llm_status tool execution."""
        # Mock availability check and model listing
        with patch.object(local_llm, 'check_availability', new=AsyncMock(return_value=True)), \
             patch.object(local_llm, 'list_models', new=AsyncMock(return_value=["gemma2:2b", "llama3:8b"])):
            
            result = await local_llm.execute_tool(
                "check_local_llm_status",
                {},
                mock_context
            )
        
        assert result["success"] is True
        assert result["available"] is True
        assert result["runtime"] == "ollama"
        assert result["current_model"] == "gemma2:2b"
        assert len(result["available_models"]) == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_unknown_tool(self, local_llm, mock_context):
        """Test unknown tool returns error."""
        result = await local_llm.execute_tool(
            "unknown_tool",
            {},
            mock_context
        )
        
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestExecuteMethod:
    """Test execute() method."""
    
    @pytest.mark.asyncio
    async def test_execute_returns_context_unchanged(self, local_llm, mock_context):
        """Test execute() is passive and returns context unchanged."""
        result = await local_llm.execute(mock_context)
        
        assert result is mock_context
