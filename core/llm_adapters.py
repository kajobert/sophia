import os
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from openai import OpenAI, AsyncOpenAI
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """
    Abstraktní základní třída pro všechny LLM adaptéry.
    Definuje jednotné rozhraní pro interakci s jazykovými modely.
    """
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    @abstractmethod
    async def generate_content_async(self, prompt: str, response_format: dict | None = None) -> tuple[str, dict | None]:
        """
        Asynchronně generuje obsah.

        Vrací:
            tuple[str, dict | None]: Vygenerovaný text a informace o použití (včetně ID generace).
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        Odhadne počet tokenů v textu. Pro OpenRouter se spoléháme na data z odpovědi,
        takže tato metoda nemusí být přesná a je spíše orientační.
        """
        # Jednoduchý odhad: 1 token ~ 4 znaky
        return len(text) // 4


from core.rich_printer import RichPrinter

class OpenRouterAdapter(BaseLLMAdapter):
    """
    Full-featured OpenRouter adapter with comprehensive API support.
    
    Features:
    - JSON mode (enforced structured output)
    - Custom generation parameters (temperature, top_p, max_tokens, etc.)
    - Provider preferences
    - Billing tracking with cost calculation
    - Enhanced usage data extraction
    - Fallback strategy
    - Stream support
    
    Example:
        ```python
        adapter = OpenRouterAdapter(
            model_name="anthropic/claude-3-haiku",
            client=async_client,
            temperature=0.7,
            max_tokens=4096,
            provider_preferences=["Anthropic", "OpenAI"]
        )
        
        # With JSON mode
        response, usage = await adapter.generate_content_async(
            prompt="Generate user profile",
            response_format={"type": "json_object"}
        )
        
        # Check billing
        summary = adapter.get_billing_summary()
        print(f"Total cost: ${summary['total_cost']:.4f}")
        ```
    """
    
    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI,
        fallback_models: Optional[List[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096,
        provider_preferences: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize OpenRouter adapter.
        
        Args:
            model_name: Primary model identifier (e.g., "anthropic/claude-3-haiku")
            client: AsyncOpenAI client configured for OpenRouter
            fallback_models: List of fallback models to try if primary fails
            temperature: Sampling temperature (0.0-2.0)
            top_p: Nucleus sampling threshold
            max_tokens: Maximum tokens to generate
            provider_preferences: Preferred providers in order (e.g., ["OpenAI", "Anthropic"])
            **kwargs: Additional parameters (system_prompt, etc.)
        """
        super().__init__(model_name=model_name)
        self._client = client
        self.system_prompt = kwargs.get("system_prompt", "")
        
        # Generation parameters
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.provider_preferences = provider_preferences or []
        
        # Fallback strategy
        self.models_to_try = [self.model_name] + (fallback_models or [])
        
        # Billing tracking
        self._total_cost = 0.0
        self._call_history: List[Dict[str, Any]] = []
        
        logger.info(f"OpenRouterAdapter initialized: model={model_name}, temp={temperature}, max_tokens={max_tokens}")
    
    async def generate_content_async(
        self,
        prompt: str,
        response_format: Optional[Dict] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        stream_callback: Optional[Callable] = None,
        **kwargs
    ) -> tuple[str, Dict]:
        """
        Generate content with full parameter support.
        
        Args:
            prompt: User prompt
            response_format: Force response format (e.g., {"type": "json_object"})
            temperature: Override default temperature
            max_tokens: Override default max tokens
            tools: Function calling tools definition
            stream_callback: Callback for streaming (async callable)
            **kwargs: Additional OpenRouter parameters
        
        Returns:
            tuple[str, Dict]: (generated_text, usage_data)
            
        Raises:
            Exception: If all models (including fallbacks) fail
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Build generation parameters
        gen_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": self.top_p,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        # JSON mode
        if response_format:
            gen_params["response_format"] = response_format
            logger.debug(f"JSON mode enabled: {response_format}")
        
        # Function calling
        if tools:
            gen_params["tools"] = tools
            gen_params["tool_choice"] = kwargs.get("tool_choice", "auto")
            logger.debug(f"Function calling enabled: {len(tools)} tools")
        
        # Provider preferences
        extra_body = {}
        if self.provider_preferences:
            extra_body["provider"] = {
                "order": self.provider_preferences,
                "allow_fallbacks": True
            }
            logger.debug(f"Provider preferences: {self.provider_preferences}")
        
        if extra_body:
            gen_params["extra_body"] = extra_body
        
        # Execute with fallback strategy
        last_error = None
        for model_name in self.models_to_try:
            try:
                if model_name != self.model_name:
                    RichPrinter.warning(
                        f"Primary model '{self.model_name}' failed. "
                        f"Trying fallback: [bold cyan]{model_name}[/bold cyan]"
                    )
                
                gen_params["model"] = model_name
                
                if stream_callback:
                    # Streaming mode
                    return await self._generate_stream(gen_params, stream_callback)
                else:
                    # Non-streaming mode
                    response = await self._client.chat.completions.create(**gen_params)
                    
                    # Extract content
                    content = response.choices[0].message.content
                    
                    # Extract enhanced usage data
                    usage_data = self._extract_usage_data(response)
                    
                    # Track billing
                    self._track_billing(usage_data)
                    
                    logger.debug(
                        f"Generation successful: model={response.model}, "
                        f"tokens={usage_data['usage'].get('total_tokens', 0)}, "
                        f"cost=${usage_data.get('cost', 0):.6f}"
                    )
                    
                    return content, usage_data
            
            except Exception as e:
                last_error = e
                RichPrinter.error(f"Model '{model_name}' failed: {e}")
                logger.error(f"Model '{model_name}' failed: {e}", exc_info=True)
                continue
        
        # All models failed
        error_msg = f"All models (including fallbacks) failed. Last error: {last_error}"
        RichPrinter.error(error_msg)
        raise Exception(error_msg)
    
    async def _generate_stream(
        self,
        gen_params: Dict[str, Any],
        stream_callback: Callable
    ) -> tuple[str, Dict]:
        """
        Generate content with streaming.
        
        Args:
            gen_params: Generation parameters
            stream_callback: Async callback(chunk: str) called for each chunk
        
        Returns:
            tuple[str, Dict]: (full_response, usage_data)
        """
        full_response_content = ""
        usage_data = None
        
        stream = await self._client.chat.completions.create(
            **gen_params,
            stream=True
        )
        
        async for chunk in stream:
            chunk_content = chunk.choices[0].delta.content or ""
            full_response_content += chunk_content
            
            # Call stream callback
            await stream_callback(chunk_content)
            
            # Usage data comes in last chunk
            if chunk.usage:
                usage_data = {
                    "id": chunk.id,
                    "model": chunk.model,
                    "usage": chunk.usage.model_dump()
                }
        
        # If no usage data from stream, create minimal one
        if not usage_data:
            usage_data = {
                "id": "stream",
                "model": gen_params["model"],
                "usage": {
                    "prompt_tokens": self.count_tokens(gen_params["messages"][0]["content"]),
                    "completion_tokens": self.count_tokens(full_response_content),
                    "total_tokens": 0
                }
            }
            usage_data["usage"]["total_tokens"] = (
                usage_data["usage"]["prompt_tokens"] +
                usage_data["usage"]["completion_tokens"]
            )
        
        # Calculate cost
        usage_data["cost"] = self._calculate_cost(
            model=usage_data["model"],
            prompt_tokens=usage_data["usage"].get("prompt_tokens", 0),
            completion_tokens=usage_data["usage"].get("completion_tokens", 0)
        )
        usage_data["timestamp"] = datetime.now().isoformat()
        
        # Track billing
        self._track_billing(usage_data)
        
        return full_response_content, usage_data
    
    def _extract_usage_data(self, response) -> Dict[str, Any]:
        """
        Extract comprehensive usage data from response.
        
        OpenRouter provides:
        - Token counts (prompt, completion, total)
        - Model used (may differ from requested due to fallbacks)
        - Generation ID
        - Native provider cost (if available)
        
        Args:
            response: OpenAI ChatCompletion response
        
        Returns:
            Dict with keys: id, model, usage, cost, timestamp
        """
        usage = response.usage.model_dump() if response.usage else {}
        
        # Calculate cost
        cost = self._calculate_cost(
            model=response.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0)
        )
        
        return {
            "id": response.id,
            "model": response.model,
            "usage": usage,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost based on OpenRouter pricing.
        
        Note: Pricing is model-specific and changes frequently.
        This uses hardcoded fallback pricing. For production,
        fetch from OpenRouter /api/v1/models endpoint.
        
        Args:
            model: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        
        Returns:
            Estimated cost in USD
        """
        # Hardcoded pricing (per 1M tokens) - FALLBACK ONLY
        # TODO: Fetch dynamically from OpenRouter API
        # Prices updated: 2025-10-12
        PRICING = {
            # Gemini models (Google)
            "google/gemini-2.5-flash-lite-preview-09-2025": {
                "prompt": 0.10 / 1_000_000,      # $0.10/1M tokens
                "completion": 0.40 / 1_000_000   # $0.40/1M tokens
            },
            "google/gemini-2.0-flash-exp": {
                "prompt": 0.075 / 1_000_000,
                "completion": 0.30 / 1_000_000
            },
            "google/gemini-1.5-flash": {
                "prompt": 0.075 / 1_000_000,
                "completion": 0.30 / 1_000_000
            },
            "google/gemma-3-27b-it": {
                "prompt": 0.09 / 1_000_000,      # $0.09/1M tokens
                "completion": 0.16 / 1_000_000   # $0.16/1M tokens
            },
            
            # DeepSeek models
            "deepseek/deepseek-v3.2-exp": {
                "prompt": 0.27 / 1_000_000,      # $0.27/1M tokens
                "completion": 0.40 / 1_000_000   # $0.40/1M tokens
            },
            
            # Meta Llama models
            "meta-llama/llama-3.3-70b-instruct": {
                "prompt": 0.13 / 1_000_000,      # $0.13/1M tokens
                "completion": 0.39 / 1_000_000   # $0.39/1M tokens
            },
            
            # Qwen models (Alibaba)
            "qwen/qwen-2.5-72b-instruct": {
                "prompt": 0.07 / 1_000_000,      # $0.07/1M tokens (cheapest!)
                "completion": 0.26 / 1_000_000   # $0.26/1M tokens
            },
            
            # Anthropic models
            "anthropic/claude-3-haiku": {
                "prompt": 0.25 / 1_000_000,
                "completion": 1.25 / 1_000_000
            },
            "anthropic/claude-3-sonnet": {
                "prompt": 3.0 / 1_000_000,
                "completion": 15.0 / 1_000_000
            },
            "anthropic/claude-3-opus": {
                "prompt": 15.0 / 1_000_000,
                "completion": 75.0 / 1_000_000
            },
            
            # OpenAI models
            "openai/gpt-4o": {
                "prompt": 5.0 / 1_000_000,
                "completion": 15.0 / 1_000_000
            },
            "openai/gpt-4o-mini": {
                "prompt": 0.15 / 1_000_000,
                "completion": 0.60 / 1_000_000
            },
            "openai/gpt-3.5-turbo": {
                "prompt": 0.50 / 1_000_000,
                "completion": 1.50 / 1_000_000
            }
        }
        
        # Get pricing for model
        if model not in PRICING:
            logger.warning(f"No pricing data for model '{model}', cost will be $0.00")
            return 0.0
        
        pricing = PRICING[model]
        cost = (
            (prompt_tokens * pricing["prompt"]) +
            (completion_tokens * pricing["completion"])
        )
        
        return round(cost, 8)  # 8 decimal places for micro-transactions
    
    def _track_billing(self, usage_data: Dict[str, Any]):
        """
        Track billing for analytics and cost management.
        
        Args:
            usage_data: Usage data dict with 'cost' key
        """
        self._total_cost += usage_data.get("cost", 0.0)
        self._call_history.append(usage_data)
        
        # Log if cost is significant
        if usage_data.get("cost", 0) > 0.01:  # > 1 cent
            logger.info(
                f"High-cost call: ${usage_data['cost']:.4f} "
                f"({usage_data['usage'].get('total_tokens', 0)} tokens)"
            )
    
    def get_billing_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive billing summary.
        
        Returns:
            Dict with:
            - total_cost: Total USD spent
            - total_calls: Number of API calls
            - total_tokens: Total tokens used
            - by_model: Cost breakdown per model
            - recent_calls: Last 10 calls
        """
        return {
            "total_cost": round(self._total_cost, 6),
            "total_calls": len(self._call_history),
            "total_tokens": sum(
                call["usage"].get("total_tokens", 0)
                for call in self._call_history
            ),
            "by_model": self._group_by_model(),
            "recent_calls": self._call_history[-10:] if self._call_history else []
        }
    
    def _group_by_model(self) -> Dict[str, Dict[str, Any]]:
        """
        Group billing data by model.
        
        Returns:
            Dict[model_name, stats] where stats includes:
            - calls: Number of calls
            - tokens: Total tokens
            - cost: Total cost
        """
        by_model = {}
        
        for call in self._call_history:
            model = call.get("model", "unknown")
            
            if model not in by_model:
                by_model[model] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += call["usage"].get("total_tokens", 0)
            by_model[model]["cost"] += call.get("cost", 0.0)
        
        # Round costs
        for model in by_model:
            by_model[model]["cost"] = round(by_model[model]["cost"], 6)
        
        return by_model
    
    def reset_billing(self):
        """Reset billing tracking (useful for testing or new sessions)."""
        self._total_cost = 0.0
        self._call_history = []
        logger.info("Billing tracking reset")