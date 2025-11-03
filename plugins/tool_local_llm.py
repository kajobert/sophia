"""
Local LLM Tool Plugin

Provides support for running LLMs locally via:
- Ollama (recommended) - Easy setup, great performance
- LM Studio - GUI-based alternative
- llamafile - Single-file executables

Supports models like:
- Gemma 2/3 (Google)
- Llama 3/3.1/3.2 (Meta)
- Mistral/Mixtral (Mistral AI)
- Phi-3 (Microsoft)
- Qwen (Alibaba)

Version: 1.0.0
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class LocalModelConfig(BaseModel):
    """Configuration for local LLM runtime."""
    runtime: str = Field("ollama", description="Runtime type: ollama, lmstudio, llamafile")
    base_url: str = Field("http://localhost:11434", description="Base URL for local runtime")
    model: str = Field("gemma2:2b", description="Model identifier")
    timeout: int = Field(120, description="Request timeout in seconds")
    max_tokens: int = Field(2048, description="Maximum output tokens")
    temperature: float = Field(0.7, description="Sampling temperature")


class LocalLLMTool(BasePlugin):
    """
    Local LLM Tool Plugin
    
    Enables cost-free, private LLM inference using locally-run models.
    Perfect for development, experimentation, and privacy-sensitive tasks.
    
    Tool Definition:
    - execute_local_llm: Generate text using local model
    """

    @property
    def name(self) -> str:
        """Returns the unique name of the plugin."""
        return "tool_local_llm"

    @property
    def plugin_type(self) -> PluginType:
        """Returns the type of the plugin."""
        return PluginType.TOOL

    @property
    def version(self) -> str:
        """Returns the version of the plugin."""
        return "1.0.0"
    
    def setup(self, config: Dict[str, Any]) -> None:
        """
        Initialize local LLM configuration.
        
        Args:
            config: Plugin configuration
        """
        self.config = LocalModelConfig(**config.get("local_llm", {}))
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        
        logger.info(
            f"Local LLM initialized: {self.config.runtime} @ {self.config.base_url}, "
            f"model={self.config.model}"
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This is a tool plugin - execution happens via tool calls.
        
        Args:
            context: Shared context object
            
        Returns:
            Unchanged context
        """
        return context
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using local LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        if self.config.runtime == "ollama":
            return await self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
        elif self.config.runtime == "lmstudio":
            return await self._generate_lmstudio(prompt, system_prompt, temperature, max_tokens)
        elif self.config.runtime == "llamafile":
            return await self._generate_llamafile(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown runtime: {self.config.runtime}")
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """
        Generate using Ollama runtime.
        
        Ollama API: POST /api/generate
        """
        url = f"{self.config.base_url}/api/generate"
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request
        request = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }
        
        try:
            logger.info(f"🤖 Calling Ollama: model={self.config.model}, prompt_len={len(prompt)}")
            
            response = await self.client.post(url, json=request)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            logger.info(f"✅ Ollama response: {len(generated_text)} chars")
            
            return generated_text
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}", exc_info=True)
            raise
    
    async def _generate_lmstudio(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """
        Generate using LM Studio runtime.
        
        LM Studio uses OpenAI-compatible API.
        """
        url = f"{self.config.base_url}/v1/chat/completions"
        
        # Build messages (OpenAI format)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        request = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }
        
        try:
            logger.info(f"🤖 Calling LM Studio: model={self.config.model}")
            
            response = await self.client.post(url, json=request)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            
            logger.info(f"✅ LM Studio response: {len(generated_text)} chars")
            
            return generated_text
        
        except Exception as e:
            logger.error(f"❌ LM Studio error: {e}", exc_info=True)
            raise
    
    async def _generate_llamafile(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """
        Generate using llamafile runtime.
        
        llamafile also uses OpenAI-compatible API.
        """
        # Same as LM Studio
        return await self._generate_lmstudio(prompt, system_prompt, temperature, max_tokens)
    
    async def check_availability(self) -> bool:
        """
        Check if local LLM runtime is available.
        
        Returns:
            True if runtime is accessible
        """
        try:
            if self.config.runtime == "ollama":
                # Check Ollama /api/tags endpoint
                response = await self.client.get(f"{self.config.base_url}/api/tags")
                response.raise_for_status()
                
                # Check if our model is available
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                
                if self.config.model not in model_names:
                    logger.warning(
                        f"Model {self.config.model} not found. Available: {model_names[:5]}"
                    )
                    return False
                
                return True
            
            else:
                # For LM Studio/llamafile, try a simple health check
                response = await self.client.get(f"{self.config.base_url}/health")
                return response.status_code == 200
        
        except Exception as e:
            logger.warning(f"Local LLM not available: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available models in local runtime.
        
        Returns:
            List of model names
        """
        try:
            if self.config.runtime == "ollama":
                response = await self.client.get(f"{self.config.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                return [m.get("name") for m in models]
            
            else:
                # LM Studio/llamafile don't have model listing
                return [self.config.model]
        
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions for LLM function calling.
        
        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_local_llm",
                    "description": (
                        "Generate text using a locally-running LLM (Ollama/Gemma/Llama). "
                        "Perfect for cost-free operations, privacy-sensitive tasks, "
                        "or when internet is unavailable. "
                        f"Current model: {self.config.model}"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt for text generation"
                            },
                            "system_prompt": {
                                "type": "string",
                                "description": "Optional system prompt for context"
                            },
                            "temperature": {
                                "type": "number",
                                "description": "Sampling temperature (0.0-1.0)",
                                "default": 0.7
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum output tokens",
                                "default": 2048
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_local_llm_status",
                    "description": (
                        "Check if local LLM is available and list available models. "
                        "Useful for debugging and model discovery."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: SharedContext
    ) -> Dict[str, Any]:
        """
        Execute a tool function.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Shared context
            
        Returns:
            Tool execution result
        """
        if tool_name == "execute_local_llm":
            try:
                result = await self.generate(
                    prompt=arguments["prompt"],
                    system_prompt=arguments.get("system_prompt"),
                    temperature=arguments.get("temperature"),
                    max_tokens=arguments.get("max_tokens")
                )
                
                return {
                    "success": True,
                    "result": result,
                    "model": self.config.model,
                    "runtime": self.config.runtime,
                    "cost": 0.0  # Local = free!
                }
            
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "suggestion": "Check if Ollama/LM Studio is running and model is downloaded"
                }
        
        elif tool_name == "check_local_llm_status":
            try:
                available = await self.check_availability()
                models = await self.list_models()
                
                return {
                    "success": True,
                    "available": available,
                    "runtime": self.config.runtime,
                    "base_url": self.config.base_url,
                    "current_model": self.config.model,
                    "available_models": models[:10],  # Limit output
                    "total_models": len(models)
                }
            
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
