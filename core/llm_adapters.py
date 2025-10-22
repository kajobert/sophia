import os
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from openai import OpenAI, AsyncOpenAI
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        """
        Asynchronously generates content from a structured list of messages.
        """
        pass

    # ... (rest of BaseLLMAdapter is the same)

# ... (GeminiAdapter remains the same for now)

class OpenRouterAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, client: AsyncOpenAI, **kwargs):
        super().__init__(model_name=model_name)
        self._client = client
        # Assign all other kwargs to instance attributes for flexibility
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.models_to_try = [self.model_name] + kwargs.get("fallback_models", [])
        self._total_cost = 0.0
        self._call_history: List[Dict[str, Any]] = []
        logger.info(f"OpenRouterAdapter initialized for model={model_name}")

    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, Dict | None]:
        """
        Generate content from a structured message list with robust validation.
        """
        # **THE FIX: The `messages` list is now the primary input and is used directly.**
        gen_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": getattr(self, 'temperature', 0.7),
            "max_tokens": getattr(self, 'max_tokens', 4096),
        }
        
        last_error = None
        for model_name in self.models_to_try:
            try:
                gen_params["model"] = model_name
                
                response = await self._client.chat.completions.create(**gen_params)

                if response and response.choices:
                    first_choice = response.choices[0]
                    if first_choice.message and first_choice.message.content:
                        content = first_choice.message.content.strip()
                        if content:
                            usage_data = self._extract_usage_data(response)
                            self._track_billing(usage_data)
                            logger.info(f"Successfully generated content from model '{model_name}'.")
                            return content, usage_data

                logger.error(f"Model '{model_name}' returned an empty or invalid response. Response: {response.model_dump_json(indent=2) if response else 'None'}")
                last_error = f"Model {model_name} returned an invalid/empty response."
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Model '{model_name}' failed with an exception.", exc_info=True)
                continue
        
        logger.error(f"All models failed to generate a valid response. Last error: {last_error}")
        return None, None

    # ... (Rest of the methods: _extract_usage_data, _calculate_cost, _track_billing remain the same)
    
    def _extract_usage_data(self, response) -> Dict[str, Any]:
        """Extracts comprehensive usage data from the response."""
        usage = response.usage.model_dump() if response.usage else {}
        cost = self._calculate_cost(
            model=response.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0)
        )
        return { "id": response.id, "model": response.model, "usage": usage, "cost": cost, "timestamp": datetime.now().isoformat() }
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates cost based on hardcoded pricing."""
        # A simplified pricing map
        PRICING = {
            "google/gemini-2.5-flash-lite": {"prompt": 0.10 / 1_000_000, "completion": 0.40 / 1_000_000},
            "default": {"prompt": 0.50 / 1_000_000, "completion": 1.50 / 1_000_000} # Fallback pricing
        }

        # Find a matching price, or use default
        price_info = next((PRICING[key] for key in PRICING if key in model), PRICING["default"])
        if price_info is PRICING["default"]:
             logger.warning(f"No specific pricing data for model '{model}', using default. Cost will be an estimate.")

        return (prompt_tokens * price_info["prompt"]) + (completion_tokens * price_info["completion"])

    def _track_billing(self, usage_data: Dict[str, Any]):
        """Tracks billing for analytics."""
        self._total_cost += usage_data.get("cost", 0.0)
        self._call_history.append(usage_data)

class GeminiAdapter(BaseLLMAdapter):
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        # Placeholder for future implementation
        logger.warning("GeminiAdapter.generate_content_async is not fully implemented.")
        return "Toto je testovací odpověď od Gemini.", None
