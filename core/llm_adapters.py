import asyncio
from abc import ABC, abstractmethod
import google.generativeai as genai

class BaseLLMAdapter(ABC):
    """
    Abstraktní základní třída pro všechny LLM adaptéry.
    Definuje jednotné rozhraní pro generování obsahu.
    """
    @abstractmethod
    async def generate_content_async(self, prompt: str) -> str:
        """
        Asynchronně generuje obsah na základě promptu.
        Tato metoda musí být implementována v každé podtřídě.
        """
        pass

    def count_tokens(self, prompt: str) -> int:
        """
        Volitelná metoda pro počítání tokenů.
        Pokud není implementována, vrací 0.
        """
        return 0

class GoogleGeminiAdapter(BaseLLMAdapter):
    """Adaptér pro modely od Google (Gemini)."""
    def __init__(self, model_name: str, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    async def generate_content_async(self, prompt: str) -> str:
        response = await self._model.generate_content_async(prompt)
        return response.text

    def count_tokens(self, prompt: str) -> int:
        return self._model.count_tokens(prompt).total_tokens


class DeepSeekAdapter(BaseLLMAdapter):
    """
    Mock adaptér pro DeepSeek modely.
    Zajišťuje kompatibilitu rozhraní.
    """
    def __init__(self, model_name: str, api_key: str):
        self._model_name = model_name
        self._api_key = api_key # Uložen pro budoucí použití

    async def generate_content_async(self, prompt: str) -> str:

        # Mock implementace, která vrací informativní text
        await asyncio.sleep(0.1) # Simulace síťové latence
        return f"<TOOL_CODE_START>\n{{\"tool_name\": \"task_complete\", \"args\": [], \"kwargs\": {{\"reason\": \"DeepSeek model '{self._model_name}' is not fully implemented. This is a mock response.\"}}}}\n</TOOL_CODE_END>"


class OllamaAdapter(BaseLLMAdapter):
    """
    Mock adaptér pro lokální Ollama modely.
    Zajišťuje kompatibilitu rozhraní.
    """
    def __init__(self, model_name: str):
        self._model_name = model_name

    async def generate_content_async(self, prompt: str) -> str:
        # Mock implementace
        await asyncio.sleep(0.1)

        return f"<TOOL_CODE_START>\n{{\"tool_name\": \"task_complete\", \"args\": [], \"kwargs\": {{\"reason\": \"Ollama model '{self._model_name}' is not fully implemented. This is a mock response.\"}}}}\n</T>OOL_CODE_END>"
