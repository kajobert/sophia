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

Version: 1.1.0 - Function calling support added
"""

import logging
import httpx
import requests  # Sync HTTP for Ollama (avoids httpx async lock issues in Sophia event loop)
import json
from typing import Dict, Any, List, Optional
from types import SimpleNamespace
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
    
    # Advanced Ollama parameters for maximum quality
    num_ctx: Optional[int] = Field(None, description="Context window size (Ollama num_ctx)")
    num_predict: Optional[int] = Field(None, description="Max tokens to predict (Ollama num_predict)")
    num_gpu: Optional[int] = Field(None, description="GPU layers to offload (0 = CPU only)")
    num_thread: Optional[int] = Field(None, description="CPU threads to use")
    repeat_penalty: Optional[float] = Field(None, description="Penalty for repetition")
    top_k: Optional[int] = Field(None, description="Top-K sampling")
    top_p: Optional[float] = Field(None, description="Nucleus sampling threshold")
    escalation_model: Optional[str] = Field(None, description="Model for Tier 2 escalation")


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
        # Don't create shared client here - create fresh client per request to avoid connection issues
        # self.client = httpx.AsyncClient(timeout=self.config.timeout)
        # Expose a `client` attribute so tests and callers can monkeypatch or inspect it.
        # Clients should be created per call to avoid event-loop conflicts, but
        # having this attribute present avoids AttributeErrors in tests.
        # Provide a lightweight client object so tests can patch .post/.get methods
        # Default client placeholders - leave .post/.get as None so the
        # implementation falls back to the synchronous `requests` library.
        self.client = SimpleNamespace(post=None, get=None)

        # Use offline-specific prompt if offline_mode is set in config
        offline_mode = config.get("offline_mode", False)
        if offline_mode:
            prompt_path = "config/prompts/sophia_dna_offline.txt"
        else:
            prompt_path = "config/prompts/sophia_dna.txt"

        self.system_prompt = "You are Sophia, a helpful AI assistant."
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
                logger.info(f"System prompt loaded from {prompt_path}")
        except FileNotFoundError:
            logger.warning(f"{prompt_path} not found - using default system prompt")

        logger.info(
            f"Local LLM initialized: {self.config.runtime} @ {self.config.base_url}, "
            f"model={self.config.model}"
        )

        # Quick synchronous health probe (best-effort). We do this synchronously
        # to keep setup simple and avoid requiring an active asyncio loop here.
        try:
            probe_url = self.config.base_url
            if self.config.runtime == "ollama":
                probe_url = f"{self.config.base_url}/api/tags"
            else:
                probe_url = f"{self.config.base_url}/health"

            logger.info(f"Probing local LLM runtime at {probe_url}", extra={"plugin_name": self.name})
            resp = requests.get(probe_url, timeout=5)
            if resp is None:
                logger.warning("Local LLM probe returned no response (None)", extra={"plugin_name": self.name})
            elif not resp.ok:
                logger.warning(f"Local LLM probe returned status {resp.status_code}", extra={"plugin_name": self.name})
            else:
                try:
                    j = resp.json()
                    # If Ollama, warn if configured model not present
                    if self.config.runtime == "ollama":
                        models = j.get("models", []) if isinstance(j, dict) else []
                        model_names = [m.get("name") for m in models if isinstance(m, dict)]
                        if self.config.model not in model_names:
                            logger.warning(
                                f"Configured model '{self.config.model}' not found locally. Available: {model_names[:6]}",
                                extra={"plugin_name": self.name},
                            )
                        else:
                            logger.info(f"Local model '{self.config.model}' is present", extra={"plugin_name": self.name})
                except Exception:
                    # Non-fatal; best-effort only
                    logger.debug("Local LLM probe returned non-JSON response", extra={"plugin_name": self.name})
        except Exception as e:
            logger.warning(f"Local LLM probe failed: {e}", extra={"plugin_name": self.name})
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Generate a response using local LLM with function calling support.
        Compatible with tool_llm interface for drop-in replacement.

        Args:
            context: Shared context object

        Returns:
            Updated context with llm_response in payload
        """
        prompt = context.payload.get("prompt", context.user_input)
        tools = context.payload.get("tools")  # Function calling tools (NOW SUPPORTED!)
        tool_choice = context.payload.get("tool_choice")
        
        if not prompt:
            context.payload["llm_response"] = {"content": "Error: No input provided to LocalLLMTool."}
            return context
        
        # Build messages from history (keep as array!)
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(context.history)
        
        # Add current prompt if not in history
        if not any(msg["role"] == "user" and msg["content"] == prompt for msg in messages):
            messages.append({"role": "user", "content": prompt})
        
        context.logger.info(
            f"Calling local LLM '{self.config.model}' with {len(messages)} messages"
            + (f" and {len(tools)} tools" if tools else ""),
            extra={"plugin_name": self.name},
        )
        
        try:
            # Use Ollama /api/chat with function calling support
            if self.config.runtime == "ollama":
                response_message = await self._generate_ollama(
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            else:
                # Fallback for other runtimes (LM Studio, llamafile)
                # They also support OpenAI-compatible /chat/completions
                response_message = await self._generate_lmstudio_chat(
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            
            # Store response matching tool_llm format:
            # - If tool_calls present, convert to LiteLLM-compatible objects
            # - Otherwise store content string
            if response_message.get("tool_calls"):
                # Convert Ollama tool_calls (dict) to LiteLLM format (objects)
                tool_calls = []
                for tc in response_message["tool_calls"]:
                    # Ollama format: {"function": {"name": "...", "arguments": {...}}}
                    # LiteLLM format: object with .function.name and .function.arguments
                    tool_call_obj = SimpleNamespace(
                        function=SimpleNamespace(
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"]
                        )
                    )
                    tool_calls.append(tool_call_obj)
                
                context.payload["llm_response"] = tool_calls
                context.logger.info(
                    f"LLM response with {len(tool_calls)} tool calls",
                    extra={"plugin_name": self.name},
                )
            else:
                context.payload["llm_response"] = response_message.get("content", "")
                context.logger.info(
                    "LLM response received successfully",
                    extra={"plugin_name": self.name},
                )
            
        except Exception as e:
            error_msg = f"Error calling local LLM: {e}"
            context.logger.error(error_msg, extra={"plugin_name": self.name})
            context.payload["llm_response"] = {"content": f"Error: {error_msg}"}
        
        return context

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        LEGACY METHOD: Generate text using local LLM (simple string-based interface).
        
        This is kept for backward compatibility with execute_tool() and direct calls.
        For function calling support, use execute() instead.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text (string only, no tool calls)
        """
        # Build messages for new API
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Call new _generate_ollama (without tools)
        if self.config.runtime == "ollama":
            response_message = await self._generate_ollama(
                messages=messages,
                tools=None,  # No function calling in legacy mode
                temperature=temperature,
                max_tokens=max_tokens
            )
            # Return just the text content
            return response_message.get("content", "")
        
        elif self.config.runtime == "lmstudio":
            return await self._generate_lmstudio(prompt, system_prompt, temperature, max_tokens)
        elif self.config.runtime == "llamafile":
            return await self._generate_llamafile(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown runtime: {self.config.runtime}")

    async def _generate_ollama(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate using Ollama runtime with function calling support.

        Ollama API: POST /api/chat
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions (OpenAI format)
            tool_choice: Optional tool choice strategy
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Full message object with content and/or tool_calls
        """
        url = f"{self.config.base_url}/api/chat"

        # Allow model override via environment variable (for model escalation)
        import os
        model_to_use = os.getenv("LOCAL_LLM_MODEL_OVERRIDE") or self.config.model
        
        # Build base options with temperature and token limits
        options = {
            "temperature": temperature or self.config.temperature,
            "num_predict": max_tokens or self.config.max_tokens,
        }
        
        # Add advanced Ollama parameters if configured (for maximum quality)
        if self.config.num_ctx is not None:
            options["num_ctx"] = self.config.num_ctx
        if self.config.num_predict is not None and max_tokens is None:
            options["num_predict"] = self.config.num_predict
        if self.config.num_gpu is not None:
            options["num_gpu"] = self.config.num_gpu
        if self.config.num_thread is not None:
            options["num_thread"] = self.config.num_thread
        if self.config.repeat_penalty is not None:
            options["repeat_penalty"] = self.config.repeat_penalty
        if self.config.top_k is not None:
            options["top_k"] = self.config.top_k
        if self.config.top_p is not None:
            options["top_p"] = self.config.top_p
        
        # Build request
        request = {
            "model": model_to_use,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        
        # Add JSON format requirement if prompt asks for JSON
        if messages and len(messages) > 0:
            last_message = messages[-1].get("content", "")
            if "JSON" in last_message or "json" in last_message:
                request["format"] = "json"
                logger.info("🔧 Ollama JSON mode enabled (detected JSON keyword in prompt)")
        
        # Add tools if provided (function calling)
        if tools:
            request["tools"] = tools

        max_attempts = 3
        backoff_base = 0.6
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"🤖 Calling Ollama /api/chat: model={model_to_use}, "
                    f"messages={len(messages)}"
                    + (f", tools={len(tools)}" if tools else "")
                )

                # Debug: Log request size
                request_json = json.dumps(request)
                logger.debug(f"Request size: {len(request_json)} bytes")
                logger.debug(f"Request preview: {request_json[:500]}")

                # CRITICAL DEBUG: Log before HTTP call
                logger.info(f"🔍 DEBUG: About to POST to {url}")

                # Prefer an injected client (useful for tests/mocking). If not present,
                # fall back to synchronous requests.post.
                import asyncio

                if hasattr(self, "client") and getattr(self.client, "post", None):
                    post_fn = getattr(self.client, "post")
                    if asyncio.iscoroutinefunction(post_fn) or asyncio.iscoroutine(post_fn):
                        response = await post_fn(url, json=request, timeout=self.config.timeout)
                    else:
                        response = post_fn(url, json=request, timeout=self.config.timeout)
                else:
                    # Use sync requests library instead of httpx (avoids async event loop conflicts)
                    response = requests.post(url, json=request, timeout=self.config.timeout)

                # Basic response validation
                if response is None:
                    raise RuntimeError("No response object received from Ollama (None)")

                status = getattr(response, "status_code", None)
                if status is not None:
                    logger.info(f"🔍 DEBUG: POST completed, status={status}")
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()

                # Parse JSON safely without assuming response.json exists or is callable
                json_fn = getattr(response, "json", None)
                if callable(json_fn):
                    try:
                        result = json_fn()
                    except Exception as je:
                        raise RuntimeError(f"Received non-JSON response from Ollama: {je}")
                else:
                    text = getattr(response, "text", None)
                    if text:
                        try:
                            result = json.loads(text)
                        except Exception as je:
                            raise RuntimeError(f"Received non-JSON text response from Ollama: {je}")
                    else:
                        raise RuntimeError("Ollama response object has no json/text to parse")

                # Support multiple response shapes:
                # - Ollama runtime: {'message': {...}}
                # - Some tests/mocks: {'response': 'text'}
                # - LM Studio style: {'choices': [{'message': {...}}]}
                message = result.get("message") if isinstance(result, dict) and "message" in result else result
                if isinstance(message, dict):
                    if "response" in message:
                        message = {"content": message.get("response")}
                    elif "choices" in message and isinstance(message.get("choices"), list):
                        # Convert OpenAI-style choice wrapper
                        choice = message["choices"][0]
                        message = choice.get("message", {}) if isinstance(choice, dict) else message
                else:
                    message = {"content": message}

                # Log response details
                tool_calls_list = message.get("tool_calls") or []
                has_tool_calls = bool(tool_calls_list)
                content_len = len(message.get("content", "") or "")
                logger.info(
                    f"✅ Ollama response: content={content_len} chars"
                    + (f", tool_calls={len(tool_calls_list)}" if has_tool_calls else "")
                )

                return message

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{max_attempts} failed calling Ollama: {e}", extra={"plugin_name": self.name})
                if attempt < max_attempts:
                    sleep_for = backoff_base * (2 ** (attempt - 1))
                    logger.info(f"Retrying Ollama call in {sleep_for:.1f}s (attempt {attempt+1})", extra={"plugin_name": self.name})
                    import asyncio as _asyncio

                    await _asyncio.sleep(sleep_for)
                    continue
                else:
                    logger.error(f"All {max_attempts} Ollama attempts failed. Last error: {last_exception}", extra={"plugin_name": self.name})
                    raise

        # If we exit the loop without returning, raise the last exception for clarity
        if last_exception:
            raise last_exception
        raise RuntimeError("Ollama call failed without exception")

    async def _generate_lmstudio(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> str:
        """
        LEGACY METHOD: Generate using LM Studio runtime (string-based).
        For function calling, use _generate_lmstudio_chat() instead.

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
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        try:
            logger.info(f"🤖 Calling LM Studio: model={self.config.model}")

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=request)
                response.raise_for_status()

                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]

                logger.info(f"✅ LM Studio response: {len(generated_text)} chars")

                return generated_text

        except Exception as e:
            logger.error(f"❌ LM Studio error: {e}", exc_info=True)
            raise
    
    async def _generate_lmstudio_chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate using LM Studio with function calling support.
        
        LM Studio uses OpenAI-compatible /v1/chat/completions API.
        
        Args:
            messages: List of message dicts
            tools: Optional tool definitions
            tool_choice: Optional tool choice strategy
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Full message object with content and/or tool_calls
        """
        url = f"{self.config.base_url}/v1/chat/completions"

        request = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        
        # Add tools if provided
        if tools:
            request["tools"] = tools
        if tool_choice:
            request["tool_choice"] = tool_choice

        try:
            logger.info(
                f"🤖 Calling LM Studio /v1/chat/completions: model={self.config.model}, "
                f"messages={len(messages)}"
                + (f", tools={len(tools)}" if tools else "")
            )

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=request)
                response.raise_for_status()

                result = response.json()
                message = result["choices"][0]["message"]
                
                # Convert to dict if needed
                if hasattr(message, "model_dump"):
                    message = message.model_dump()
                
                has_tool_calls = bool(message.get("tool_calls"))
                content_len = len(message.get("content", "") or "")
                logger.info(
                    f"✅ LM Studio response: content={content_len} chars"
                    + (f", tool_calls={len(message.get('tool_calls', []))}" if has_tool_calls else "")
                )

                return message

        except Exception as e:
            logger.error(f"❌ LM Studio error: {e}", exc_info=True)
            raise

    async def _generate_llamafile(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
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
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{self.config.base_url}/api/tags")
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
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{self.config.base_url}/health")
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
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{self.config.base_url}/api/tags")
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
                                "description": "The prompt for text generation",
                            },
                            "system_prompt": {
                                "type": "string",
                                "description": "Optional system prompt for context",
                            },
                            "temperature": {
                                "type": "number",
                                "description": "Sampling temperature (0.0-1.0)",
                                "default": 0.7,
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum output tokens",
                                "default": 2048,
                            },
                        },
                        "required": ["prompt"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_local_llm_status",
                    "description": (
                        "Check if local LLM is available and list available models. "
                        "Useful for debugging and model discovery."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], context: SharedContext
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
                    max_tokens=arguments.get("max_tokens"),
                )

                return {
                    "success": True,
                    "result": result,
                    "model": self.config.model,
                    "runtime": self.config.runtime,
                    "cost": 0.0,  # Local = free!
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "suggestion": "Check if Ollama/LM Studio is running and model is downloaded",
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
                    "total_models": len(models),
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
