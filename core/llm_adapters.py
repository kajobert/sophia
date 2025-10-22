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
    async def generate_content_async(self, prompt: str, response_format: dict | None = None) -> tuple[str | None, dict | None]:
        """
        Asynchronně generuje obsah.

        Vrací:
            tuple[str | None, dict | None]: Vygenerovaný text (nebo None při chybě) a informace o použití.
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
    Full-featured OpenRouter adapter with robust error handling.
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
        super().__init__(model_name=model_name)
        self._client = client
        self.system_prompt = kwargs.get("system_prompt", "")
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.provider_preferences = provider_preferences or []
        self.models_to_try = [self.model_name] + (fallback_models or [])
        self._total_cost = 0.0
        self._call_history: List[Dict[str, Any]] = []
        logger.info(f"OpenRouterAdapter initialized: model={model_name}, temp={temperature}, max_tokens={max_tokens}")
    
    async def generate_content_async(
        self,
        prompt: str,
        **kwargs
    ) -> tuple[str | None, Dict | None]:
        """
        Generate content with robust validation and fallback.
        Returns None if generation fails or response is invalid.
        """
        messages = [{"role": "user", "content": prompt}]
        
        gen_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        
        last_error = None
        for model_name in self.models_to_try:
            try:
                gen_params["model"] = model_name
                
                response = await self._client.chat.completions.create(**gen_params)

                # **ROBUST VALIDATION LOGIC**
                if response and response.choices:
                    first_choice = response.choices[0]
                    if first_choice.message and first_choice.message.content:
                        content = first_choice.message.content.strip()
                        if content:
                            usage_data = self._extract_usage_data(response)
                            self._track_billing(usage_data)
                            logger.info(f"Successfully generated content from model '{model_name}'.")
                            return content, usage_data

                # If we reach here, the response was invalid.
                logger.error(f"Model '{model_name}' returned an empty or invalid response. Full response: {response.model_dump_json(indent=2)}")
                last_error = f"Model {model_name} returned an invalid/empty response."
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Model '{model_name}' failed with an exception.", exc_info=True)
                continue
        
        logger.error(f"All models failed to generate a valid response. Last error: {last_error}")
        return None, None # Return None if all attempts fail.
    
    def _extract_usage_data(self, response) -> Dict[str, Any]:
        """Extracts comprehensive usage data from the response."""
        usage = response.usage.model_dump() if response.usage else {}
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
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates cost based on hardcoded pricing."""
        PRICING = {
            "google/gemini-2.5-flash-lite": {"prompt": 0.10 / 1_000_000, "completion": 0.40 / 1_000_000},
            "google/gemini-2.0-flash-exp": {"prompt": 0.075 / 1_000_000, "completion": 0.30 / 1_000_000},
            "google/gemma-3-27b-it": {"prompt": 0.09 / 1_000_000, "completion": 0.16 / 1_000_000},
            # ... add other models if needed
        }
        if model not in PRICING:
            logger.warning(f"No pricing data for model '{model}', cost will be $0.00")
            return 0.0
        pricing = PRICING[model]
        return (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])

    def _track_billing(self, usage_data: Dict[str, Any]):
        """Tracks billing for analytics."""
        self._total_cost += usage_data.get("cost", 0.0)
        self._call_history.append(usage_data)
        
# GeminiAdapter remains unchanged
class GeminiAdapter(BaseLLMAdapter):
    # ... (code for GeminiAdapter)
    async def generate_content_async(self, prompt: str, response_format: dict | None = None) -> tuple[str, dict | None]:
        # This would also need robust error handling in a full implementation.
        # For now, we focus on the OpenRouter part.
        return "Gemini response not implemented in this refactor.", None
