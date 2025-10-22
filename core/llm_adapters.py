import os
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from openai import OpenAI, AsyncOpenAI  # Corrected typo
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseLLMAdapter(ABC):
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    @abstractmethod
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        pass

# ... (The rest of the file is the same as the last correct version) ...

class OpenRouterAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, client: AsyncOpenAI, **kwargs):
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
                        return content, {} # Simplified for now

                last_error = "Invalid response from model."
                continue

            except Exception as e:
                last_error = e
                continue
        
        return None, None

class GeminiAdapter(BaseLLMAdapter):
    async def generate_content_async(self, messages: List[Dict[str, str]], **kwargs) -> tuple[str | None, dict | None]:
        return "Gemini response.", None
