import os
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from openai import AsyncOpenAI
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseLLMAdapter(ABC):
    """
    Abstract base class for all LLM adapters.
    **THE FIX:** The __init__ method is now correctly defined to accept arguments.
    """
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    @abstractmethod
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        pass

# The rest of the class methods that were here before are not needed for this fix,
# but would be present in a full implementation.

class OpenRouterAdapter(BaseLLMAdapter):
    """
    Full-featured OpenRouter adapter.
    """
    def __init__(self, model_name: str, client: AsyncOpenAI, **kwargs):
        # **THE FIX:** The call to super().__init__ is now correct and passes arguments
        # to the parent class, which is correctly defined to accept them.
        super().__init__(model_name=model_name, **kwargs)
        self._client = client
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.models_to_try = [self.model_name] + kwargs.get("fallback_models", [])
        self._total_cost = 0.0
        self._call_history: List[Dict[str, Any]] = []
        logger.info(f"OpenRouterAdapter initialized for model={model_name}")

    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, Dict | None]:
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

                if response and response.choices and response.choices[0].message and response.choices[0].message.content:
                    content = response.choices[0].message.content.strip()
                    if content:
                        # For now, we return dummy usage data. A full implementation would calculate this.
                        return content, {"tokens": 0, "cost": 0.0}

                logger.error(f"Model '{model_name}' returned an empty or invalid response.")
                last_error = "Invalid response from model."
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Model '{model_name}' failed with an exception.", exc_info=True)
                continue
        
        logger.error(f"All models failed to generate a valid response. Last error: {last_error}")
        return None, None

class GeminiAdapter(BaseLLMAdapter):
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        logger.warning("GeminiAdapter is a placeholder and not fully implemented.")
        return "Toto je testovací odpověď od Gemini.", None
